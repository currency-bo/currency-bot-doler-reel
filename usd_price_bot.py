"""
ربات تلگرام گزارش قیمت ارزها
----------------------------
این اسکریپت هر ۲ ساعت یک‌بار قیمت لحظه‌ای دلار و چند ارز دیگه رو (تومان)
از منبع آنلاین می‌گیره و به یه چت/گروه/کانال تلگرام می‌فرسته.

راه‌اندازی:
1. pip install -r requirements.txt
2. مقادیر BOT_TOKEN و CHAT_ID رو به‌صورت Environment Variable ست کن
3. python usd_price_bot.py
   (برای اجرای دائمی روی سرور، بهتره با systemd یا screen/tmux یا pm2 اجراش کنی)
"""

import os
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# ============ تنظیمات - از Environment Variables خونده می‌شه ============
# روی Railway: بخش Variables پروژه رو باز کن و این دو تا رو اضافه کن:
#   BOT_TOKEN = توکنی که از BotFather گرفتی
#   CHAT_ID   = آیدی چت/کانال/گروه
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
INTERVAL_SECONDS = int(os.environ.get("INTERVAL_SECONDS", 2 * 60 * 60))  # پیش‌فرض: هر ۲ ساعت
# ================================================================

if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit(
        "خطا: BOT_TOKEN و CHAT_ID تنظیم نشدن. "
        "توی Railway از بخش Variables اضافه‌شون کن، یا موقع اجرای لوکال به‌صورت env var ست کن."
    )

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TEHRAN_TZ = ZoneInfo("Asia/Tehran")

# نگاشت ارزها: کلید داخلی tgju -> (نماد نمایشی, اسم فارسی)
# توجه: کلیدهای tgju ممکنه با گذشت زمان یا آپدیت سایت تغییر کنن.
# اگه یکی از ارزها خطا داد، توی لاگ مشخص می‌شه که کدوم کلید مشکل داره.
CURRENCIES = {
    "usd": {"tgju_key": "price_dollar_rl", "name": "دلار", "symbol": "USD"},
    "eur": {"tgju_key": "price_eur", "name": "یورو", "symbol": "EUR"},
    "aed": {"tgju_key": "price_aed", "name": "درهم امارات", "symbol": "AED"},
    "try": {"tgju_key": "price_try", "name": "لیر ترکیه", "symbol": "TRY"},
    "cny": {"tgju_key": "price_cny", "name": "یوان چین", "symbol": "CNY"},
    "kwd": {"tgju_key": "price_kwd", "name": "دینار کویت", "symbol": "KWD"},
}


def fetch_all_prices():
    """
    یه بار به tgju وصل می‌شه و همه‌ی ارزهای داخل CURRENCIES رو استخراج می‌کنه.
    خروجی: dict مثل {"usd": (price_toman, arrow), "eur": (price_toman, arrow), ...}
    ارزهایی که خطا بدن (کلید پیدا نشه و ...) توی نتیجه نمیان و توی لاگ چاپ می‌شن.
    """
    url = "https://call4.tgju.org/ajax.json"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    current = data.get("current", {})

    results = {}
    for code, info in CURRENCIES.items():
        tgju_key = info["tgju_key"]
        try:
            item = current[tgju_key]
            price_rial = int(str(item["p"]).replace(",", ""))
            price_toman = price_rial // 10

            change = item.get("dt", "")
            if change == "high":
                arrow = "🔺"
            elif change == "low":
                arrow = "🔻"
            else:
                arrow = "➖"

            results[code] = (price_toman, arrow)
        except (KeyError, ValueError, TypeError) as e:
            print(f"[WARN] نتونستم قیمت {info['name']} ({tgju_key}) رو بخونم: {e}")

    return results


def send_to_telegram(text):
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    resp = requests.post(TELEGRAM_API, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def build_message(prices):
    now = datetime.now(TEHRAN_TZ).strftime("%Y-%m-%d %H:%M")

    usd_line = ""
    if "usd" in prices:
        price, arrow = prices["usd"]
        usd_line = f"💵 قیمت دلار(USD): {price:,} تومان {arrow}\n"

    header = (
        f"{usd_line}"
        f"📊 قیمت لحظه‌ای ارزها\n"
        f"🕒 {now} (به وقت تهران)\n\n"
        f"💵ارز فیات :\n"
    )

    lines = []
    for code in ("eur", "aed", "try", "cny", "kwd"):
        info = CURRENCIES[code]
        if code in prices:
            price, arrow = prices[code]
            lines.append(f"{info['name']}({info['symbol']}): {price:,} تومان {arrow}")
        else:
            lines.append(f"{info['name']}({info['symbol']}): نامشخص")

    return header + "\n".join(lines)


def run_once():
    try:
        prices = fetch_all_prices()
        if not prices:
            print("[ERROR] هیچ قیمتی دریافت نشد.")
            return
        message = build_message(prices)
        send_to_telegram(message)
        print(f"[OK] پیام ارسال شد ({len(prices)} ارز).")
    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    print("ربات قیمت ارزها شروع به کار کرد. هر ۲ ساعت یک‌بار آپدیت می‌فرسته...")
    while True:
        run_once()
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
