from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from tg.main_handlers import ask_radius, ask_date
from tg.tg_constants import RADIUS, DATE, END, COMPOSITE
from tg.texts import START_TEXT, GUIDE_TEXT, INDICES_TEXT, COMPOSITES_TEXT, CLASS_TEXT, VECTOR_TEXT

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

    elif state == COMPOSITE:
        await update.message.reply_text("Введите каналы через пробелм, например, B04 B03 B02:",
                                        reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True))
    
    else:
        await update.message.reply_text("Введите локацию для поиска:")

def make_help(text: str):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(text=text, parse_mode=ParseMode.HTML)
    return handler

indices_help = make_help(INDICES_TEXT)
composites_help = make_help(COMPOSITES_TEXT)
class_help = make_help(CLASS_TEXT)
vector_help = make_help(VECTOR_TEXT)