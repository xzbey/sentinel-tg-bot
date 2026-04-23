from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler # pip install python-telegram-bot

from handlers import start, guide, ask_radius, get_radius, ask_date, get_date, do_search, RADIUS, DATE

from dotenv import load_dotenv # pip install python-dotenv
load_dotenv()

from config import token
import os

'''
from geo_search import search

def print_data(results):
    if results["success"]:
        print(f"Адрес: {results['data']['address']}\n" +
              f"Координаты: {results['data']['coords']}\n" +
              f"Метаданные снимка: {results['data']['metadata']}\n" +
              f"Разрешение: {results['data']['resolution']} м\n" +
              f"Размер: {results['data']['size']} пикселей")
        results['data']['image'].show()
    else:
        print(f"Ошибка: {results['error']}")



#print_data(search("42"))
# работает просто ввод текста

#print_data(search("55.699426, 38.357748", delta=0.05, 
#                  time_interval=("2025-6-1", "2025-8-31")))
# работает поиск по кордам + доп условия

#print_data(search("алешинские сады", 
#                  time_interval=("2025-06-01", "2025-08-31")))

print_data(search("алешинские сады", 10, ("2025-06-01", "2025-08-31")))

'''

application = (
    ApplicationBuilder()
    .token(token())
    .read_timeout(120)
    .write_timeout(120)
    .connect_timeout(30)
    .build()
)

conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, ask_radius)],
    states={
        RADIUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_radius)],
        DATE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
    },
    fallbacks=[
        CommandHandler("start", start),
    ],
)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("guide", guide))
application.add_handler(conv_handler)

application.run_polling()

# github.com/xzbey | tg/xzbey