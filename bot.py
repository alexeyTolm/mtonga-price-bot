import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/pairs/ton/eqdo_vblig0b_yr7kwcb0wyxzlzcnmd7rw3jtqmv01nx5g54"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_mtonga_price():
    try:
        r = requests.get(DEXSCREENER_API_URL, timeout=15)
        r.raise_for_status()
        data = r.json()
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


def format_number(num):
    """Форматирует число с разделителями тысяч"""
    return f"{num:,.0f}".replace(",", " ")


def format_message(data):
    price_usd = data['price_usd']
    price_ton = data['price_ton']
    mc = data['fdv']
    
    # Форматируем цену в USD (4 знака после запятой)
    price_usd_str = f"{price_usd:.4f}"
    
    # Форматируем цену в TON (6 знаков после запятой)
    price_ton_str = f"{price_ton:.6f}"
    
    # Форматируем MC с разделителями тысяч
    mc_str = format_number(mc)
    
    # Собираем сообщение в нужном формате
    text = f"${price_usd_str} | {price_ton_str} TON\nMC: ${mc_str}"
    
    return text


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        logging.info("Сообщение отправлено")
        logging.info(f"Текст: {text}")
        
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        if 'r' in locals():
            logging.error(f"Ответ: {r.text}")


if __name__ == "__main__":
    logging.info("Бот запущен")
    
    while True:
        data = get_mtonga_price()
        
        if data:
            text = format_message(data)
            send_telegram_message(text)
        else:
            logging.warning("Не удалось получить данные о цене")
        
        time.sleep(60)