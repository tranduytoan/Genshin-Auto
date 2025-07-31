import requests
import os
from bs4 import BeautifulSoup
from typing import List


def scrape_genshin_codes() -> List[str]:
    """Scrape Genshin Impact promotional codes from fandom wiki"""
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
        codes = []
        
        for table in soup.select('#mw-content-text > div > table'):
            for code_elem in table.find_all('code'):
                code_text = code_elem.get_text(strip=True)
                if code_text and len(code_text) >= 8 and code_text.replace(' ', '').isalnum():
                    if code_text not in codes:
                        codes.append(code_text)
        return codes
        
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
    """Get existing redeemed codes from gist"""
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


def upload_redeemed_codes(new_codes: List[str]) -> bool:
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
        all_codes = new_codes + existing_codes
        
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
    


