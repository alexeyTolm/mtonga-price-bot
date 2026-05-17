import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/pairs/ton/eqdo_vblig0b_yr7kwcb0wyxzlzcnmd7rw3jtqmv01nx5g54"

# Ваши ID кастомных эмодзи
DOLLAR_EMOJI_ID = "5195308461193182892"
TON_EMOJI_ID = "5188672371648634636"

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
    
    # Форматируем цены
    if price_usd < 0.01:
        price_usd_str = f"{price_usd:.6f}"
    else:
        price_usd_str = f"{price_usd:.4f}"
    
    if price_ton < 0.0001:
        price_ton_str = f"{price_ton:.8f}"
    else:
        price_ton_str = f"{price_ton:.6f}"
    
    mc_str = format_number(mc)
    
    # Создаем кастомные эмодзи через HTML-разметку
    # Внутри тега указываем обычный эмодзи как заглушку
    dollar_emoji = f'<a href="tg://emoji?id={DOLLAR_EMOJI_ID}">💵</a>'
    ton_emoji = f'<a href="tg://emoji?id={TON_EMOJI_ID}">💎</a>'
    
    # Собираем сообщение в нужном формате
    text = f"{dollar_emoji} {price_usd_str} | {price_ton_str} {ton_emoji}\nMC: ${mc_str}"
    
    return text


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",  # Обязательно для кастомных эмодзи
        "disable_web_page_preview": True
    }
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        logging.info("✅ Сообщение отправлено")
        logging.info(f"Текст: {text}")
        
    except Exception as e:
        logging.error(f"❌ Ошибка отправки: {e}")
        if 'r' in locals():
            logging.error(f"Ответ: {r.text}")


def check_bot_permissions():
    """Проверяет, может ли бот отправлять кастомные эмодзи"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    try:
        r = requests.get(url, timeout=10)
        bot_info = r.json()
        
        if bot_info.get("ok"):
            bot = bot_info.get("result", {})
            username = bot.get("username")
            is_premium = bot.get("is_premium", False)
            
            logging.info(f"🤖 Бот: @{username}")
            logging.info(f"💎 Премиум статус: {is_premium}")
            
            if not is_premium:
                logging.warning("⚠️ Бот не имеет премиум статуса. Кастомные эмодзи могут не работать!")
                logging.warning("Для отправки кастомных эмодзи боту нужен Telegram Business или купленный юзернейм")
        else:
            logging.error("Не удалось получить информацию о боте")
            
    except Exception as e:
        logging.error(f"Ошибка проверки прав бота: {e}")


if __name__ == "__main__":
    logging.info("🚀 Бот запущен")
    
    # Проверяем права бота
    check_bot_permissions()
    
    # Отправляем тестовое сообщение при старте
    test_data = {
        "price_usd": 0.0152,
        "price_ton": 0.007948,
        "fdv": 1519694
    }
    test_text = format_message(test_data)
    logging.info(f"📝 Тестовое сообщение: {test_text}")
    send_telegram_message(test_text)
    
    # Основной цикл
    while True:
        try:
            data = get_mtonga_price()
            
            if data:
                text = format_message(data)
                send_telegram_message(text)
            else:
                logging.warning("⚠️ Не удалось получить данные о цене")
            
            time.sleep(60)
            
        except KeyboardInterrupt:
            logging.info("🛑 Бот остановлен пользователем")
            break
        except Exception as e:
            logging.error(f"❌ Непредвиденная ошибка: {e}")
            time.sleep(60)