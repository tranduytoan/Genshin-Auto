import requests
import time
import datetime
import os
from dotenv import load_dotenv


def upload_to_gist(log_content: str, gist_id: str, token: str) -> bool:
    """Upload check-in log to gist"""
    try:
        headers = {
            'Authorization': f'token {token}',
            'Content-Type': 'application/json'
        }
        
        # Get existing content
        response = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=30)
        current_content = response.json().get('files', {}).get('genshin-checkin.log', {}).get('content', '') if response.ok else ''
        
        # Add timestamp and new content
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        separator = f"\n{'='*50}\n[{timestamp}] New Check-in Session\n{'='*50}\n"
        updated_content = current_content + separator + log_content
        
        # Update gist
        data = {"files": {"genshin-checkin.log": {"content": updated_content}}}
        response = requests.patch(f"https://api.github.com/gists/{gist_id}", json=data, headers=headers, timeout=30)
        
        return response.ok
    except:
        return False


def checkin(url: str, payload: dict, headers: dict) -> tuple[bool, str]:
    """Send check-in request"""
    time_now = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
    log_content = f"Request at: {time_now}\n"
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        message = result.get('message', 'Unknown response')
        log_content += f"\tResponse: {response.text}"
        
        print(message)
        print("Daily check-in completed successfully!")
        return True, log_content
        
    except Exception as e:
        error_msg = str(e)
        log_content += f"\tError: {error_msg}"
        print(f"Daily check-in failed: {error_msg}")
        return False, log_content


def main():
    try:
        api_url = "https://sg-hk4e-api.hoyolab.com/event/sol/sign"
        
        load_dotenv()
        
        # Get environment variables
        act_id = os.getenv('ACT_ID')
        cookie = os.getenv('COOKIE')
        gist_id = os.getenv('GIST_ID')
        github_token = os.getenv('GITHUB_TOKEN')

        # Check required variables
        if not all([act_id, cookie]):
            print("Missing required environment variables: ACT_ID, COOKIE")
            exit(1)

        # Prepare API request
        payload = {"act_id": act_id}
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": cookie,
            "Origin": "https://act.hoyolab.com",
            "Referer": "https://act.hoyolab.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        
        # Perform check-in
        success, log_content = checkin(api_url, payload, headers)
        
        # Upload to Gist if available
        if gist_id and github_token:
            upload_to_gist(log_content, gist_id, github_token)
        else:
            print("Gist ID or GitHub token not found. Skipping upload.")
        
        exit(0 if success else 1)
            
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)


if __name__ == '__main__':
    main()