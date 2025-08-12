import os
import sys
from typing import List, Dict, Any, Optional, Set

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))
try:
    from discord_webhook import send_discord_notification
    from constants import MIMO_LIST_TASKS_API_URL, MIMO_FINISH_TASK_API_URL, MIMO_RECEIVE_POINT_API_URL, DEFAULT_HEADERS
except ImportError:
    def send_discord_notification(content):
        return False
    
    MIMO_LIST_TASKS_API_URL = "https://sg-public-api.hoyolab.com/event/e2023mimotravel/nata/task_list?game_id=2&version_id=58"
    MIMO_FINISH_TASK_API_URL = "https://sg-public-api.hoyolab.com/event/e2023mimotravel/nata/finish_task"
    MIMO_RECEIVE_POINT_API_URL = "https://sg-public-api.hoyolab.com/event/e2023mimotravel/nata/receive_point"
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

def get_list_tasks(headers: dict) -> Optional[Dict]:    
    try:
        response = requests.get(MIMO_LIST_TASKS_API_URL, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        if data.get('retcode') == 0 and data.get('message') == 'OK':
            task_list = data.get('data', {}).get('task_list', [])
            return task_list if task_list else None
        else:
            return None
    except Exception as e:
        return None
    

def finish_tasks(headers: dict, task_list: Optional[Dict]) -> List[Dict[str, Any]]:
    if not task_list:
        return []

    tasks_to_finish: Optional[Dict] = []
    for task in task_list:
        if task.get('status') != 1:
            tasks_to_finish.append(task)
    
    if not tasks_to_finish:
        return []

    finish_statuses: List[Dict[str, Any]] = []

    for task in tasks_to_finish:
        status = "failed" if task.get('task_type') == 3 else None
        if status:
            finish_statuses.append({
                "task_id": task.get('task_id'),
                "task_name": task.get('task_name'),
                "point": task.get('point'),
                "finish_status": status
            })
            continue

        payload = {
            "task_id": task.get('task_id'),
            "game_id": 2,
            "version_id": 58,
            "lang": "en-us"
        }
        try:
            response = requests.post(MIMO_FINISH_TASK_API_URL, json=payload, headers=headers, timeout=30)
            result = response.json()
            status = "success" if result.get('retcode') == 0 and result.get('message') == 'OK' else "failed"
        except Exception:
            status = "error"
        finish_statuses.append({
            "task_id": task.get('task_id'),
            "task_name": task.get('task_name'),
            "point": task.get('point'),
            "finish_status": status
        })
    return finish_statuses


def receive_point(headers: dict, finish_statuses: Optional[Dict]) -> List[Dict[str, Any]]:
    if not finish_statuses:
        return []

    receive_statuses: List[Dict[str, Any]] = []
    payload = {
        "game_id": 2,
        "version_id": 58,
        "lang": "en-us"
    }

    for task in finish_statuses:
        receive_status = None
        if task["finish_status"] == "success":
            params = { "task_id": task["task_id"] }
            try:
                response = requests.post(MIMO_RECEIVE_POINT_API_URL, json=payload, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                receive_status = "success" if response.json().get("retcode") == 0 else "failed"
            except Exception:
                receive_status = "error"
            
        else:
            receive_status = "not_finished"
        receive_statuses.append({
            "task_id": task["task_id"],
            "task_name": task["task_name"],
            "point": task["point"],
            "finish_status": task["finish_status"],
            "receive_status": receive_status
        })

    return receive_statuses


def main():
    load_dotenv()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": os.getenv('COOKIE')
    }

    task_list = get_list_tasks(headers)
    if not task_list:
        print("Failed to retrieve task list.")
        return

    finish_statuses = finish_tasks(headers, task_list)
    if not finish_statuses:
        print("No tasks to finish or all tasks already completed.")
        return

    receive_statuses = receive_point(headers, finish_statuses)
    content = ""
    for status in receive_statuses:
        print(f"Task: {status['task_name']}, Finish Status: {status['finish_status']}, Receive Status: {status.get('receive_status', 'N/A')}")
        #discord noti
        content += f"Task: {status['task_name']}, Finish Status: {status['finish_status']}, Receive Status: {status.get('receive_status', 'N/A')}\n"
    if content:
        send_discord_notification(content)

if __name__ == "__main__":
    main()