"""
ربات تلگرام گزارش قیمت دلار
----------------------------
این اسکریپت هر ۲ ساعت یک‌بار قیمت لحظه‌ای دلار (تومان) رو از منبع آنلاین می‌گیره
و به یه چت/گروه/کانال تلگرام می‌فرسته.

راه‌اندازی:
1. pip install -r requirements.txt
2. مقادیر BOT_TOKEN و CHAT_ID رو پایین‌تر پر کن
3. python usd_price_bot.py
   (برای اجرای دائمی روی سرور، بهتره با systemd یا screen/tmux یا pm2 اجراش کنی)
"""

import time
import requests
from datetime import datetime

# ============ تنظیمات - این دو تا رو حتماً پر کن ============
BOT_TOKEN = "8284493768:AAGJ2-aRW_wwyjrR3ni4aeMND1rMMT896Oo"      # از @BotFather می‌گیری
CHAT_ID = "@arstala"          # آیدی چت/کانال/گروه (می‌تونه با @ هم شروع بشه اگه کانال پابلیکه)
INTERVAL_SECONDS = 2 * 60 * 60         # هر ۲ ساعت
# ================================================================

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def get_usd_price():
    """
    قیمت دلار رو از tgju.org (منبع عمومی و بدون نیاز به API key) می‌گیره.
    خروجی به تومان برمی‌گردونه.
    """
    url = "https://call4.tgju.org/ajax.json"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    usd_data = data["current"]["price_dollar_rl"]
    price_rial = int(usd_data["p"].replace(",", ""))
    price_toman = price_rial // 10

    change = usd_data.get("dt", "")  # جهت تغییر: high / low / unchanged
    if change == "high":
        arrow = "🔺"
    elif change == "low":
        arrow = "🔻"
    else:
        arrow = "➖"

    return price_toman, arrow


def send_to_telegram(text):
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    resp = requests.post(TELEGRAM_API, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def build_message(price, arrow):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"💵 <b>قیمت دلار</b>\n"
        f"{price:,} تومان {arrow}\n\n"
        f"🕒 {now}"
    )


def run_once():
    try:
        price, arrow = get_usd_price()
        message = build_message(price, arrow)
        send_to_telegram(message)
        print(f"[OK] پیام ارسال شد: {price:,} تومان")
    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    print("ربات قیمت دلار شروع به کار کرد. هر ۲ ساعت یک‌بار آپدیت می‌فرسته...")
    while True:
        run_once()
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
