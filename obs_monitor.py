import json
import requests
import time
import threading
import urllib3
from config import Config

from concurrent.futures import ThreadPoolExecutor

import gspread
from google.oauth2.service_account import Credentials

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# CONFIGURATION
REFRESH_INTERVAL = 5  # seconds
AUTH = ("admin", "scapture123!")

# GOOGLE SHEET
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly"
]
creds = Credentials.from_service_account_file(
    "service_account.json",
    scopes=SCOPES
)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key(
    Config.GOOGLE_SHEET_ID
)

worksheet = spreadsheet.worksheet("Pearl")

# CACHE
results_cache = []
results_lock = threading.Lock()

# GET LOCATIONS FROM GOOGLE SHEET
def get_locations():
    values = worksheet.get_all_values()

    if len(values) < 2:
        return []

    headers = [
        header.strip()
        for header in values[0]
    ]

    column_map = {
        header: index
        for index, header in enumerate(headers)
    }

    required_columns = [
        "Ping",
        "Device Number",
        "Type",
        "Location",
        "IP Address"
    ]

    for column in required_columns:
        if column not in column_map:
            raise ValueError(
                f"Missing Google Sheet column: {column}"
            )

    locations = []

    num = 1

    for row in values[1:]:
        print(f"row: {row}")
        # Make sure the row has enough columns
        while len(row) < len(headers):
            row.append("")

        is_ping = row[column_map["Ping"]].strip()

        ip_address = row[column_map["IP Address"]].strip()

        location = row[column_map["Location"]].strip()

        if not ip_address:
            continue

        locations.append({
            "num": num,
            "location": location,
            "ip_address": ip_address,
            "is_ping": is_ping
        })

        num += 1

    return locations

# FETCH ONE LOCATION
def fetch_location(location):
    print(f"fetch_location: {location}")
    num = location["num"]
    location_name = location["location"]
    ip_address = location["ip_address"]
    ping = location["is_ping"]

    output_data = {
        "status": "running",
        "results": []
    }

    # Disable pining in Google Sheet
    if ping.lower() == "no":
        return {
            "num": num,
            "location": location_name,
            "ip_address": ip_address,
            "status": "The room is not in use",
            "data": output_data
        }
        # channel_status = "The room is not in use"

    url = f"http://{ip_address}/api/recorders/status"
    
    print(f'ip_address: {url}')
    try:
        response = requests.get(
            url,
            verify=False,
            auth=AUTH,
            timeout=5
        )
        print(f"fetch_location.reponse: ${response}")

        response.raise_for_status()
        data = response.json()
        
        output_data = data
        # channel_status = get_channel_status(output_data)

        # Inject 'custom' key based on 'stopped' presence
        if any(item.get("status", {}).get("state") == "error" for item in output_data.get("result", [])):
            channel_status = "ERROR Channel " + ", ".join(started_ids)

        elif any(item.get("status", {}).get("state") == "disabled" for item in output_data.get("result", [])):
            channel_status = "Disabled Channel " + ", ".join(started_ids)

        elif any(item.get("status", {}).get("state") == "started" for item in output_data.get("result", [])):
            # Filter to collect ids with state == "started"
            started_ids = [
                item["id"] for item in output_data.get("result", [])
                if item.get("status", {}).get("state") == "started"
            ]

            # Add to your JSON
            channel_status = "Channel " + ", ".join(started_ids)

        elif any(item.get("status", {}).get("state") == "stopped" for item in output_data.get("result", [])):
            channel_status = "Not recording"

    except requests.exceptions.ConnectionError as e:
        # print(f"{ip_address} - Connection Error: {e}")
        print(f"{ip_address} - Connection Error")
        channel_status = "OFFLINE"

    except requests.exceptions.Timeout as e:
        print(f"{ip_address} - Timeout: {e}")
        channel_status = "OFFLINE"

    except Exception as e:
        print(f"{ip_address} - Error: {e}")
        channel_status = "OFFLINE"

    # Add information about this location.
    output = {
        "num": num,
        "location": location_name,
        "ip_address": ip_address,
        "status": channel_status,
        "data": output_data
    }

    return output

def get_channel_status(data):
    results = data.get("result", [])

    started_ids = [
        item["id"]
        for item in results
        if item.get("status", {}).get("state") == "started"
    ]

    if started_ids:
        return "Channel " + ", ".join(started_ids)

    if results and all(
        item.get("status", {}).get("state") == "stopped"
        for item in results
    ):
        return "Not Recording"

    return "Offline"


# POLL ALL LOCATIONS
def poll_all_locations():
    global results_cache

    locations = get_locations()

    if not locations:
        with results_lock:
            results_cache = []

        return

    with ThreadPoolExecutor(
        max_workers=len(locations)
    ) as executor:

        # futures = [
        #     executor.submit(
        #         fetch_location,
        #         index
        #     )
        #     for index in range(len(SOURCE_URLS))
        # ]

        new_results = list(
            executor.map(
                fetch_location,
                locations
            )
        )

    with results_lock:
        results_cache = new_results


# GET CURRENT RESULTS
def get_results():
    with results_lock:
        return list(results_cache)


# MONITOR LOOP
def monitor_loop():
    while True:
        poll_all_locations()

        time.sleep(REFRESH_INTERVAL)


# START MONITOR
def start():
    thread = threading.Thread(
        target=monitor_loop,
        daemon=True,
        name="OBSMonitor"
    )

    thread.start()
