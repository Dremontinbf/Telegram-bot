import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# секрет для выдачи очереди (должен совпадать с PENDING_SECRET на компе)
PENDING_SECRET = os.getenv("PENDING_SECRET", "").strip()

# тут храним всех, кто писал, пока комп выключен
pending_chat_ids = set()


@app.route("/", methods=["GET"])
def index():
    return "OK", 200


@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    message = data.get("message") or data.get("edited_message")
    if not message:
        return "ok", 200

    chat_id = message["chat"]["id"]

    # кладём человека в очередь "ждущих", чтобы локальный бот потом всем написал
    pending_chat_ids.add(chat_id)

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

    return "ok", 200


@app.route("/pending/<secret>", methods=["GET"])
def pending(secret):
    """
    Локальный бот при запуске дергает /pending/<PENDING_SECRET>.
    Возвращаем список chat_id, кто писал, пока работал автоответчик,
    и очищаем очередь.
    """
    if not PENDING_SECRET or secret != PENDING_SECRET:
        return {"error": "forbidden"}, 403

    global pending_chat_ids
    ids = list(pending_chat_ids)
    pending_chat_ids = set()

    # вернём обычный JSON-массив, типа [123, 456, 789]
    return jsonify(ids), 200


if __name__ == "__main__":
    # локальный запуск, на Render всё равно запустит gunicorn
    app.run(host="0.0.0.0", port=10000)
