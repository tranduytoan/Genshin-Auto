import os
import re
import sys
import time
from typing import List, Dict, Any, Set

import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))
try:
    from discord_webhook import send_discord_notification
    from constants import WIKI_API_URL, REDEEM_API_URL, RATE_LIMIT_CODE, REDEEM_SUCCESS_CODES, DEFAULT_HEADERS
except ImportError:
    def send_discord_notification(content):
        return False

    WIKI_API_URL = "https://genshin-impact.fandom.com/api.php?action=parse&page=Promotional_Code&prop=wikitext&format=json"
    REDEEM_API_URL = "https://public-operation-hk4e.hoyoverse.com/common/apicdkey/api/webExchangeCdkey"
    RATE_LIMIT_CODE = -2016
    REDEEM_SUCCESS_CODES = {0, -2017, -1007, -2001}
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


class CookieExpiredError(Exception):
    pass


def scrape_genshin_codes() -> List[Dict[str, str]]:
    try:
        response = requests.get(WIKI_API_URL, headers=DEFAULT_HEADERS, timeout=30)
        response.raise_for_status()

        wikitext = response.json()['parse']['wikitext']['*']

        active_start = wikitext.find('==Active Codes==')
        inactive_start = wikitext.find('==Inactive Codes==')
        if active_start == -1:
            return []
        end_idx = inactive_start if inactive_start != -1 else len(wikitext)
        active_section = wikitext[active_start:end_idx]

        clean_section = re.sub(r'<!--.*?-->', '', active_section, flags=re.DOTALL)

        codes_data = []
        code_row_pattern = re.compile(r'\{\{Code Row(?!/)(.*?)\}\}', re.DOTALL)

        for match in code_row_pattern.finditer(clean_section):
            block = match.group(1)

            if 'notacode=yes' in block:
                continue

            params = [p.strip() for p in block.split('|') if p.strip()]
            positional = [p for p in params if not re.match(r'^[a-zA-Z_]+=', p)]

            if len(positional) < 3:
                continue

            code_text = positional[0]
            server_raw = positional[1]
            rewards = re.sub(r'\s+', ' ', positional[2]).strip()
            duration = positional[4] if len(positional) > 4 else 'unknown'

            if not _is_valid_code(code_text):
                continue

            servers = _extract_server_names(server_raw)

            if not any(existing['code'] == code_text for existing in codes_data):
                codes_data.append({
                    'code': code_text,
                    'server': servers,
                    'rewards': rewards,
                    'duration': duration
                })

        return codes_data

    except Exception as e:
        print(f"Error scraping codes: {e}")
        raise


_WIKI_SERVER_MAPPING = {
    'G': ['os_usa', 'os_euro', 'os_asia', 'os_cht'],
    'A': ['os_usa', 'os_euro', 'os_asia', 'os_cht', 'os_china'],
    'NA': ['os_usa'],
    'EU': ['os_euro'],
    'SEA': ['os_asia'],
    'SAR': ['os_cht'],
    'CN': ['os_china'],
}


def _extract_server_names(server_raw: str) -> List[str]:
    parts = re.split(r'[;,]', server_raw.strip().upper())
    servers = []
    for part in parts:
        mapped = _WIKI_SERVER_MAPPING.get(part.strip(), [])
        for s in mapped:
            if s not in servers:
                servers.append(s)
    return servers if servers else ['os_usa', 'os_euro', 'os_asia', 'os_cht']


def _is_valid_code(code_text: str) -> bool:
    return bool(code_text and len(code_text) >= 8 and code_text.replace(' ', '').isalnum())


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

            if retcode == -1071:
                raise CookieExpiredError(result.get('message', 'Cookie expired or invalid'))

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
        except CookieExpiredError:
            raise
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
    try:
        redeem_multiple_codes(uid, region, cookie, [{'code': 'GENSHINGIFT', 'server': '', 'rewards': '', 'duration': ''}])
    except CookieExpiredError as e:
        content = (f"⚠️ **Hoyoverse cookie has expired or is invalid**\n"
                   f"Tried to redeem a random code **GENSHINGIFT**\n"
                   f" Got message: {e}\n")
        send_discord_notification(content)
        print("Cookie expired or invalid. Notification sent.")
        sys.exit(1)


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