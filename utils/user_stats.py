import os
import requests
from typing import Dict, Optional


def get_user_stats() -> Optional[Dict]:
    """
    Get user stats from Genshin Impact API
    
    Returns:
        Dict: User role data if successful, None if failed
    """
    # Get environment variables
    server = os.getenv('REGION')
    role_id = os.getenv('UID')
    cookie = os.getenv('COOKIE')
    
    if not all([server, role_id, cookie]):
        print("Missing required environment variables: REGION, UID, or COOKIE")
        return None
    
    # API configuration
    url = "https://bbs-api-os.hoyolab.com/game_record/genshin/api/index"
    
    params = {
        'server': server,
        'role_id': role_id
    }
    
    headers = {
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if response is successful
        if data.get('retcode') == 0 and data.get('message') == 'OK':
            role_data = data.get('data', {}).get('role')
            if role_data:
                return role_data
            else:
                print("No role data found in response")
                return None
        else:
            print(f"API returned error: retcode={data.get('retcode')}, message={data.get('message')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except ValueError as e:
        print(f"JSON decode failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
