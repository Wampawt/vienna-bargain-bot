import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))

# Categories and their Willhaben URLs for Vienna (areaId=900)
CATEGORIES = {
    "Smartphones": "https://www.willhaben.at/iad/kaufen-und-verkaufen/handys-telefonie-handys-angebot?areaId=900",
    "Kameras": "https://www.willhaben.at/iad/kaufen-und-verkaufen/kameras-tv-multimedia-kameras-angebot?areaId=900",
    "Games": "https://www.willhaben.at/iad/kaufen-und-verkaufen/games-konsolen-angebot?areaId=900",
    "Computer": "https://www.willhaben.at/iad/kaufen-und-verkaufen/computer-software-angebot?areaId=900",
    "Bücher": "https://www.willhaben.at/iad/kaufen-und-verkaufen/buecher-angebot?areaId=900",
    "Möbel": "https://www.willhaben.at/iad/kaufen-und-verkaufen/moebel-angebot?areaId=900",
    "Fahrräder": "https://www.willhaben.at/iad/kaufen-und-verkaufen/fahrrad-angebot?areaId=900",
    "Sport": "https://www.willhaben.at/iad/kaufen-und-verkaufen/sport-angebote?areaId=900",
    "Haushalt": "https://www.willhaben.at/iad/kaufen-und-verkaufen/haushalt-angebot?areaId=900",
    "Kleidung": "https://www.willhaben.at/iad/kaufen-und-verkaufen/kleidung-angebot?areaId=900",
}

# Use realistic browser headers to avoid 403 Forbidden
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.willhaben.at/"
}

bot = Bot(token=BOT_TOKEN)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        print("Telegram send status:", resp.status_code, resp.text)
    except Exception as e:
        print("Error sending Telegram message:", e)

def scrape_category(name, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return []

    # Parse listings (basic example, adjust selectors to actual Willhaben HTML)
    listings = []
    items = soup.select("article.ads__unit")  # Willhaben's ad container class
    for item in items[:5]:  # top 5 items
        title_el = item.select_one(".ads__unit__title")
        price_el = item.select_one(".ads__unit__price")
        link_el = item.select_one("a")
        if title_el and price_el and link_el:
            title = title_el.text.strip()
            price = price_el.text.strip()
            link = "https://www.willhaben.at" + link_el.get("href")
            listings.append(f"{title} - {price}\n{link}")
    return listings

def start(update: Update, context: CallbackContext):
    keyboard = [[category] for category in CATEGORIES.keys()]
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(
        "Choose a category to get the top 5 current bargains in Vienna:",
        reply_markup=reply_markup,
    )
    return 1

def category_selected(update: Update, context: CallbackContext):
    category = update.message.text
    if category not in CATEGORIES:
        update.message.reply_text("Please select a valid category.")
        return 1

    update.message.reply_text(f"Fetching bargains for {category}...")

    listings = scrape_category(category, CATEGORIES[category])
    if listings:
        message = f"Top 5 {category} bargains in Vienna:\n\n" + "\n\n".join(listings)
    else:
        message = f"No listings found or error fetching {category}."

    update.message.reply_text(message)
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, category_selected)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    dp.add_handler(conv_handler)

    # Send welcome message on start
    send_telegram_message("Vienna Bargain Bot started! Use /start in Telegram to begin.")

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    run_bot()
