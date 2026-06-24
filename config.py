import os
from dotenv import load_dotenv

# 1. Try to load local .env variables if the file exists (useful for local laptop testing)
load_dotenv()

# 2. Extract the BOT_TOKEN directly from the environment variables injected by the host panel
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("CRITICAL ERROR: BOT_TOKEN is not set in the environment variables.")

# Note: PythonAnywhere's proxy config has been completely stripped out 
# so your network requests can flow natively out of Wispbyte!
