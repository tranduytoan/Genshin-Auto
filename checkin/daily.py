import os
import sys
import time
import datetime
from typing import Tuple

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))
try:
    from discord_webhook import send_discord_notification
    from constants import CHECKIN_API_URL, DAILY_CHECKIN_ACT_ID, CHECKIN_SUCCESS_CODES, CHECKIN_HEADERS
except ImportError:
    def send_discord_notification(content):
        return False
    
    CHECKIN_API_URL = "https://sg-hk4e-api.hoyolab.com/event/sol/sign"
    DAILY_CHECKIN_ACT_ID = "e202102251931481"
    CHECKIN_SUCCESS_CODES = {0, -5003}
    CHECKIN_HEADERS = {
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://act.hoyolab.com",
        "Referer": "https://act.hoyolab.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }


def checkin(url: str, payload: dict, headers: dict) -> Tuple[bool, str, str]:
    time_now = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
    log_content = f"Request at: {time_now}\n"
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        message = result.get('message', 'Unknown response')
        log_content += f"\tResponse: {response.text}"
        retcode = result.get('retcode', -1)
        
        success = retcode in CHECKIN_SUCCESS_CODES
        return success, log_content, message
        
    except Exception as e:
        error_msg = str(e)
        log_content += f"\tError: {error_msg}"
        return False, log_content, error_msg


def write_log(log_content: str) -> None:
    log_file = "../genshin-checkin.log"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    header = f"\n{'='*50}\n[{timestamp}] New Check-in Session\n{'='*50}\n"
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                old_content = f.read()
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(header + log_content + "\n" + old_content)
        else:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(header + log_content)
    except Exception as e:
        print(f"Failed to write log file: {e}")


def send_notification(success: bool, message: str) -> None:
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        return
    
    try:
        if success:
            content = "✅ **Daily Check-in Completed Successfully!**\n\nYour daily rewards have been claimed."
        else:
            content = f"❌ **Daily Check-in Failed**\n\nResponse: {message}"
        
        send_discord_notification(content)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")


def validate_environment() -> Tuple[str]:
    load_dotenv()
    cookie = os.getenv('COOKIE')
    
    if not cookie:
        raise ValueError("Missing required environment variable: COOKIE")
    
    return cookie


def main():
    try:
        cookie = validate_environment()
        
        payload = {"act_id": DAILY_CHECKIN_ACT_ID}
        headers = {**CHECKIN_HEADERS, "Cookie": cookie}
        
        success, log_content, message = checkin(CHECKIN_API_URL, payload, headers)
        
        write_log(log_content)
        send_notification(success, message)
        
        exit(0 if success else 1)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)


if __name__ == '__main__':
    main()