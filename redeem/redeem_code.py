import os
import re
import requests
import time
import logging
from typing import List, Dict, Any
from scrawl_code import scrape_genshin_codes
from upload_to_gist import upload_redeemed_codes, get_existing_redeemed_codes

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GenshinRedeemAPI:
    """Class to handle Genshin Impact code redemption"""
    
    def __init__(self, uid: str, region: str, cookie: str):
        self.uid = uid
        self.region = region
        self.cookie = cookie
        self.base_url = "https://public-operation-hk4e.hoyoverse.com/common/apicdkey/api/webExchangeCdkey"
        self.headers = {
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def redeem_code(self, code: str, max_retries: int = 3) -> Dict[str, Any]:
        """Redeem a single code and return the response"""
        for attempt in range(max_retries + 1):
            try:
                params = {
                    'lang': 'en',
                    'game_biz': 'hk4e_global',
                    'sLangKey': 'en-us',
                    'uid': self.uid,
                    'region': self.region,
                    'cdkey': code
                }
                
                if attempt == 0:
                    logger.info(f"Attempting to redeem code: {code}")
                else:
                    logger.info(f"Retry attempt {attempt} for code: {code}")
                    
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                retcode = result.get('retcode', -1)
                message = result.get('message', 'Unknown error')
                
                logger.info(f"Code {code} - Response: {retcode} - {message}")
                
                # If cooldown error (-2016), retry after waiting
                if retcode == -2016 and attempt < max_retries:
                    # Extract wait time from message if available, default to 5 seconds
                    wait_time = self._extract_cooldown_time(message)
                    logger.info(f"Code {code} in cooldown, waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                
                return result
                
            except requests.RequestException as e:
                logger.error(f"Network error redeeming code {code} (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    return {'retcode': -1, 'message': f'Network error: {e}'}
                time.sleep(2)  # Wait 2 seconds before retry on network error
            except Exception as e:
                logger.error(f"Unexpected error redeeming code {code} (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    return {'retcode': -1, 'message': f'Unexpected error: {e}'}
        
        return {'retcode': -1, 'message': 'Max retries exceeded'}
    
    def _extract_cooldown_time(self, message: str) -> int:
        """Extract cooldown time from error message, default to 5 seconds"""
        match = re.search(r'try again in (\d+) second', message)
        if match:
            return int(match.group(1)) + 1  # Add 1 second buffer
        return 5  # Default fallback
    
    def redeem_multiple_codes(self, codes: List[str]) -> List[str]:
        """Redeem multiple codes and return list of codes that should be marked as redeemed"""
        redeemed_codes = []
        
        for code in codes:
            try:
                result = self.redeem_code(code)
                retcode = result.get('retcode', -1)
                
                # Mark code as redeemed if: successful (0), already used (-2017), or unable to use (-1007)
                if retcode in [0, -2017, -1007]:
                    redeemed_codes.append(code)
                    logger.info(f"Code {code} marked as redeemed (retcode: {retcode})")
                elif retcode == -2016:
                    logger.warning(f"Code {code} still in cooldown after retries, will try again next run")
                else:
                    logger.warning(f"Code {code} not marked as redeemed (retcode: {retcode})")
                
                # Wait 1 second between requests to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing code {code}: {e}")
                continue
        
        return redeemed_codes


def load_environment_variables() -> Dict[str, str]:
    """Load required environment variables"""
    required_vars = ['REDEEM_UID', 'REDEEM_REGION', 'COOKIE', 'GIST_ID', 'METRICS_TOKEN']
    env_vars = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            logger.error(f"Required environment variable {var} not set")
            raise ValueError(f"Missing required environment variable: {var}")
        env_vars[var] = value
    
    logger.info("All required environment variables loaded successfully")
    return env_vars


def filter_new_codes(all_codes: List[str], existing_redeemed_codes: List[str]) -> List[str]:
    """Filter out codes that have already been redeemed"""
    new_codes = [code for code in all_codes if code not in existing_redeemed_codes]
    
    logger.info(f"Total codes found: {len(all_codes)}")
    logger.info(f"Already redeemed codes: {len(existing_redeemed_codes)}")
    logger.info(f"New codes to redeem: {len(new_codes)}")
    
    return new_codes


def main():
    """Main function to orchestrate the redemption process"""
    try:
        logger.info("Starting Genshin Impact code redemption process...")
        
        # Load environment variables
        env_vars = load_environment_variables()
        
        # Scrape codes from web
        logger.info("Scraping codes from web...")
        all_codes = scrape_genshin_codes()
        
        if not all_codes:
            logger.warning("No codes found from scraping")
            return
        
        # Get existing redeemed codes from gist
        logger.info("Getting existing redeemed codes...")
        existing_redeemed_codes = get_existing_redeemed_codes()
        
        # Filter out codes that have already been redeemed
        new_codes = filter_new_codes(all_codes, existing_redeemed_codes)
        
        if not new_codes:
            logger.info("No new codes to redeem")
            return
        
        # Initialize redeem API
        redeem_api = GenshinRedeemAPI(
            uid=env_vars['REDEEM_UID'],
            region=env_vars['REDEEM_REGION'],
            cookie=env_vars['COOKIE']
        )
        
        # Redeem codes
        logger.info("Starting code redemption...")
        newly_redeemed_codes = redeem_api.redeem_multiple_codes(new_codes)
        
        # Upload newly redeemed codes to gist
        if newly_redeemed_codes:
            logger.info(f"Uploading {len(newly_redeemed_codes)} newly redeemed codes to gist...")
            success = upload_redeemed_codes(newly_redeemed_codes)
            
            if success:
                logger.info("Successfully updated gist with newly redeemed codes")
            else:
                logger.error("Failed to update gist with newly redeemed codes")
        else:
            logger.info("No codes were successfully redeemed")
        
        logger.info("Code redemption process completed")
        
    except Exception as e:
        logger.error(f"Fatal error in main process: {e}")
        raise


if __name__ == '__main__':
    main()