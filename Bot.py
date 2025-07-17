import telebot
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

# Твої хендлери тут...

if __name__ == "__main__":
    print("Видаляємо webhook...")
    bot.remove_webhook()  # Гарантовано видаляємо webhook
    print("Запускаємо polling...")
    bot.polling(none_stop=True)
