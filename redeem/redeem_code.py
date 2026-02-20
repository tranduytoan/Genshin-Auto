import os
import re
import sys
import time
from typing import List, Dict, Any, Set

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))
try:
    from discord_webhook import send_discord_notification
    from constants import WIKI_URL, REDEEM_API_URL, RATE_LIMIT_CODE, REDEEM_SUCCESS_CODES, DEFAULT_HEADERS
except ImportError:
    def send_discord_notification(content):
        return False
    
    WIKI_URL = "https://genshin-impact.fandom.com/wiki/Promotional_Code"
    REDEEM_API_URL = "https://public-operation-hk4e.hoyoverse.com/common/apicdkey/api/webExchangeCdkey"
    RATE_LIMIT_CODE = -2016
    REDEEM_SUCCESS_CODES = {0, -2017, -1007, -2001}
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }


def scrape_genshin_codes() -> List[Dict[str, str]]:
    try:
        response = requests.get(WIKI_URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        codes_data = []
        
        for table in soup.select('#mw-content-text > div > table'):
            tbody = table.find('tbody')
            if not tbody:
                continue
                
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 4:
                    code_elems = cells[0].find_all('code')
                    if not code_elems:
                        continue

                    server = _extract_server_names(cells[1])
                    rewards = _extract_rewards(cells[2])
                    duration = cells[3].get_text(strip=True)
                    
                    for code_elem in code_elems:
                        code_text = code_elem.get_text(strip=True)
                        if not _is_valid_code(code_text):
                            continue
                        
                        code_data = {
                            'code': code_text,
                            'server': server,
                            'rewards': rewards,
                            'duration': duration
                        }
                        
                        if not any(existing['code'] == code_text for existing in codes_data):
                            codes_data.append(code_data)
        
        return codes_data
        
    except Exception as e:
        print(f"Error scraping codes: {e}")
        raise


def _extract_server_names(cells: str) -> List[str]:
    raw_server = cells.get_text(strip=True)
    parts = re.split(r'[,&;]|\band\b', raw_server)
    
    server_mapping = {
        'America': 'os_usa',
        'Europe': 'os_euro',
        'Asia': 'os_asia',
        'TW/HK/Macao': 'os_cht',
        'China': 'os_china'
    }
    
    servers = []
    for p in parts:
        p_stripped = p.strip()
        if p_stripped:
            mapped_server = server_mapping.get(p_stripped, 'all')
            servers.append(mapped_server)
    
    return servers


def _is_valid_code(code_text: str) -> bool:
    return bool(code_text and len(code_text) >= 8 and code_text.replace(' ', '').isalnum())


def _extract_rewards(rewards_elem) -> str:
    rewards = []
    for item in rewards_elem.find_all(class_='item-text'):
        reward_text = item.get_text(strip=True)
        if reward_text:
            rewards.append(reward_text)
    return ', '.join(rewards) if rewards else rewards_elem.get_text(strip=True)


def get_existing_redeemed_codes() -> List[str]:
    try:
        codes_file = 'redeemed_codes.txt'
        if not os.path.exists(codes_file):
            codes_file = '../redeemed_codes.txt'
            
        if os.path.exists(codes_file):
            with open(codes_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return [line.strip() for line in content.split('\n') if line.strip()]
        return []
    except Exception as e:
        print(f"Failed to read redeemed codes: {e}")
        return []


def save_redeemed_codes(new_codes: List[Dict[str, str]]) -> bool:
    if not new_codes:
        return True
    
    try:
        existing_codes = get_existing_redeemed_codes()
        new_code_strings = [code_data['code'] for code_data in new_codes]
        all_codes = new_code_strings + existing_codes
        
        unique_codes = []
        seen = set()
        for code in all_codes:
            if code not in seen:
                unique_codes.append(code)
                seen.add(code)
        
        codes_file = '../redeemed_codes.txt'
        with open(codes_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(unique_codes))
        
        return True
        
    except Exception as e:
        print(f"Failed to write redeemed codes: {e}")
        return False


def redeem_code(session: requests.Session, uid: str, region: str, code: str) -> Dict[str, Any]:
    for attempt in range(4):
        try:
            response = session.get(
                REDEEM_API_URL,
                params={
                    'lang': 'en', 'game_biz': 'hk4e_global', 'sLangKey': 'en-us',
                    'uid': uid, 'region': region, 'cdkey': code
                },
                timeout=30
            )
            
            result = response.json() if response.ok else {'retcode': -1, 'message': 'Network error'}
            retcode = result.get('retcode', -1)
            
            if retcode == RATE_LIMIT_CODE and attempt < 3:
                wait_time = _get_wait_time(result.get('message', ''))
                time.sleep(wait_time)
                continue
            
            return result
            
        except Exception as e:
            if attempt == 3:
                return {'retcode': -1, 'message': f'Error: {e}'}
            time.sleep(2)
    
    return {'retcode': -1, 'message': 'Max retries exceeded'}


def _get_wait_time(message: str) -> int:
    match = re.search(r'try again in (\d+) second', message)
    return int(match.group(1)) + 1 if match else 5


def redeem_multiple_codes(uid: str, region: str, cookie: str, codes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    session = requests.Session()
    session.headers.update({**DEFAULT_HEADERS, 'Cookie': cookie})

    new_codes_redeemed = []
    for code_data in codes:
        try:
            code = code_data['code']
            result = redeem_code(session, uid, region, code)
            retcode = result.get('retcode', -1)
            
            status_entry = code_data.copy()
            status_entry.update({
                'retcode': retcode,
                'message': result.get('message', 'unknown'),
                'success': retcode == 0,
                'cacheable': retcode in REDEEM_SUCCESS_CODES
            })
            new_codes_redeemed.append(status_entry)
            
            _print_redemption_result(code, result, code_data)
            time.sleep(1)
            
        except Exception as e:
            error_entry = code_data.copy()
            error_entry.update({
                'retcode': -1,
                'message': str(e),
                'success': False,
                'cacheable': False
            })
            new_codes_redeemed.append(error_entry)
            print(f"Error with code {code_data.get('code', 'unknown')}: {e}")

    return new_codes_redeemed


def _print_redemption_result(code: str, result: Dict[str, Any], code_data: Dict[str, str]) -> None:
    retcode = result.get('retcode', -1)
    message = result.get('message', 'processed')
    rewards = code_data['rewards'][:50] + ('...' if len(code_data['rewards']) > 50 else '')
    
    if retcode in REDEEM_SUCCESS_CODES:
        print(f"Code {code}: {message} | Rewards: {rewards}")
    else:
        print(f"Code {code} failed: {message}")

def validate_environment() -> tuple[str, str, str]:
    required_vars = ['UID', 'REGION', 'COOKIE']
    env_values = {var: os.getenv(var) for var in required_vars}
    missing = [k for k, v in env_values.items() if not v]
    
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        exit(1)
    
    return env_values['UID'], env_values['REGION'], env_values['COOKIE']


def filter_new_codes(all_codes: List[Dict[str, str]], region: str = None) -> List[Dict[str, str]]:
    redeemed_codes = get_existing_redeemed_codes()
    redeemed_codes_set = set(redeemed_codes)
    new_codes = [code_data for code_data in all_codes if code_data['code'] not in redeemed_codes_set]
    already_redeemed_count = len(all_codes) - len(new_codes)
    
    if region:
        filtered_codes = []
        for code_data in new_codes:
            servers = code_data.get('server', [])
            if isinstance(servers, str):
                servers = [servers]
            if 'all' in servers or region in servers:
                filtered_codes.append(code_data)
        
        print(f"Found {len(all_codes)} total codes, {already_redeemed_count} already redeemed, {len(new_codes)} new, {len(filtered_codes)} new match region '{region}'")
        return filtered_codes
    
    print(f"Found {len(all_codes)} total codes, {already_redeemed_count} already redeemed, {len(new_codes)} new")
    return new_codes


def send_discord_report(new_codes_redeemed: List[Dict[str, str]], cacheable_codes: List[Dict[str, str]]) -> None:
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        return
    
    try:
        success_count = len([code for code in new_codes_redeemed if code.get('success', False)])
        total_count = len(new_codes_redeemed)
        
        codes_detail = []
        for code_data in new_codes_redeemed:
            code = code_data.get('code', 'Unknown')
            rewards = code_data.get('rewards', 'Unknown rewards')
            
            if code_data.get('success', False):
                status = "✅ Success"
            else:
                retcode = code_data.get('retcode', -1)
                message = code_data.get('message', 'Unknown error')
                status = f"❌ {message} (retcode: {retcode})"
            
            codes_detail.append(f"**{code}**\n• Rewards: {rewards}\n• Status: {status}")
        
        codes_text = "\n\n".join(codes_detail)
        
        cached_summary = ""
        if cacheable_codes:
            cached_codes_list = [code_data.get('code', 'Unknown') for code_data in cacheable_codes]
            cached_summary = f"\n\n**📂 Codes added to cache (Repository - branch logs):**\n{', '.join(cached_codes_list)}"
        
        content = (f"🎁 **Code Redemption Report**\n\n"
                  f"**Summary:** {success_count}/{total_count} codes successful\n\n"
                  f"**Code details:**\n{codes_text}{cached_summary}")
        
        send_discord_notification(content)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")


def try_renew_cookie(uid, region, cookie) -> None:
    print("Attempting to renew cookie...")

    # Redeem a random code using the cookie to renew it
    temp_check = redeem_multiple_codes(uid, region, cookie, [{'code': 'GENSHINGIFT', 'server': '', 'rewards': '', 'duration': ''}])
    
    # If retcode -1071 (cookie expired), notify via Discord
    if temp_check and temp_check[0].get('retcode') == -1071:
        content = (f"⚠️ **Hoyoverse cookie has expired or is invalid**\n"
                   f"Tried to redeem a random code **{temp_check[0].get('code')}**\n"
                   f" Got message: {temp_check[0].get('message')}"
                   f" (retcode: {temp_check[0].get('retcode')}).\n")
        send_discord_notification(content)
        print("Cookie expired or invalid. Notification sent.")
    return


def main():
    try:
        uid, region, cookie = validate_environment()

        all_codes_data = scrape_genshin_codes()
        if not all_codes_data:
            print("No codes found")
            try_renew_cookie(uid, region, cookie)
            return

        new_codes_data = filter_new_codes(all_codes_data, region)
        if not new_codes_data:
            print("No new codes to redeem")
            try_renew_cookie(uid, region, cookie)
            return

        new_codes_redeemed = redeem_multiple_codes(uid, region, cookie, new_codes_data)
        cacheable_codes = [code for code in new_codes_redeemed if code.get('cacheable', False)]

        if cacheable_codes:
            print(f"\nWriting {len(cacheable_codes)} redeemed codes to file...")
            if save_redeemed_codes(cacheable_codes):
                print("Codes file updated successfully")
            else:
                print("Failed to update codes file")
        else:
            print("No codes were successfully redeemed")
        
        send_discord_report(new_codes_redeemed, cacheable_codes)

    except Exception as e:
        print(f"Fatal error: {e}")
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if webhook_url:
            try:
                send_discord_notification(f"⚠️⚠️⚠️ ERROR WHEN REDEEMING CODES: {e}")
            except Exception as e:
                print(f"Failed to send Discord notification: {e}")
        raise

if __name__ == '__main__':
    main()