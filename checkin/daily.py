import requests
import time
import datetime
import os
import sys
from dotenv import load_dotenv

# Add utils directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))
try:
    from discord_webhook import send_discord_notification
except ImportError:
    def send_discord_notification(content):
        print(f"Discord webhook not available: {content}")
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
        retcode = result.get('retcode', -1)
        
        print(message)
        print("Daily check-in completed successfully!")

        if retcode != 0 and retcode != -5003:
            return False, log_content, message
        return True, log_content, message
        
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
        cookie = os.getenv('COOKIE')

        act_id = "e202102251931481"  # activity ID for daily check-in

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
        success, log_content, message = checkin(api_url, payload, headers)

        # Write log to file (prepend new log to top) - save to parent directory for logs manager
        log_file = "../genshin-checkin.log"
        try:
            new_log = log_content
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    old_content = f.read()
                with open(log_file, 'w', encoding='utf-8') as f:
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
                    header = f"\n{'='*50}\n[{timestamp}] New Check-in Session\n{'='*50}\n"
                    f.write(header + new_log + "\n" + old_content)
            else:
                with open(log_file, 'w', encoding='utf-8') as f:
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
                    header = f"{'='*50}\n[{timestamp}] New Check-in Session\n{'='*50}\n"
                    f.write(header + new_log)
            print(f"Log written to {log_file}")
        except Exception as e:
            print(f"Failed to write log file: {e}")
        
        # Send Discord notification if webhook URL is available
        discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if discord_webhook_url:
            try:
                if success:
                    content = "✅ **Daily Check-in Completed Successfully!**\n\nYour daily rewards have been claimed."
                else:
                    content = f"❌ **Daily Check-in Failed**\n\nResponse: {message}"
                
                send_discord_notification(content)
            except Exception as e:
                print(f"Failed to send Discord notification: {e}")
        
        exit(0 if success else 1)
            
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)


if __name__ == '__main__':
    main()