import os
import requests
import telebot
import warnings
import time
import hashlib
import hmac  # Import the hmac module
from dotenv import load_dotenv

# Suppress SSL verification warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

load_dotenv()

bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello, I am a bot that can get you product information from AliExpress. Send me a product link.")

@bot.message_handler(func=lambda message: True)
def handle_product_link(message):
    product_link = message.text
    app_key = os.getenv('ALIEXPRESS_APP_KEY')
    app_secret = os.getenv('ALIEXPRESS_APP_SECRET')

    if not all([app_key, app_secret]):
        bot.reply_to(message, "API credentials are not properly configured.")
        return

    try:
        # Extract product ID from AliExpress link
        if "item/" in product_link:
            product_id = product_link.split("item/")[1].split(".")[0]
        else:
            product_id = product_link

        # Construct the API request URL with proper endpoint
        api_url = "https://eco.taobao.com/router/rest"

        timestamp = str(int(time.time() * 1000))
        params = {
            'method': 'aliexpress.affiliate.productdetail.get',
            'app_key': app_key,
            'timestamp': timestamp,
            'format': 'json',
            'v': '2.0',
            'sign_method': 'hmac',
            'product_ids': product_id,
            'target_currency': 'USD',
            'target_language': 'EN'
        }

        # Generate signature
        sorted_params = sorted(params.items())
        base_string = ''.join(f"{k}{v}" for k, v in sorted_params)
        sign = hmac.new(app_secret.encode(), base_string.encode(), hashlib.sha256).hexdigest().upper()  # Use hmac.new
        params['sign'] = sign

        # Make the API request
        response = requests.get(api_url, params=params, verify=False)
    except Exception as e:
        bot.reply_to(message, f"Error processing the link: {str(e)}")
        return

    try:
        # Handle the response
        if response.status_code == 200:
            try:
                print("API Response:", response.text)  # Debug log
                data = response.json()
                if 'errorCode' in data:
                    bot.reply_to(message, f"API Error: {data.get('errorMessage', 'Unknown error')}")
                    return

                product_info = data.get('productInfo', {})
                product_name = product_info.get('title', 'N/A')
                product_price = product_info.get('salePrice', 'N/A')
                bot.reply_to(message, f"Product Name: {product_name}\nPrice: ${product_price}")
            except ValueError as e:
                bot.reply_to(message, f"Invalid API response format. Response: {response.text[:100]}")
        else:
            bot.reply_to(message, f"API request failed with status code: {response.status_code}")
    except Exception as e:
        bot.reply_to(message, f"An error occurred while fetching the product information: {str(e)}")

if __name__ == "__main__":
    print("Bot started...")
    bot.polling()