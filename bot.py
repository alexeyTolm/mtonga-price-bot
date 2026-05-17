import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/pairs/ton/eqdo_vblig0b_yr7kwcb0wyxzlzcnmd7rw3jtqmv01nx5g54"

DOLLAR_EMOJI_ID = "5195308461193182892"
TON_EMOJI_ID = "5188672371648634636"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def tg_len(text):
    return len(text.encode("utf-16-le")) // 2


def get_mtonga_price():
    try:
        r = requests.get(DEXSCREENER_API_URL, timeout=15)
        r.raise_for_status()
        pair = r.json().get("pair")

        if not pair:
            return None

        return {
            "price_usd": float(pair.get("priceUsd", 0)),
            "price_ton": float(pair.get("priceNative", 0)),
            "fdv": float(pair.get("fdv", 0)),
        }

    except Exception as e:
        logging.error(f"Ошибка получения цены: {e}")
        return None


def format_message(data):
    price_usd = f"{data['price_usd']:.4f}"
    price_ton = f"{data['price_ton']:.6f}"
    mc = f"{data['fdv'] / 1_000_000:.1f}kk"

    text = ""
    entities = []

    text += f"${price_usd} "

    dollar_offset = tg_len(text)
    text += "$"

    entities.append({
        "offset": dollar_offset,
        "length": tg_len("$"),
        "type": "custom_emoji",
        "custom_emoji_id": DOLLAR_EMOJI_ID
    })

    text += "\n"
    text += f"{price_ton} "

    ton_offset = tg_len(text)
    text += "TON"

    entities.append({
        "offset": ton_offset,
        "length": tg_len("TON"),
        "type": "custom_emoji",
        "custom_emoji_id": TON_EMOJI_ID
    })

    text += f"\n\nMC: ${mc}"

    return text, entities


def check_custom_emoji_ids():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getCustomEmojiStickers"

    payload = {
        "custom_emoji_ids": [
            DOLLAR_EMOJI_ID,
            TON_EMOJI_ID
        ]
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        logging.info(f"Проверка emoji IDs: {r.text}")
    except Exception as e:
        logging.error(f"Ошибка проверки emoji IDs: {e}")


def send_telegram_message(text, entities):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "entities": entities,
        "disable_web_page_preview": True
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        logging.info("Сообщение отправлено")

    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        try:
            logging.error(r.text)
        except Exception:
            pass


if __name__ == "__main__":
    logging.info("Бот запущен")

    check_custom_emoji_ids()

    while True:
        data = get_mtonga_price()

        if data:
            text, entities = format_message(data)
            send_telegram_message(text, entities)

        time.sleep(60)