import os
from dotenv import load_dotenv

env_file = ".env"
if os.getenv("ENV") == "test":
       env_file = ".env.test"

load_dotenv(env_file)

class Config:
    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    GOOGLE_SHEET_TAB = os.getenv("GOOGLE_SHEET_TAB")
    PEARL_USERNAME = os.getenv("PEARL_USERNAME")
    PEARL_PASSWORD = os.getenv("PEARL_PASSWORD")
    REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", 10))
    MONITOR_START_ROW = int(os.getenv("MONITOR_START_ROW", 10))
    MONITOR_END_ROW = int(os.getenv("MONITOR_END_ROW", 10))