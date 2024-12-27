from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
import requests
import os
from aliexpress_api import AliexpressApi

# Configuration
TOKEN = "7796931705:AAEXK6Grrh4LttcUBs2bOLGGLeNtQbwCvgk"  #  Token  بوت  تيليجرام
ALIEXPRESS_APP_KEY = os.getenv('ALIEXPRESS_APP_KEY')  #  App Key  من  AliExpress
ALIEXPRESS_APP_SECRET = os.getenv('ALIEXPRESS_APP_SECRET')  #  App Secret  من  AliExpress
BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price?symbol=USDTDZD"
COMMISSIONS = [(0, 10, 1.5), (10, 50, 1.3), (50, 100, 1.2), (100, float('inf'), 1.1)]

#  تهيئة  AliExpress API
aliexpress = AliexpressApi(key=ALIEXPRESS_APP_KEY, secret=ALIEXPRESS_APP_SECRET)

# Helper Functions
def fetch_aliexpress_product(url):
    try:
        product_id = aliexpress.get_product_id(url)
        product_data = aliexpress.get_product_details(product_id)
        print(f"Product data: {product_data}")  #  لطباعة  product_data  في  logs
        return product_data
    except Exception as e:
        print(f"Error fetching product details: {e}")
        return None

def fetch_usdt_dzd_rate():
    response = requests.get(BINANCE_API_URL)
    if response.status_code == 200:
        return float(response.json().get("price", 0))
    else:
        print(f"Error fetching exchange rate: {response.status_code}")
        return None

def calculate_commission(price_usd):
    for lower, upper, multiplier in COMMISSIONS:
        if lower <= price_usd < upper:
            return price_usd * multiplier
    return price_usd

def calculate_total_price(price_usd, shipping_cost_usd, exchange_rate):
    price_dzd = (price_usd + shipping_cost_usd) * exchange_rate
    final_price_dzd = calculate_commission(price_dzd)
    return final_price_dzd

# Bot Handlers
def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحباً بك في بوت منتجات AliExpress! أرسل لي رابط المنتج للبدء.")

def handle_product_link(update: Update, context: CallbackContext):
    user_message = update.message.text

    if "aliexpress.com" not in user_message:
        update.message.reply_text("يرجى إرسال رابط منتج AliExpress صحيح.")
        return

    update.message.reply_text("جاري جلب تفاصيل المنتج، يرجى الانتظار...")

    product_data = fetch_aliexpress_product(user_message)
    exchange_rate = fetch_usdt_dzd_rate()

    if not product_data or not exchange_rate:
        update.message.reply_text("عذرًا، تعذر جلب تفاصيل المنتج أو سعر الصرف.")
        return

    product_title = product_data.get("title", "عنوان غير معروف")
    product_price_usd = float(product_data.get("price", 0))
    shipping_cost_usd = float(product_data.get("shipping_cost", 0))

    total_price_dzd = calculate_total_price(product_price_usd, shipping_cost_usd, exchange_rate)

    keyboard = [[InlineKeyboardButton("تأكيد الطلب", callback_data="confirm_order")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (f"المنتج: {product_title}\n"
               f"السعر: ${product_price_usd}\n"
               f"تكلفة الشحن: ${shipping_cost_usd}\n"
               f"السعر الإجمالي بالدينار الجزائري: {total_price_dzd:.2f}\n")

    update.message.reply_text(message, reply_markup=reply_markup)

def confirm_order(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("تم تأكيد طلبك. سيقوم المسؤول بمعالجته قريبًا.")

# Main Function
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_product_link))
    dp.add_handler(CallbackQueryHandler(confirm_order, pattern="confirm_order"))

    #  استخدام  Webhook
    updater.start_webhook(listen="0.0.0.0",
                          port=int(os.environ.get('PORT', 8443)),
                          url_path=TOKEN,
                          webhook_url='https://aliexpress-bot-ab11.onrender.com' + TOKEN)
    updater.idle()

if __name__ == "__main__":
    main()
