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

def refresh_cache():
    global camera_cache

    rows = worksheet.get_all_records()
    new_cache = []
    counter = 0

    for row in rows:
        counter = counter + 1
        ping = row["Ping"].strip().lower()
        status = "Playing" if ping == "yes" else "Stopped"

        new_cache.append({
            "num": int(counter),
            "camera": row["Device Number"],
            "location": row["Location"],
            "status": status,
            "ping": ping
        })

    camera_cache = new_cache


def get_cache():
    return camera_cache
