import threading
import time
import requests
import urllib3

import google_sheet
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USERNAME = "admin"
PASSWORD = "scapture123!"

POLL_INTERVAL = 5


def poll_camera(camera):
    # Skip polling camera that is not in use.
    ping = camera["ping"].strip().lower()
    if ping == "no":
        # TODO: Stop pinging.
        camera["status"] = "Not in use"
        return

    url = f"http://{camera['ip_address']}/api/recorders/status"
    # print(f"what is camera: {camera}")
    print(f"Camera {camera['camera']} -> Offlinee")
    camera["status"] = "Offline"
    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            verify=False,
            timeout=3
        )

        response.raise_for_status()
        data = response.json()
        # print(f'poll camera: {data}')
        #
        # Expected:
        # {
        #     "status": "Playing",
        #     "result": []
        # }
        #

        # Set camera status
        print(f"Camera {camera['camera']} -> running")
        camera["status"] = set_camera_status(data)

        return
        # camera["status"] = data.get("status", "Unknown")

    except requests.exceptions.ConnectionError as e:
        print(f"Camera {camera['camera']} -> Connection Error")
        camera["status"] = "Offline"

    except requests.exceptions.Timeout as e:
        print(f"Camera {camera['camera']} -> Timeout Error")
        camera["status"] = "Offline"

    except Exception as ex:
        print(f"exception: {ex}")
        print(f"Camera {camera['camera']} -> Exception")

        camera["status"] = "Offline"

def monitor_loop():
    while True:
        cameras = list(google_sheet.get_all_cameras())
        
        # Poll all cameras concurrently
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [
                executor.submit(poll_camera, camera)
                for camera in cameras
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as ex:
                    print("Thread exception:", ex)

            # executor.map(poll_camera, cameras)

        time.sleep(POLL_INTERVAL)

def start():
    thread = threading.Thread(
        target=monitor_loop,
        daemon=True
    )

    thread.start()

def set_camera_status(data):
    started_ids = []
    output_data = data
    if any(item.get("status", {}).get("state") == "error" for item in output_data.get("result", [])):
        return "ERROR Channel " + ", ".join(started_ids)

    elif any(item.get("status", {}).get("state") == "disabled" for item in output_data.get("result", [])):
        return "Disabled Channel " + ",".join(started_ids)

    elif any(item.get("status", {}).get("state") == "started" for item in output_data.get("result", [])):
        # Filter to collect ids with state == 'started'
        started_ids = [
            item["id"] for item in output_data.get("result", [])
            if item.get("status", {}).get("state") == "started"
        ]
        return "Channel " + ", ".join(started_ids)

    elif any(item.get("status", {}).get("state") == "stopped" for item in output_data.get("result", [])):
        return "Not recording"

    return 'Off Limit'

