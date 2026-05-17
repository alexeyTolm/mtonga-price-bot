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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_mtonga_price():
    try:
        response = requests.get(DEXSCREENER_API_URL, timeout=15)
        response.raise_for_status()

        data = response.json()
        pair = data.get("pair")

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
    text = (
        f"${data['price_usd']:.4f} $\n"
        f"{data['price_ton']:.6f} T\n\n"
        f"MC: ${data['fdv'] / 1_000_000:.1f}kk"
    )

    dollar_offset = len(f"${data['price_usd']:.4f} ")

    ton_offset = len(
        f"${data['price_usd']:.4f} $\n"
        f"{data['price_ton']:.6f} "
    )

    entities = [
        {
            "offset": dollar_offset,
            "length": 1,
            "type": "custom_emoji",
            "custom_emoji_id": DOLLAR_EMOJI_ID
        },
        {
            "offset": ton_offset,
            "length": 1,
            "type": "custom_emoji",
            "custom_emoji_id": TON_EMOJI_ID
        }
    ]

    return text, entities


def send_telegram_message(text, entities=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "entities": entities or [],
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=10
        )

        response.raise_for_status()

        logging.info("Сообщение отправлено")

    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

        try:
            logging.error(response.text)
        except:
            pass


if __name__ == "__main__":
    logging.info("Бот запущен")

    while True:
        data = get_mtonga_price()

        if data:
            text, entities = format_message(data)
            send_telegram_message(text, entities)

        time.sleep(60)