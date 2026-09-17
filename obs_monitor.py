import json
import requests
import time
import threading
import urllib3
from config import Config
from app import busy_light

from concurrent.futures import ThreadPoolExecutor, as_completed

import gspread
from google.oauth2.service_account import Credentials

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
MAX_WORKERS = 30
AUTH = (Config.PEARL_USERNAME, Config.PEARL_PASSWORD)

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

# Worker pool
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Prevent overlapping polling cycles
poll_lock = threading.Lock()

# Embrava light
# from busy_light import BusyLightDriver
# busy_light = BusyLightDriver()

def initialize_embrava_light():
    """
    Detect the Embrava light on Windows or macOS.

    If the light is not connected or cannot be accessed,
    the monitor continues without light support.
    """
    global embrava_light

    try:
        from busylight_core import EmbravaLights

        lights = EmbravaLights.all_lights()

        if not lights:
            print("No Embrava light detected.")
            return

        embrava_light = lights[0]

        print(
            f"Embrava light detected: "
            f"{getattr(embrava_light, 'name', 'Embrava')}"
        )

        # Test the light on startup
        embrava_light.on((0, 255, 0))
        time.sleep(1)
        embrava_light.off()

        print("Embrava light test successful.")

    except ImportError:
        print(
            "busylight-core is not installed. "
            "Continuing without Embrava light."
        )
        embrava_light = None

    except Exception as ex:
        print(
            f"Unable to initialize Embrava light: {ex}"
        )

        embrava_light = None


initialize_embrava_light()

# GET LOCATIONS FROM GOOGLE SHEET
def get_locations():
    values = worksheet.get_all_values()

    if len(values) < 2:
        return []

    headers = [header.strip() for header in values[0]]

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

    # Google Sheet row numbers start at 2 because row 1 is headers.
    for sheet_row, row in enumerate(values[1:], start=2):
        # Ignore rows outside the configured monitor range.
        if sheet_row < Config.MONITOR_START_ROW:
            continue

        if sheet_row > Config.MONITOR_END_ROW:
            break

        # Ignore empty rows
        if not any(cell.strip() for cell in row):
            continue

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
    # print(f"fetch_location: {location}")
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

    try:
        url = f"http://{ip_address}/api/recorders/status"
        print(f'ip_address: {url}')

        response = requests.get(
            url,
            verify=False,
            auth=AUTH,
            timeout=5
        )
        # print(f"fetch_location.reponse: ${response}")

        response.raise_for_status()
        data = response.json()
        
        output_data = data

        results = output_data.get(
            "result",
            []
        )

        # COLLECT CHANNEL STATES
        # =================================================

        started_ids = [
            item.get("id")
            for item in results
            if item.get(
                "status",
                {}
            ).get("state") == "started"
        ]


        error_ids = [
            item.get("id")
            for item in results
            if item.get(
                "status",
                {}
            ).get("state") == "error"
        ]


        disabled_ids = [
            item.get("id")
            for item in results
            if item.get(
                "status",
                {}
            ).get("state") == "disabled"
        ]


        # =================================================
        # DETERMINE OVERALL STATUS
        # =================================================

        if error_ids:

            channel_status = (
                "ERROR Channel "
                + ", ".join(error_ids)
            )


        elif disabled_ids:

            channel_status = (
                "Disabled Channel "
                + ", ".join(disabled_ids)
            )


        elif started_ids:

            channel_status = (
                "Channel "
                + ", ".join(started_ids)
            )


        elif results and all(
            item.get(
                "status",
                {}
            ).get("state") == "stopped"
            for item in results
        ):

            channel_status = "Not recording"


        else:

            channel_status = "Unknown"

        # # COLLECT CHANNEL STATES
        # started_ids = [
        #     item.get("id")
        #     for item in results
        #     if item.get(
        #         "status",
        #         {}
        #     ).get("state") == "started"
        # ]

        # # channel_status = get_channel_status(output_data)

        # # Inject 'custom' key based on 'stopped' presence
        # if any(item.get("status", {}).get("state") == "error" for item in output_data.get("result", [])):
        #     channel_status = "ERROR Channel " + ", ".join(started_ids)

        # elif any(item.get("status", {}).get("state") == "disabled" for item in output_data.get("result", [])):
        #     channel_status = "Disabled Channel " + ", ".join(started_ids)

        # elif any(item.get("status", {}).get("state") == "started" for item in output_data.get("result", [])):
        #     # Filter to collect ids with state == "started"
        #     started_ids = [
        #         item["id"] for item in output_data.get("result", [])
        #         if item.get("status", {}).get("state") == "started"
        #     ]

        #     # Add to your JSON
        #     channel_status = "Channel " + ", ".join(started_ids)

        # elif any(item.get("status", {}).get("state") == "stopped" for item in output_data.get("result", [])):
        #     channel_status = "Not recording"

        return {
            "num": num,
            "location": location_name,
            "ip_address": ip_address,
            "status": channel_status,
            "data": output_data
        }

    except requests.exceptions.ConnectionError as e:
        # print(f"{ip_address} - Connection Error: {e}")
        print(f"{ip_address} - Connection Error")

    except requests.exceptions.Timeout as e:
        print(f"{ip_address} - Timeout: {e}")

    except Exception as e:
        print(f"{ip_address} - Error: {e}")

    # Offline Result
    return {
        "num": num,
        "location": location_name,
        "ip_address": ip_address,
        "status": "OFFLINE",
        "data": output_data
    }

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
        # Don't start another polling cycle if the previous
        # cycle is still running.
        if not poll_lock.acquire(blocking=False):
            print("Previous polling cycle still running. Skipping this cycle.")
            time.sleep(Config.REFRESH_INTERVAL)
            continue

        try:
            locations = get_locations()

            futures = {
                executor.submit(fetch_location, location): location
                for location in locations
            }

            results = []
            any_api_error = False

            for future in as_completed(futures):
                location = futures[future]
                try:
                    result = future.result()

                    if result is not None:
                        results.append(result)

                    if result["status"] == "OFFLINE":
                        any_api_error = True

                except Exception as ex:
                    any_api_error = True

                    print(
                        f"Error processing "
                        f"{location['ip_address']}: {ex}"
                    )

                    results.append({
                        "num": location["num"],
                        "location": location["location"],
                        "ip_address": location["ip_address"],
                        "status": "OFFLINE",
                        "result": []
                    })

            # Keep the UI in num order
            results.sort(key=lambda x: x["num"])

            with results_lock:
                results_cache[:] = results

            # Embrava error indicator
            if any_api_error:
            	busy_light.set_status("fail")
            else:
            	busy_light.off()

        except Exception as ex:
            print(f"Monitor loop error: {ex}")
            set_error_light()

        finally:
            poll_lock.release()

        time.sleep(Config.REFRESH_INTERVAL)

# Embrava light helper function
def set_error_light():
    """Turn the Embrava light red and blinking if available."""
    print(f"set_error_light")
    if embrava_light is None:
        return

    try:
        embrava_light.on((255, 0, 0))
    except Exception as ex:
        print(f"Unable to activate Embrava light: {ex}")

def clear_error_light():
    """Turn off the Embrava light if available."""

    if embrava_light is None:
        return

    try:
        embrava_light.off()
    except Exception as ex:
        print(f"Unable to turn off Embrava light: {ex}")


# START MONITOR
def start():
    thread = threading.Thread(
        target=monitor_loop,
        daemon=True,
        name="OBSMonitor"
    )

    thread.start()
