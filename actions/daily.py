import requests
import time
import datetime
import os
from dotenv import load_dotenv


def log_request(message):
    """
    Log a message to log.txt
    :param message: message that needs to be logged
    """
    with open("log.txt", "a", encoding="utf-8") as file:
        file.write(message + "\n")


def diem_danh(apiUrl, apiPayload, apiHeaders):
    """
    Send request to check in api, log response to log.txt and print message to console
    :param apiUrl: url of the check in api
    :param apiPayload: payload of the check in api
    :param apiHeaders: headers of the check in api
    """

    # Log time of request before sending request
    time_now = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
    log_request("Request at: " + time_now)

    # Request handling
    try:
        response = requests.post(apiUrl, json=apiPayload, headers=apiHeaders)
        response.raise_for_status()
        log_request("\tResponse:\n\t\t" + response.text)
        message = response.json()['message']
        print(message)
        
        # Display success message for GitHub Actions
        print("✅ Daily check-in completed successfully!")
        
        # Print success ASCII art if file exists
        if os.path.exists("res/ok.txt"):
            with open("res/ok.txt", "r", encoding="utf-8") as f:
                print(f.read())

    except requests.exceptions.RequestException as e:
        print("❌ Daily check-in failed")
        print(f"Error: {str(e)}")
        log_request("\tError:\n\t\t" + str(e))
        
        # Print failure ASCII art if file exists
        if os.path.exists("res/failed.txt"):
            with open("res/failed.txt", "r", encoding="utf-8") as f:
                print(f.read())
        
        # Exit with error code for GitHub Actions
        exit(1)


def main():
    load_dotenv()
    act_id = os.getenv('ACT_ID')
    cookie = os.getenv('COOKIE')
    apiUrl = os.getenv('API_URL')

    # Validate required environment variables
    if not all([act_id, cookie, apiUrl]):
        print("❌ Missing required environment variables")
        print("Please set ACT_ID, COOKIE, and API_URL in GitHub Secrets")
        exit(1)

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
    diem_danh(url, payload, headers)


if __name__ == '__main__':
    main()