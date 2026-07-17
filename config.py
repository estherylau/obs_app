import os
from dotenv import load_dotenv

env_file = ".env"
if os.getenv("ENV") == "test":
       env_file = ".env.test"

load_dotenv(env_file)

class Config:
    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    GOOGLE_SHEET_TAB = os.getenv("GOOGLE_SHEET_TAB")
    REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", 10))
