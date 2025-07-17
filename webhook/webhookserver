import telebot

API_TOKEN = '8057736246:AAEFRcDq_2tM3Mm_KaN5jCZNKmkD0QrRJuk'
WEBHOOK_URL = 'https://telebot-zydo.onrender.com' + API_TOKEN

bot = telebot.TeleBot(API_TOKEN)

# Зняти попередній вебхук (необов’язково)
bot.remove_webhook()

# Встановити новий
bot.set_webhook(url=WEBHOOK_URL)

print("Webhook встановлено")
