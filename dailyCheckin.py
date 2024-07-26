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
        batch_command = "type res\ok.txt & echo."
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

    url = 'https://sg-hk4e-api.hoyolab.com/event/sol/sign?lang=vi-vn'
    payload = {"act_id": act_id}
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": "_MHYUUID=bc03fd76-961d-43ba-820f-07c50dfa6907; HYV_LOGIN_PLATFORM_OPTIONAL_AGREEMENT={%22content%22:[]}; DEVICEFP_SEED_ID=4aef3a34346f38a4; DEVICEFP_SEED_TIME=1695879344648; account_mid_v2=10peame57f_hy; account_id_v2=206741532; ltmid_v2=10peame57f_hy; ltuid_v2=206741532; hoyolab_color_scheme=system; cookie_token_v2=v2_CAQSDGNlMXRidXdiMDB6axokYmMwM2ZkNzYtOTYxZC00M2JhLTgyMGYtMDdjNTBkZmE2OTA3ILfU37AGKNDCpZUBMJzAymJCC2hrNGVfZ2xvYmFs; ltoken_v2=v2_CAISDGNlMXRidXdiMDB6axokYmMwM2ZkNzYtOTYxZC00M2JhLTgyMGYtMDdjNTBkZmE2OTA3ILfU37AGKO7i6LkGMJzAymJCC2hrNGVfZ2xvYmFs; HYV_LOGIN_PLATFORM_LOAD_TIMEOUT={}; mi18nLang=vi-vn; DEVICEFP=38d7f1df14e66; HYV_LOGIN_PLATFORM_TRACKING_MAP={%22sourceValue%22:%2276%22}; HYV_LOGIN_PLATFORM_LIFECYCLE_ID={%22value%22:%225ab8d17d-933a-438e-be83-2a54089c7073%22}",
        "Origin": "https://act.hoyolab.com",
        "Priority": "u=1, i",
        "Referer": "https://act.hoyolab.com/",
        "Sec-Ch-Ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "X-Rpc-Device_id": "bc03fd76-961d-43ba-820f-07c50dfa6907",
        "X-Rpc-Platform": "4"
    }
    diem_danh(url, payload, headers)


if __name__ == '__main__':
    main()
