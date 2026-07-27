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
column_map = {}

def refresh_cache():
    global camera_cache

    rows = worksheet.get_all_records()

    headers = rows[0]
    new_cache = []
    counter = 0

    global column_map

    column_map = {
        header.strip(): index
        for index, header in enumerate(headers)
        if header.strip()
    }

    for row in rows:
        counter = counter + 1
        ping = row["Ping"].strip().lower()
        status = "Playing" if ping == "yes" else "Stopped"

        new_cache.append({
            "num": int(counter),
            "camera": row["Device Number"],
            "location": row["Location"],
            "ip_address": row['IP Address'].strip(),
            "status": status,
            "ping": ping
        })

    camera_cache = new_cache


def get_cache():
    return camera_cache

def get_camera(camera_id):
    print(f'camera_cache {camera_cache}')
    for camera in camera_cache:

        if camera["num"] == camera_id:
            return camera

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

    camera["ping"] = "no"
    camera["status"] = "Stopped"

    return True
