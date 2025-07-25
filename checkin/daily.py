import requests
import time
import datetime
import os
import logging
import json
from dotenv import load_dotenv
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GistManager:
    """Class to manage uploading check-in logs to GitHub Gist"""
    
    def __init__(self, gist_id: str, token: str):
        self.gist_id = gist_id
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        self.api_url = f"https://api.github.com/gists/{gist_id}"
    
    def upload_log(self, log_content: str) -> bool:
        """Upload check-in log to gist"""
        try:
            logger.info("Uploading check-in log to Gist...")
            
            # Get existing content
            response = requests.get(self.api_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            gist_data = response.json()
            current_content = gist_data.get('files', {}).get('genshin-checkin.log', {}).get('content', '')
            
            # Add separator and timestamp
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            separator = f"\n{'='*50}\n[{timestamp}] New Check-in Session\n{'='*50}\n"
            
            # Combine content
            updated_content = current_content + separator + log_content
            
            # Update gist
            data = {
                "files": {
                    "genshin-checkin.log": {
                        "content": updated_content
                    }
                }
            }
            
            response = requests.patch(self.api_url, json=data, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            logger.info("Successfully uploaded log to Gist")
            logger.info(f"Gist URL: https://gist.github.com/{self.gist_id}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error uploading to gist: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False


def checkin(apiUrl, apiPayload, apiHeaders) -> tuple[bool, str]:
    """
    Send request to check in api, return success status and log content
    :param apiUrl: url of the check in api
    :param apiPayload: payload of the check in api
    :param apiHeaders: headers of the check in api
    :return: tuple of (success, log_content)
    """
    log_content = []
    
    # Log time of request before sending request
    time_now = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
    log_content.append(f"Request at: {time_now}")
    logger.info(f"Starting check-in at {time_now}")

    # Request handling
    try:
        response = requests.post(apiUrl, json=apiPayload, headers=apiHeaders, timeout=30)
        response.raise_for_status()
        
        response_text = response.text
        log_content.append(f"\tResponse:\n\t\t{response_text}")
        
        message = response.json()['message']
        logger.info(f"Check-in response: {message}")
        print(message)
        
        # Display success message for GitHub Actions
        print("Daily check-in completed successfully!")
        return True, "\n".join(log_content)

    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        log_content.append(f"\tError:\n\t\t{error_msg}")
        logger.error(f"Check-in failed: {error_msg}")
        print("Daily check-in failed")
        print(f"Error: {error_msg}")
        return False, "\n".join(log_content)


def main():
    try:
        logger.info("Starting Genshin daily check-in process")
        load_dotenv()
        
        # Get environment variables
        act_id = os.getenv('ACT_ID')
        cookie = os.getenv('COOKIE')
        apiUrl = os.getenv('API_URL')
        gist_id = os.getenv('GIST_ID')
        github_token = os.getenv('GITHUB_TOKEN')

        # Validate required environment variables
        required_vars = {'ACT_ID': act_id, 'COOKIE': cookie, 'API_URL': apiUrl}
        missing_vars = [k for k, v in required_vars.items() if not v]
        
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            print(error_msg)
            print("Please set ACT_ID, COOKIE, and API_URL in GitHub Secrets")
            exit(1)

        # Prepare API request
        url = apiUrl
        payload = {"act_id": act_id}
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": cookie,
            "Origin": "https://act.hoyolab.com",
            "Priority": "u=1, i",
            "Referer": "https://act.hoyolab.com/",
            "Sec-Ch-Ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
            "Sec-Ch-Ua-Platform": "\"Windows\"",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        
        # Perform check-in
        success, log_content = checkin(url, payload, headers)
        
        # Upload to Gist if credentials are available
        if gist_id and github_token:
            logger.info("Uploading log to Gist...")
            gist_manager = GistManager(gist_id, github_token)
            if gist_manager.upload_log(log_content):
                logger.info("Log uploaded to Gist successfully")
            else:
                logger.warning("Failed to upload log to Gist")
        else:
            logger.info("Gist credentials not provided, skipping log upload")
        
        # Exit with appropriate code
        if not success:
            logger.error("Check-in failed")
            exit(1)
        else:
            logger.info("Check-in process completed successfully")
            
    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
        print(f"Fatal error: {e}")
        exit(1)


if __name__ == '__main__':
    main()