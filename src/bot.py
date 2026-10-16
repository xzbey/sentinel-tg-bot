from dotenv import load_dotenv
load_dotenv()

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler

from tg.commands import start, guide
from tg.handlers import ask_radius, get_radius, get_date, get_file_data, RADIUS, DATE

from core.config import token

application = (
    ApplicationBuilder()
    .token(token())
    .read_timeout(120)
    .write_timeout(120)
    .connect_timeout(30)
    .build()
)

conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, ask_radius),
                  MessageHandler(filters.Document.ALL, get_file_data)],
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