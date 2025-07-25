import os
import re
import time
import logging
import requests
from typing import List, Dict, Any
from scrawl_code import scrape_genshin_codes
from upload_to_gist import upload_redeemed_codes, get_existing_redeemed_codes

# --- Config ---
REQUIRED_ENV_VARS = ['REDEEM_UID', 'REDEEM_REGION', 'COOKIE', 'GIST_ID', 'METRICS_TOKEN']
BASE_URL = "https://public-operation-hk4e.hoyoverse.com/common/apicdkey/api/webExchangeCdkey"

# --- Logger setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GenshinRedeemAPI:
    def __init__(self, uid: str, region: str, cookie: str):
        self.uid, self.region = uid, region
        self.session = requests.Session()
        self.session.headers.update({
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def redeem_code(self, code: str, retries: int = 3) -> Dict[str, Any]:
        def _extract_wait_time(msg: str) -> int:
            match = re.search(r'try again in (\d+) second', msg)
            return int(match.group(1)) + 1 if match else 5

        for attempt in range(retries + 1):
            try:
                logger.info(f"Redeeming code {code} (Attempt {attempt})")
                response = self.session.get(BASE_URL, params={
                    'lang': 'en', 'game_biz': 'hk4e_global', 'sLangKey': 'en-us',
                    'uid': self.uid, 'region': self.region, 'cdkey': code
                }, timeout=30)
                response.raise_for_status()
                result = response.json()
                retcode, msg = result.get('retcode', -1), result.get('message', 'Unknown error')

                logger.info(f"Code {code} - retcode: {retcode} - {msg}")

                if retcode == -2016 and attempt < retries:
                    time.sleep(_extract_wait_time(msg))
                    continue

                return result

            except requests.RequestException as e:
                logger.warning(f"Network error: {e}")
                if attempt == retries:
                    return {'retcode': -1, 'message': f'Network error: {e}'}
                time.sleep(2)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt == retries:
                    return {'retcode': -1, 'message': f'Unexpected error: {e}'}

        return {'retcode': -1, 'message': 'Max retries exceeded'}

    def redeem_multiple_codes(self, codes: List[str]) -> List[str]:
        redeemed = []
        for code in codes:
            try:
                result = self.redeem_code(code)
                if result.get('retcode') in [0, -2017, -1007]:
                    logger.info(f"Code {code} marked as redeemed")
                    redeemed.append(code)
                else:
                    logger.warning(f"Code {code} not redeemed: {result.get('retcode')}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error with code {code}: {e}")
        return redeemed

def load_env() -> Dict[str, str]:
    env = {var: os.getenv(var) for var in REQUIRED_ENV_VARS}
    missing = [k for k, v in env.items() if not v]
    if missing:
        raise ValueError(f"Missing env vars: {', '.join(missing)}")
    logger.info("Environment variables loaded")
    return env

def filter_new_codes(all_codes: List[str], redeemed: List[str]) -> List[str]:
    new_codes = list(set(all_codes) - set(redeemed))
    logger.info(f"Found {len(all_codes)} total codes, {len(redeemed)} redeemed, {len(new_codes)} new")
    return new_codes

def main():
    try:
        logger.info("Starting redemption process")
        env = load_env()

        all_codes = scrape_genshin_codes()
        if not all_codes:
            logger.warning("No codes found")
            return

        redeemed = get_existing_redeemed_codes()
        new_codes = filter_new_codes(all_codes, redeemed)
        if not new_codes:
            logger.info("No new codes to redeem")
            return

        api = GenshinRedeemAPI(env['REDEEM_UID'], env['REDEEM_REGION'], env['COOKIE'])
        new_redeemed = api.redeem_multiple_codes(new_codes)

        if new_redeemed:
            logger.info(f"Uploading {len(new_redeemed)} redeemed codes to Gist...")
            if upload_redeemed_codes(new_redeemed):
                logger.info("Gist updated successfully")
            else:
                logger.error("Failed to update Gist")
        else:
            logger.info("No codes were successfully redeemed")

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
