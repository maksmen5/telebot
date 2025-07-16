import telebot
from telebot import types
import hmac
import hashlib
import base64
from urllib.parse import urlencode
import time
import os
from flask import Flask, request

# Читаємо ключі з Environment Variables
BOT_TOKEN = os.environ['BOT_TOKEN']
MERCHANT_ACCOUNT = os.environ['MERCHANT_ACCOUNT']
MERCHANT_SECRET_KEY = os.environ['MERCHANT_SECRET_KEY']

# У config.py залиш тільки COURSES і CHANNELS або перенеси їх сюди
from config import COURSES, CHANNELS

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Головна сторінка (для перевірки Render)
@app.route('/')
def home():
    return 'Bot is running!'

# Webhook для отримання апдейтів від Telegram
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

# Після оплати
def handle_successful_payment(user_id, course_id):
    try:
        chat_id = CHANNELS.get(course_id)
        if not chat_id:
            bot.send_message(user_id, "❌ Канал не знайдено для цього курсу.")
            return
        invite = bot.create_chat_invite_link(
            chat_id=chat_id,
            member_limit=1,
            creates_join_request=False
        )
        bot.send_message(user_id, f"✅ Оплату підтверджено!\n🔗 Ось твоє посилання:\n{invite.invite_link}")
    except Exception as e:
        bot.send_message(user_id, f"❌ Помилка видачі доступу:\n{e}")
        print(f"[ERROR] handle_successful_payment: {e}")

# Меню курсу
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(course['name']) for course in COURSES.values()]
    markup.add(*buttons)
    bot.send_message(chat_id, "👋 Обери курс:", reply_markup=markup)

def show_course_menu(chat_id, course_id):
    course = COURSES[course_id]
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("ℹ️ Інформація"),
        types.KeyboardButton("💳 Купити"),
        types.KeyboardButton("⬅️ Назад")
    )
    bot.send_message(chat_id, f"📘 {course['name']}", reply_markup=markup)

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_state.pop(message.chat.id, None)
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    for cid, course in COURSES.items():
        if text == course['name']:
            user_state[chat_id] = cid
            show_course_menu(chat_id, cid)
            return

    if chat_id in user_state:
        cid = user_state[chat_id]
        course = COURSES[cid]

        if text == "ℹ️ Інформація":
            bot.send_message(chat_id, f"*{course['name']}*\n\n{course['description']}", parse_mode="Markdown")

        elif text == "💳 Купити":
            if course['price'] == 0:
                handle_successful_payment(chat_id, cid)
                return

            order_ref = f"order_{chat_id}_{cid}"
            order_date = str(int(time.time()))
            data = {
                "merchantAccount": MERCHANT_ACCOUNT,
                "merchantDomainName": "test.com",
                "orderReference": order_ref,
                "orderDate": int(order_date),
                "amount": course['price'],
                "currency": "UAH",
                "productName": [course['name']],
                "productCount": [1],
                "productPrice": [course['price']],
                "clientAccountId": str(chat_id),
                "returnUrl": "https://t.me/your_bot"
            }

            keys = [
                MERCHANT_ACCOUNT, "test.com", order_ref, order_date,
                str(course['price']), "UAH", course['name'], "1", str(course['price'])
            ]
            sign_str = ";".join(keys)
            sign = base64.b64encode(
                hmac.new(MERCHANT_SECRET_KEY.encode(), sign_str.encode(), hashlib.md5).digest()
            ).decode()
            data['merchantSignature'] = sign

            pay_link = "https://secure.wayforpay.com/pay?" + urlencode(data, doseq=True)

            bot.send_message(chat_id,
                f"💳 Щоб купити {course['name']}, сплати {course['price']} грн:\n{pay_link}\n\nПісля оплати бот видасть доступ.")

        elif text == "⬅️ Назад":
            user_state.pop(chat_id, None)
            show_main_menu(chat_id)
        else:
            bot.send_message(chat_id, "❗️ Оберіть кнопку з меню внизу.")
    else:
        bot.send_message(chat_id, "❗️ Оберіть курс з меню.")

if __name__ == '__main__':
    # Встановлюємо webhook для Telegram
    bot.remove_webhook()
    bot.set_webhook(url='https://telebot-zydo.onrender.com/' + BOT_TOKEN)

    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
