import telebot
from telebot import types
import hmac
import hashlib
import base64
from urllib.parse import urlencode

from config import BOT_TOKEN, CHANNELS, COURSES

bot = telebot.TeleBot(BOT_TOKEN)

MERCHANT_ACCOUNT = "7de8a72b71369907282f75c00bb050e8"
MERCHANT_SECRET_KEY = "8600b023c86794b0496293e6b907aee895baa8e0"

# Функція для показу головного меню з кнопками курсів
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(course['name']) for course in COURSES.values()]
    markup.add(*buttons)
    bot.send_message(chat_id, "👋 Обери курс:", reply_markup=markup)

# Функція показу меню курсу з кнопками: Інформація, Купити, Назад
def show_course_menu(chat_id, course_id):
    course = COURSES[course_id]
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("ℹ️ Інформація"),
        types.KeyboardButton("💳 Купити"),
        types.KeyboardButton("⬅️ Назад")
    )
    bot.send_message(chat_id, f"📘 {course['name']}", reply_markup=markup)

# Збереження поточного вибраного курсу для кожного користувача (в пам'яті)
user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_state.pop(message.chat.id, None)  # Очистити стан
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    # Якщо користувач у головному меню обирає курс
    for cid, course in COURSES.items():
        if text == course['name']:
            user_state[chat_id] = cid
            show_course_menu(chat_id, cid)
            return

    # Якщо користувач в меню курсу
    if chat_id in user_state:
        cid = user_state[chat_id]

        if text == "ℹ️ Інформація":
            course = COURSES[cid]
            bot.send_message(chat_id, f"*{course['name']}*\n\n{course['description']}", parse_mode="Markdown")
        elif text == "💳 Купити":
            course = COURSES[cid]
            if course['price'] == 0:
                handle_successful_payment(chat_id, cid)
                return

            order_ref = f"order_{chat_id}_{cid}"
            data = {
                "merchantAccount": MERCHANT_ACCOUNT,
                "merchantDomainName": "test.com",
                "orderReference": order_ref,
                "orderDate": 1699999999,
                "amount": course['price'],
                "currency": "UAH",
                "productName": [course['name']],
                "productCount": [1],
                "productPrice": [course['price']],
                "clientAccountId": str(chat_id),
                "returnUrl": "https://t.me/your_bot"
            }

            keys = [
                MERCHANT_ACCOUNT, "test.com", order_ref, "1699999999",
                str(course['price']), "UAH", course['name'], "1", str(course['price'])
            ]
            sign_str = ";".join(keys)
            sign = base64.b64encode(hmac.new(MERCHANT_SECRET_KEY.encode(), sign_str.encode(), hashlib.md5).digest()).decode()
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

# Функція видачі посилання після оплати
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

bot.polling(none_stop=True)
