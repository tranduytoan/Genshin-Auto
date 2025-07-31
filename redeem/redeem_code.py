import os
import re
import time
import requests
from typing import List, Dict, Any
from utils import scrape_genshin_codes, upload_redeemed_codes, get_existing_redeemed_codes


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


def redeem_multiple_codes(uid: str, region: str, cookie: str, codes: List[str]) -> List[str]:
    """Redeem multiple codes and return successfully redeemed ones"""
    session = requests.Session()
    session.headers.update({
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    redeemed = []
    for code in codes:
        try:
            result = redeem_code(session, uid, region, code)
            retcode = result.get('retcode', -1)
            
            # Save codes that can never be reused
            # 0 (success), -2017 (already claimed), -1007 (expired), -2001 (invalid)
            if retcode in [0, -2017, -1007, -2001]:
                redeemed.append(code)
                print(f"Code {code}: {result.get('message', 'processed')}")
            else:
                print(f"Code {code} failed: {result.get('message', 'unknown error')}")
            
            time.sleep(1)
        except Exception as e:
            print(f"Error with code {code}: {e}")
    
    return redeemed

def main():
    try:
        # Check environment variables
        required_vars = ['UID', 'REGION', 'COOKIE', 'GIST_ID', 'GITHUB_TOKEN']
        env_values = {var: os.getenv(var) for var in required_vars}
        missing = [k for k, v in env_values.items() if not v]
        
        if missing:
            print(f"Missing environment variables: {', '.join(missing)}")
        if not all([env_values['COOKIE'], env_values['UID'], env_values['REGION']]):
            print("Required environment variables are not set")
            exit(1)

        # Get codes
        all_codes = scrape_genshin_codes()
        if not all_codes:
            print("No codes found")
            return

        # Filter new codes
        redeemed_codes = get_existing_redeemed_codes()
        new_codes = list(set(all_codes) - set(redeemed_codes))
        
        print(f"Found {len(all_codes)} total codes, {len(redeemed_codes)} already redeemed, {len(new_codes)} new")
        
        if not new_codes:
            print("No new codes to redeem")
            return

        # Redeem codes
        newly_redeemed = redeem_multiple_codes(
            env_values['UID'], 
            env_values['REGION'], 
            env_values['COOKIE'], 
            new_codes
        )

        # Upload to gist
        if newly_redeemed and all([env_values['GIST_ID'], env_values['GITHUB_TOKEN']]):
            print(f"Uploading {len(newly_redeemed)} redeemed codes to Gist...")
            if upload_redeemed_codes(newly_redeemed):
                print("Gist updated successfully")
            else:
                print("Failed to update Gist")
        else:
            print("No codes were successfully redeemed")

    except Exception as e:
        print(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
