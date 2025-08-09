# vienna_bargain_bot.py
import requests
import time
from bs4 import BeautifulSoup
import threading
import os

# Read tokens from environment variables for safety (set these in Render dashboard)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7582551179:AAFl3EDbpByJKhQ72d5el67wbonkm1tRue8")
CHAT_ID = os.environ.get("CHAT_ID", "580150046")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60"))

CATEGORIES = {
    "Smartphones": "https://www.willhaben.at/iad/kaufen-und-verkaufen/handys-telefonie-handys-angebot?areaId=900&sfId=1673544045",
    "Kameras": "https://www.willhaben.at/iad/kaufen-und-verkaufen/kameras-tv-multimedia-kameras-angebot?areaId=900",
    "Games": "https://www.willhaben.at/iad/kaufen-und-verkaufen/games-konsolen-angebot?areaId=900",
    "Computer": "https://www.willhaben.at/iad/kaufen-und-verkaufen/computer-software-angebot?areaId=900"
}

PRICE_LIMITS = {
    "Smartphones": 100,
    "Kameras": 150,
    "Games": 80,
    "Computer": 120
}

seen_links = set()
_lock = threading.Lock()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Error sending Telegram message:", e)

def scrape_category(name, url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ViennaBot/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return

    for item in soup.select("article"):
        link_tag = item.find("a", href=True)
        price_tag = item.find("div", class_="price")
        title_tag = item.find("h3")

        if not link_tag or not price_tag or not title_tag:
            continue

        link = "https://www.willhaben.at" + link_tag["href"]
        title = title_tag.get_text(strip=True)
        price_text = price_tag.get_text(strip=True).replace("€", "").replace(".", "").strip()

        try:
            price = int(price_text.split()[0])
        except:
            continue

        with _lock:
            already_seen = link in seen_links
            if not already_seen and price <= PRICE_LIMITS.get(name, 9999):
                seen_links.add(link)
                msg = f"📦 <b>{name}</b>\n{title}\n💶 {price} EUR\n🔗 {link}"
                send_telegram_message(msg)

def run_bot(stop_event):
    """Main loop — run until stop_event is set."""
    send_telegram_message("🚀 Vienna Bargain Bot started (web-service mode)!")
    print("Bot started. Checking every", CHECK_INTERVAL, "seconds.")
    while not stop_event.is_set():
        for category, url in CATEGORIES.items():
            scrape_category(category, url)
        # sleep in small steps so we can stop quickly if Render restarts
        for _ in range(int(CHECK_INTERVAL)):
            if stop_event.is_set():
                break
            time.sleep(1)
    print("Bot stopping.")
