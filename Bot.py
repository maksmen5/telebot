import telebot
from telebot import types
from config import BOT_TOKEN, CHANNELS, COURSES

bot = telebot.TeleBot(BOT_TOKEN)

# 👉 Заміни на свій Telegram ID (admin)
ADMIN_ID = 123456789

# Стан користувача
user_state = {}

# Головне меню
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(course['name']) for course in COURSES.values()]
    markup.add(*buttons)
    bot.send_message(chat_id, "👋 Обери курс:", reply_markup=markup)

# Меню курсу
def show_course_menu(chat_id, course_id):
    course = COURSES[course_id]
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("ℹ️ Інформація"),
        types.KeyboardButton("💳 Купити"),
        types.KeyboardButton("⬅️ Назад")
    )
    bot.send_message(chat_id, f"📘 {course['name']}", reply_markup=markup)

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

        if text == "ℹ️ Інформація":
            course = COURSES[cid]
            bot.send_message(chat_id, f"*{course['name']}*\n\n{course['description']}", parse_mode="Markdown")

        elif text == "💳 Купити":
            course = COURSES[cid]
            if course['price'] == 0:
                handle_successful_payment(chat_id, cid)
                return

            # Повідомлення адміну
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton(
                text=f"✅ Підтвердити оплату для ID {chat_id}",
                callback_data=f"confirm:{chat_id}:{cid}"
            )
            markup.add(btn)

            bot.send_message(chat_id, "🔄 Зачекай, твій запит на оплату надіслано адміну.")
            bot.send_message(
                ADMIN_ID,
                f"🧾 Запит на оплату від @{message.from_user.username or message.from_user.first_name}\n"
                f"💬 Курс: {course['name']}\n"
                f"🆔 ID: {chat_id}",
                reply_markup=markup
            )

        elif text == "⬅️ Назад":
            user_state.pop(chat_id, None)
            show_main_menu(chat_id)

        else:
            bot.send_message(chat_id, "❗️ Обери кнопку з меню.")

    else:
        bot.send_message(chat_id, "❗️ Обери курс з меню.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm:"))
def handle_confirm(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Ви не адміністратор.")
        return

    try:
        _, user_id, course_id = call.data.split(":")
        user_id = int(user_id)
        handle_successful_payment(user_id, course_id)
        bot.answer_callback_query(call.id, "✅ Підтверджено.")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Помилка.")
        print(f"[ERROR] confirm: {e}")

def handle_successful_payment(user_id, course_id):
    try:
        chat_id = CHANNELS.get(course_id)
        if not chat_id:
            bot.send_message(user_id, "❌ Канал не знайдено.")
            return
        invite = bot.create_chat_invite_link(
            chat_id=chat_id,
            member_limit=1,
            creates_join_request=False
        )
        bot.send_message(user_id, f"✅ Оплату підтверджено!\n🔗 Ось твоє посилання:\n{invite.invite_link}")
    except Exception as e:
        bot.send_message(user_id, f"❌ Помилка:\n{e}")
        print(f"[ERROR] handle_successful_payment: {e}")

bot.polling(none_stop=True)
