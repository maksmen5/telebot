# webhook_server.py
from flask import Flask, request, jsonify
import hmac
import base64
import hashlib
import telebot

from config import MERCHANT_SECRET_KEY, BOT_TOKEN, CHANNELS

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)


def validate_signature(data, signature):
    keys = [
        "merchantAccount", "orderReference", "amount", "currency",
        "authCode", "cardPan", "transactionStatus", "reasonCode"
    ]
    sign_str = ";".join(str(data.get(k, "")) for k in keys)
    calc_sign = base64.b64encode(hmac.new(
        MERCHANT_SECRET_KEY.encode(), sign_str.encode(), digestmod="md5"
    ).digest()).decode()
    return calc_sign == signature


@app.route("/wayforpay_callback", methods=["POST"])
def callback():
    data = request.json
    signature = data.get("signature", "")

    if data.get("transactionStatus") == "Approved" and validate_signature(data, signature):
        user_id = int(data.get("clientAccountId"))
        order_ref = data.get("orderReference")
        course_id = order_ref.split("_")[-1]

        try:
            chat_id = CHANNELS.get(course_id)
            if not chat_id:
                bot.send_message(user_id, "❌ Не знайдено курс.")
                return jsonify({"code": "accept"})

            invite = bot.create_chat_invite_link(
                chat_id=chat_id,
                member_limit=1,
                creates_join_request=False
            )
            bot.send_message(user_id, f"✅ Оплату підтверджено!\n🔗 Ось твоє посилання: {invite.invite_link}")
        except Exception as e:
            bot.send_message(user_id, f"❌ Помилка при доступі:\n{e}")
        return jsonify({"code": "accept"})

    return jsonify({"code": "reject"})


@app.route("/", methods=["GET"])
def home():
    return "Сервер працює!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
