import os
import re
import time
import requests
import sys
from typing import List, Dict, Any
from bs4 import BeautifulSoup

# Add utils directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))
try:
    from discord_webhook import send_discord_notification
except ImportError:
    def send_discord_notification(content):
        print(f"Discord webhook not available: {content}")
        return False


def scrape_genshin_codes() -> List[Dict[str, str]]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(
            "https://genshin-impact.fandom.com/wiki/Promotional_Code", 
            headers=headers, 
            timeout=30
        )
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
                    code_elem = cells[0].find('code')
                    if not code_elem:
                        continue
                    code_text = code_elem.get_text(strip=True)
                    
                    if not (code_text and len(code_text) >= 8 and code_text.replace(' ', '').isalnum()):
                        continue
                    server = cells[1].get_text(strip=True)
                    rewards_elem = cells[2]
                    rewards = []
                    for item in rewards_elem.find_all(class_='item-text'):
                        reward_text = item.get_text(strip=True)
                        if reward_text:
                            rewards.append(reward_text)
                    rewards_str = ', '.join(rewards) if rewards else cells[2].get_text(strip=True)
                    duration = cells[3].get_text(strip=True)
                    code_data = {
                        'code': code_text,
                        'server': server,
                        'rewards': rewards_str,
                        'duration': duration
                    }
                    if not any(existing['code'] == code_text for existing in codes_data):
                        codes_data.append(code_data)
        
        return codes_data
        
    except Exception as e:
        print(f"Error scraping codes: {e}")
        return []
    

def get_env_vars() -> tuple[bool, str, str]:
    gist_id = os.getenv('GIST_ID')
    token = os.getenv('GITHUB_TOKEN')
    
    if not gist_id or not token:
        return False, "", ""

    return True, gist_id, token


def get_existing_redeemed_codes() -> List[str]:
    try:
        success, gist_id, token = get_env_vars()
        if not success:
            return []
        
        headers = {'Authorization': f'token {token}'}
        response = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=30)
        
        if response.ok:
            content = response.json().get('files', {}).get('redeemed_codes.txt', {}).get('content', '')
            return [line.strip() for line in content.split('\n') if line.strip()]
        
        return []
    except:
        return []


def upload_redeemed_codes(new_codes: List[Dict[str, str]]) -> bool:
    """Upload new redeemed codes to gist"""
    if not new_codes:
        return True
    
    try:
        success, gist_id, token = get_env_vars()
        if not success:
            return False
        
        headers = {
            'Authorization': f'token {token}',
            'Content-Type': 'application/json'
        }
        
        # Get existing codes and combine
        existing_codes = get_existing_redeemed_codes()
        new_code_strings = [code_data['code'] for code_data in new_codes]
        all_codes = new_code_strings + existing_codes
        
        # Remove duplicates while preserving order
        unique_codes = []
        seen = set()
        for code in all_codes:
            if code not in seen:
                unique_codes.append(code)
                seen.add(code)
        
        # Update gist
        data = {"files": {"redeemed_codes.txt": {"content": '\n'.join(unique_codes)}}}
        response = requests.patch(f"https://api.github.com/gists/{gist_id}", json=data, headers=headers, timeout=30)
        
        return response.ok
    except:
        return False


def redeem_code(session: requests.Session, uid: str, region: str, code: str) -> Dict[str, Any]:
    """Redeem a single code with retry logic"""
    for attempt in range(4):
        try:
            response = session.get(
                "https://public-operation-hk4e.hoyoverse.com/common/apicdkey/api/webExchangeCdkey",
                params={
                    'lang': 'en', 'game_biz': 'hk4e_global', 'sLangKey': 'en-us',
                    'uid': uid, 'region': region, 'cdkey': code
                },
                timeout=30
            )
            
            result = response.json() if response.ok else {'retcode': -1, 'message': 'Network error'}
            retcode = result.get('retcode', -1)
            
            # Rate limit handling
            if retcode == -2016 and attempt < 3:
                wait_time = 5
                if 'message' in result:
                    match = re.search(r'try again in (\d+) second', result['message'])
                    if match:
                        wait_time = int(match.group(1)) + 1
                time.sleep(wait_time)
                continue
            
            return result
            
        except Exception as e:
            if attempt == 3:
                return {'retcode': -1, 'message': f'Error: {e}'}
            time.sleep(2)
    
    return {'retcode': -1, 'message': 'Max retries exceeded'}


