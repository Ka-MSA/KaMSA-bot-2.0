import os
from dotenv import load_dotenv
from telebot import apihelper

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables.")
