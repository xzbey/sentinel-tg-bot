from dotenv import load_dotenv
load_dotenv()

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

from tg.commands import start, guide
from tg.tg_constants import DATE, RADIUS, COMPOSITE
from tg.main_handlers import ask_radius, get_radius, get_date, get_file_data
from tg.composites_handlers import ask_composite, get_composite, composite_btn
from tg.indices_handlers import indices_btn

from core.config import token

import warnings
from telegram.warnings import PTBUserWarning

warnings.filterwarnings("ignore", message=".*per_message.*", category=PTBUserWarning)

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
                  MessageHandler(filters.Document.ALL, get_file_data),
                  CallbackQueryHandler(ask_composite, pattern="custom:composite")],
    states={
        RADIUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_radius), MessageHandler(filters.Document.ALL, get_file_data)],
        DATE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date), MessageHandler(filters.Document.ALL, get_file_data)],
        COMPOSITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_composite)]
    },
    fallbacks=[
        CommandHandler("start", start),
    ],
)

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("guide", guide))
application.add_handler(CallbackQueryHandler(indices_btn, pattern="i:"))
application.add_handler(CallbackQueryHandler(composite_btn, pattern="composite:"))
application.add_handler(conv_handler)

application.run_polling()