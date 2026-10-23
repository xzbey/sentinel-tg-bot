from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from tg.main_handlers import ask_radius, ask_date
from tg.tg_constants import RADIUS, DATE, END
from tg.texts import START_TEXT, GUIDE_TEXT

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text=START_TEXT,
                                    parse_mode=ParseMode.HTML)
    return END

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text=GUIDE_TEXT,
                                    parse_mode=ParseMode.HTML, 
                                    reply_markup=ReplyKeyboardRemove())

    state = context.user_data.get('state', END)

    if state == RADIUS:
        await ask_radius(update, context, repeat=True)
    
    elif state == DATE:
        await ask_date(update, context)
    
    else:
        await update.message.reply_text("Введите локацию для поиска:")
