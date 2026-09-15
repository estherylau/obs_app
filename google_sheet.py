import threading
import gspread
from google.oauth2.service_account import Credentials

from config import Config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly"
]

creds = Credentials.from_service_account_file(
    "service_account.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)

spreadsheet = client.open_by_key(Config.GOOGLE_SHEET_ID)
worksheet = spreadsheet.worksheet("Pearl")

camera_cache = []
camera_cache_lock = threading.Lock() # Create lock to avoid race condition.
column_map = {}

def refresh_cache():
    global camera_cache
    global column_map

    values = worksheet.get_all_values()

    if len(values) < 2:
        with camera_cache_lock:
            camera_cache = []
        return

    headers = [h.strip() for h in values[0]]

    column_map = {
        header: index
        for index, header in enumerate(headers)
    }

    existing_status = {
        camera["camera"]: camera
        for camera in camera_cache
    }

    required_headers = [
        "Ping",
        "Device Number",
        "Location",
        "IP Address",
        "Stream URL"
    ]

    for header in required_headers:
        if header not in column_map:
            raise ValueError(f"Missing column: {header}")

    # Preserve the current status of cameras.
    old_cache = {}

    with camera_cache_lock:
        for camera in camera_cache:
            old_cache[int(camera["camera"])] = camera

    new_cache = []
    counter = 1

    # Skip header row.
    for row in values[1:]:
        if not any(cell.strip() for cell in row):
            continue

        # Pad short rows.
        while len(row) < len(headers):
            row.append("")

        try:
            # camera_number = int(
            #     row[column_map["Device Number"]].strip()
            # )
            camera_number = row[column_map["Device Number"]].strip()
        except ValueError:
            continue

        ping = row[column_map["Ping"]].strip().lower()

        # Preserve the current status if we already have one.
        if camera_number in old_cache:
            status = old_cache[camera_number]["status"]
        else:
            status = "Not in use" if ping == "no" else "Offline"

        new_cache.append({
            "num": counter,
            "camera": camera_number,
            "location": row[column_map["Location"]].strip(),
            "ip_address": row[column_map["IP Address"]].strip(),
            "stream_url": row[column_map["Stream URL"]].strip(),
            "ping": ping,
            "status": status
        })

        counter += 1

    with camera_cache_lock:
        camera_cache = new_cache

def get_all_cameras():
    with camera_cache_lock:
        return list(camera_cache)

def get_cache():
    with camera_cache_lock:
        return list(camera_cache)

def get_camera(camera_id):
    with camera_cache_lock:
        print(f'camera_cache {camera_cache}')
        
        for camera in camera_cache:
            if camera["num"] == camera_id:
                return camera.copy()
    return None

def stop_camera(camera_id):
    camera = get_camera(camera_id)

    if camera is None:
        return False

    sheet_row = camera["num"] + 1

    worksheet.update_cell(
        sheet_row,
        column_map["Ping"] + 1,
        "No"
    )

    with camera_cache_lock:
        camera["ping"] = "no"
        camera["status"] = "Stopped"

    return True


