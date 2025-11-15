import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"


@app.get("/")
def index():
    return "OK", 200


@app.post(f"/webhook/{'' if TOKEN is None else TOKEN}")
def webhook():
    data = request.get_json(silent=True) or {}
    message = data.get("message") or data.get("edited_message")
    if not message:
        return "OK", 200

    chat_id = message["chat"]["id"]

    text = (
        "Я сейчас не у компьютера 🌙\n"
        "Как только буду в сети – отвечу 🙂"
    )

    try:
        requests.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5,
        )
    except Exception as e:
        print("sendMessage error:", e)

    return "OK", 200
