import os
import requests
import json
from datetime import datetime

def upload_to_gist():
    github_token = os.getenv('GITHUB_TOKEN')
    gist_id = os.getenv('GIST_ID')
    
    if not github_token or not gist_id:
        print("❌ Missing GITHUB_TOKEN or GIST_ID")
        return
    
    # Đọc file log mới
    try:
        with open('log.txt', 'r', encoding='utf-8') as f:
            new_log = f.read()
    except FileNotFoundError:
        print("❌ log.txt not found")
        return
    
    # Headers cho API
    headers = {
        'Authorization': f'token {github_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Lấy nội dung Gist hiện tại
        response = requests.get(f'https://api.github.com/gists/{gist_id}', headers=headers)
        response.raise_for_status()
        
        gist_data = response.json()
        current_content = gist_data.get('files', {}).get('genshin-checkin.log', {}).get('content', '')
        
        # Thêm separator và timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        separator = f"\n{'='*50}\n[{timestamp}] New Check-in Session\n{'='*50}\n"
        
        # Ghép nội dung
        updated_content = current_content + separator + new_log
        
        # Cập nhật Gist
        update_data = {
            "files": {
                "genshin-checkin.log": {
                    "content": updated_content
                }
            }
        }
        
        update_response = requests.patch(
            f'https://api.github.com/gists/{gist_id}',
            headers=headers,
            data=json.dumps(update_data)
        )
        update_response.raise_for_status()
        
        print("✅ Successfully uploaded log to Gist")
        print(f"📝 Gist URL: https://gist.github.com/{gist_id}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to upload to Gist: {e}")

if __name__ == '__main__':
    upload_to_gist()