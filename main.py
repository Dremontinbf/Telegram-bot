import os
import json
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Токен берём из переменной среды на Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Секретный хвост для доступа к списку ожидающих
# Его зададим в Environment на Render как PENDING_SECRET
SECRET = os.environ.get("PENDING_SECRET", "change_me")

# Файл, где на Render будем хранить chat_id тех, кто писал,
# пока ты был офлайн
PENDING_FILE = "pending.json"
PENDING_LOCK = threading.Lock()


def load_pending() -> set:
    """Загрузка множества chat_id из файла."""
    if not os.path.exists(PENDING_FILE):
        return set()
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data)
    except Exception as e:
        print("load_pending error:", e)
        return set()


def save_pending(pending: set) -> None:
    """Сохранение множества chat_id в файл."""
    try:
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(list(pending), f, ensure_ascii=False)
    except Exception as e:
        print("save_pending error:", e)


@app.get("/")
def index():
    return "OK", 200


# Основной вебхук от Telegram
@app.post(f"/webhook/{'' if TOKEN is None else TOKEN}")
def webhook():
    data = request.get_json(silent=True) or {}
    message = data.get("message") or data.get("edited_message")
    if not message:
        return "OK", 200

    chat_id = message["chat"]["id"]

    # 1. Запоминаем этого пользователя как "писал, пока я офлайн"
    try:
        with PENDING_LOCK:
            pending = load_pending()
            pending.add(chat_id)
            save_pending(pending)
    except Exception as e:
        print("pending store error:", e)

    # 2. Шлём автоответ
    text = (
        "Я сейчас не у компьютера 🌙\n"
        "Как только буду в сети – посмотрю сообщения.\n"
        "Позже напишу, когда можно будет отправлять фото 🙂"
    )

    try:
        requests.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception as e:
        print("sendMessage error:", e)

    return "OK", 200


# Сервисный эндпоинт для твоего локального бота:
# он придёт сюда при включении ПК, заберёт список chat_id
# и мы тут же этот список очистим.
@app.get("/pending/<secret>")
def get_pending(secret):
    if secret != SECRET:
        return "forbidden", 403

    with PENDING_LOCK:
        pending = load_pending()
        # очищаем, чтобы при следующем запуске не слать повторно
        save_pending(set())

    # Возвращаем список ID, чтобы локальный бот всем разослал "я снова онлайн"
    return jsonify(sorted(list(pending))), 200
