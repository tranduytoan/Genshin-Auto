import requests
import os
import logging
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GistManager:
    """Class to manage uploading redeemed codes to GitHub Gist"""
    
    def __init__(self, gist_id: str, token: str):
        self.gist_id = gist_id
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        self.api_url = f"https://api.github.com/gists/{gist_id}"
    
    def get_existing_codes(self) -> List[str]:
        """Get existing redeemed codes from gist file"""
        try:
            logger.info("Fetching existing redeemed codes from gist...")
            response = requests.get(self.api_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            gist_data = response.json()
            file_content = gist_data.get('files', {}).get('redeemed_codes.txt', {}).get('content', '')
            
            if file_content:
                codes = [line.strip() for line in file_content.split('\n') if line.strip()]
                logger.info(f"Found {len(codes)} existing redeemed codes")
                return codes
            else:
                logger.info("No existing redeemed codes found")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Error fetching existing codes: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def update_redeemed_codes(self, new_codes: List[str]) -> bool:
        """Add new redeemed codes to the beginning of gist file"""
        if not new_codes:
            logger.info("No new codes to upload")
            return True
        
        try:
            logger.info(f"Uploading {len(new_codes)} new redeemed codes to gist...")
            
            # Get existing content
            existing_codes = self.get_existing_codes()
            
            # Combine new codes (at the beginning) with existing codes
            all_codes = new_codes + existing_codes
            
            # Remove duplicates while preserving order
            unique_codes = []
            seen = set()
            for code in all_codes:
                if code not in seen:
                    unique_codes.append(code)
                    seen.add(code)
            
            # Create updated content
            updated_content = '\n'.join(unique_codes)
            
            # Update gist
            data = {
                "files": {
                    "redeemed_codes.txt": {
                        "content": updated_content
                    }
                }
            }
            
            response = requests.patch(self.api_url, json=data, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            logger.info("Successfully updated redeemed codes in gist")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error updating gist: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False


def upload_redeemed_codes(new_codes: List[str]) -> bool:
    """Function to upload new redeemed codes to gist"""
    try:
        gist_id = os.getenv('GIST_ID')
        token = os.getenv('METRICS_TOKEN')
        
        if not gist_id or not token:
            logger.error("GIST_ID or METRICS_TOKEN environment variables not set")
            return False
        
        gist_manager = GistManager(gist_id, token)
        return gist_manager.update_redeemed_codes(new_codes)
        
    except Exception as e:
        logger.error(f"Error uploading redeemed codes: {e}")
        return False


def get_existing_redeemed_codes() -> List[str]:
    """Function to get existing redeemed codes from gist"""
    try:
        gist_id = os.getenv('GIST_ID')
        token = os.getenv('METRICS_TOKEN')
        
        if not gist_id or not token:
            logger.error("GIST_ID or METRICS_TOKEN environment variables not set")
            return []
        
        gist_manager = GistManager(gist_id, token)
        return gist_manager.get_existing_codes()
        
    except Exception as e:
        logger.error(f"Error getting existing redeemed codes: {e}")
        return []