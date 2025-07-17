from telebot import TeleBot
from config import BOT_TOKEN

bot = TeleBot(BOT_TOKEN)
bot.remove_webhook()
bot.set_webhook(url="https://telebot-zydo.onrender.com/<токен>/")
print("Webhook встановлено.")
