from dotenv import load_dotenv
load_dotenv()

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

from tg.commands import start, guide
from tg.handlers import ask_radius, get_radius, get_date, get_file_data, RADIUS, DATE, index_btn

from core.config import token

# import logging
# logging.basicConfig(level=logging.INFO)
# logging.getLogger("httpx").setLevel(logging.WARNING)

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
        RADIUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_radius), MessageHandler(filters.Document.ALL, get_file_data)],
        DATE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date), MessageHandler(filters.Document.ALL, get_file_data)],
    },
    fallbacks=[
        CommandHandler("start", start),
    ],
)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("guide", guide))
application.add_handler(CallbackQueryHandler(index_btn, pattern="i:"))
application.add_handler(conv_handler)

application.run_polling()