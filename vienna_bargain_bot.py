import requests
from telegram import Update, filters
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
)
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

def fetch_items(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        # Your parsing logic here
        return response.text  # or parsed data
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching {url}: {e}")
        return None

def run_bot(stop_event):
    print("Bot started. Checking every 60 seconds.")
    while not stop_event.is_set():
        # Example URLs — replace with your real ones
        categories = {
            "Smartphones": "https://www.willhaben.at/iad/kaufen-und-verkaufen/handys-telefonie-handys-angebot?areaId=900&sfId=1673544045",
            "Kameras": "https://www.willhaben.at/iad/kaufen-und-verkaufen/kameras-tv-multimedia-kameras-angebot?areaId=900",
            "Games": "https://www.willhaben.at/iad/kaufen-und-verkaufen/games-konsolen-angebot?areaId=900",
            "Computer": "https://www.willhaben.at/iad/kaufen-und-verkaufen/computer-software-angebot?areaId=900",
        }

        for category, url in categories.items():
            data = fetch_items(url)
            if data:
                # Process and send Telegram messages here
                print(f"Fetched data for {category}")
            else:
                print(f"Failed to fetch data for {category}")

        time.sleep(60)