def redeem_multiple_codes(uid: str, region: str, cookie: str, codes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Redeem multiple codes and return status of all codes"""
    session = requests.Session()
    session.headers.update({
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    new_codes_redeemed: List[Dict[str, str]] = []
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
                'cacheable': retcode in [0, -2017, -1007, -2001]
            })
            new_codes_redeemed.append(status_entry)
            
            if retcode in [0, -2017, -1007, -2001]:
                print(f"Code {code}: {result.get('message', 'processed')} | Rewards: {code_data['rewards'][:50]}...")
            else:
                print(f"Code {code} failed: {result.get('message', 'unknown error')}")
            
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

def main():
    try:
        required_vars = ['UID', 'REGION', 'COOKIE', 'GIST_ID', 'GITHUB_TOKEN']
        env_values = {var: os.getenv(var) for var in required_vars}
        missing = [k for k, v in env_values.items() if not v]
        
        if missing:
            print(f"Missing environment variables: {', '.join(missing)}")
        if not all([env_values['COOKIE'], env_values['UID'], env_values['REGION']]):
            exit(1)

        all_codes_data = scrape_genshin_codes()
        if not all_codes_data:
            print("No codes found")
            return

        # Filter new codes
        if all([env_values['GIST_ID'], env_values['GITHUB_TOKEN']]):
            redeemed_codes = get_existing_redeemed_codes()
            redeemed_codes_set = set(redeemed_codes)
            new_codes_data = [code_data for code_data in all_codes_data if code_data['code'] not in redeemed_codes_set]
        else:
            redeemed_codes = []
            new_codes_data = all_codes_data

        print(f"Found {len(all_codes_data)} total codes, {len(redeemed_codes)} already redeemed, {len(new_codes_data)} new")
        
        if not new_codes_data:
            print("No new codes to redeem")
            return

        new_codes_redeemed = redeem_multiple_codes(
            env_values['UID'], 
            env_values['REGION'], 
            env_values['COOKIE'], 
            new_codes_data
        )

        cacheable_codes = [code for code in new_codes_redeemed if code.get('cacheable', False)]

        # Cache to gist
        if cacheable_codes and all([env_values['GIST_ID'], env_values['GITHUB_TOKEN']]):
            print(f"\nUploading {len(cacheable_codes)} redeemed codes to Gist...")
            if upload_redeemed_codes(cacheable_codes):
                print("Gist updated successfully")
            else:
                print("Failed to update Gist")
        
        # Send Discord notification if webhook URL is available
        discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if discord_webhook_url:
            try:
                success_count = len([code for code in new_codes_redeemed if code.get('success', False)])
                total_count = len(new_codes_data)
                
                # Create detailed code status summary
                codes_detail = []
                for code_data in new_codes_redeemed:
                    code = code_data.get('code', 'Unknown')
                    rewards = code_data.get('rewards', 'Unknown rewards')[:50]
                    
                    if code_data.get('success', False):
                        status = "✅ Success"
                    else:
                        retcode = code_data.get('retcode', -1)
                        message = code_data.get('message', 'Unknown error')
                        status = f"❌ {message} (retcode: {retcode})"
                    
                    codes_detail.append(f"**{code}**\n• Rewards: {rewards}\n• Status: {status}")
                
                codes_text = "\n\n".join(codes_detail)
                
                # Create cached codes summary
                cached_summary = ""
                if cacheable_codes:
                    cached_codes_list = [code_data.get('code', 'Unknown') for code_data in cacheable_codes]
                    cached_summary = f"\n\n**📂 Codes added to cache (Gist):**\n{', '.join(cached_codes_list)}"
                
                content = f"🎁 **Code Redemption Report**\n\n" \
                            f"**Summary:** {success_count}/{total_count} codes successful\n\n" \
                            f"**Code details:**\n{codes_text}{cached_summary}"
                send_discord_notification(content)
            except Exception as e:
                print(f"Failed to send Discord notification: {e}")
        
        if not cacheable_codes:
            print("No codes were successfully redeemed")

    except Exception as e:
        print(f"Fatal error: {e}")
        discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if discord_webhook_url:
            try:
                send_discord_notification(f"⚠️⚠️⚠️ ERROR WHEN REDEEMING CODES: {e}")
            except Exception as e:
                print(f"Failed to send Discord notification: {e}")
        raise

if __name__ == '__main__':
    main()
