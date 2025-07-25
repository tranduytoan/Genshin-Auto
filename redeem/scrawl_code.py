import requests
from bs4 import BeautifulSoup
from typing import List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GenshinCodeScraper:
    """Class to scrape Genshin Impact promotional codes from fandom wiki"""
    
    def __init__(self):
        self.url = "https://genshin-impact.fandom.com/wiki/Promotional_Code"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def fetch_page(self) -> str:
        """Fetch the promotional code page content"""
        try:
            logger.info(f"Fetching page: {self.url}")
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            logger.info("Page fetched successfully")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching page: {e}")
            raise
    
    def parse_codes(self, html_content: str) -> List[str]:
        """Parse promotional codes from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        codes = []
        
        try:
            tables = soup.select('#mw-content-text > div > table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    code_elements = row.find_all('code')
                    
                    for code_elem in code_elements:
                        code_text = code_elem.get_text(strip=True)
                        
                        if code_text and len(code_text) >= 8 and code_text.replace(' ', '').isalnum():
                            if code_text not in codes:
                                codes.append(code_text)
                                logger.info(f"Found code: {code_text}")
            
            logger.info(f"Total codes found: {len(codes)}")
            return codes
            
        except Exception as e:
            logger.error(f"Error parsing codes: {e}")
            raise
    
    def scrape_codes(self) -> List[str]:
        """Main method to scrape promotional codes"""
        try:
            html_content = self.fetch_page()
            codes = self.parse_codes(html_content)
            
            if codes:
                logger.info(f"Sy {len(codes)} promotional codes")
                return codes
            else:
                logger.warning("No promotional codes found")
                return []
                
        except Exception as e:
            logger.error(f"Failed to scrape codes: {e}")
            raise


def scrape_genshin_codes() -> List[str]:
    """Function to scrape Genshin Impact promotional codes"""
    try:
        scraper = GenshinCodeScraper()
        codes = scraper.scrape_codes()
        return codes
    except Exception as e:
        logger.error(f"Error occurred while scraping codes: {e}")
        return []