import requests
import time
import datetime
import subprocess
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
    # There are 3 cases here:
    # 1. Request is successful, user has already checked in before
    # 2. Request is successful, user has not checked in before and has just checked in
    # 3. Request is unsuccessful (error)
    try:
        response = requests.post(apiUrl, json=apiPayload, headers=apiHeaders)
        response.raise_for_status()
        log_request("\tResponse:\n\t\t" + response.text)
        message = response.json()['message']
        print(message)
        batch_command = "type res\\ok.txt & echo."
        subprocess.run(batch_command, shell=True)

        # update daycheck.txt
        now = datetime.datetime.now().date()
        with open('daycheck.txt', 'w') as file:
            file.write(now.strftime("%Y-%m-%d"))
    except requests.exceptions.RequestException as e:
        print("Diem danh that bai")
        log_request("\tError:\n\t\t" + str(e))


def main():
    load_dotenv()
    act_id = os.getenv('ACT_ID')
    cookie = os.getenv('COOKIE')
    apiUrl = os.getenv('API_URL')

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
