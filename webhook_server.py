from flask import Flask, request, jsonify, abort
import telebot
import os

BOT_TOKEN = os.environ['BOT_TOKEN']
bot = telebot.TeleBot(BOT_TOKEN)

from config import CHANNELS

app = Flask(__name__)

# --- Функція видачі посилання ---
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

# --- Ендпоінт для Telegram webhook ---
WEBHOOK_URL_BASE = os.environ.get('WEBHOOK_URL_BASE')
WEBHOOK_URL_PATH = f"/webhook/{BOT_TOKEN}"

@app.route(WEBHOOK_URL_PATH, methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    else:
        abort(403)

@app.route("/", methods=["GET"])
def home():
    return "Сервер працює!"

# --- Обробка callback від кнопки "Я оплатив" ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_payment"))
def confirm_payment_callback(call):
    cid = call.data.split(":")[1]
    user = call.from_user
    chat_id = call.message.chat.id

    # Тут можна повідомити адміна або просто видати посилання відразу:
    handle_successful_payment(user.id, cid)
    bot.answer_callback_query(call.id, "Доступ видано. Перевір пошту повідомлення.")

if __name__ == "__main__":
    bot.remove_webhook()
    webhook_url = WEBHOOK_URL_BASE + WEBHOOK_URL_PATH
    if bot.set_webhook(url=webhook_url):
        print(f"Webhook встановлено: {webhook_url}")
    else:
        print("Не вдалося встановити webhook")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
