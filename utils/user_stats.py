import os
from typing import Dict, Optional

import requests

try:
    from constants import USER_STATS_API_URL, DEFAULT_HEADERS
except ImportError:
    USER_STATS_API_URL = "https://bbs-api-os.hoyolab.com/game_record/genshin/api/index"
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }


def get_user_stats() -> Optional[Dict]:
    server = os.getenv('REGION')
    role_id = os.getenv('UID')
    cookie = os.getenv('COOKIE')
    
    if not all([server, role_id, cookie]):
        return None
    
    params = {
        'server': server,
        'role_id': role_id
    }
    
    headers = {**DEFAULT_HEADERS, 'Cookie': cookie}
    
    try:
        response = requests.get(USER_STATS_API_URL, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('retcode') == 0 and data.get('message') == 'OK':
            role_data = data.get('data', {}).get('role')
            return role_data if role_data else None
        
        return None
            
    except Exception:
        return None
