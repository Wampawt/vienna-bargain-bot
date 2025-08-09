from flask import Flask, jsonify
import threading
import os
from vienna_bargain_bot import run_bot

app = Flask(__name__)

bot_thread = None

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "Vienna Bargain Bot is running."})

@app.route("/health")
def health():
    return "OK", 200

def start_background_bot():
    global bot_thread
    if bot_thread and bot_thread.is_alive():
        return
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

if __name__ == "__main__":
    start_background_bot()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
else:
    # When imported by Gunicorn, start background thread
    start_background_bot()
