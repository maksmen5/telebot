import telebot
from flask import Flask, request
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Бот активний!"

@app.route("/", methods=["POST"])
def receive_update():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "ok", 200
    return "not supported", 403

# Приклад обробника команди
@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(message.chat.id, "Привіт! Це бот з webhook.")

# Не запускай bot.polling()!
if __name__ == "__main__":
    app.run(debug=True)
