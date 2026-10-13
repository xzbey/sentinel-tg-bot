from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

import io
import html
import logging

from pipeline.pipeline import search
from core.error import SearchError

from datetime import datetime, date

logger = logging.getLogger(__name__)

RADIUS, DATE = range(2)
END = ConversationHandler.END

async def ask_radius(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_radius: bool = False):
    if not reply_radius:
        context.user_data['location'] = update.message.text
        context.user_data['state'] = RADIUS

    keyboard = [["📍 5 км - по умолчанию", "❌ Отмена"]]
    await update.message.reply_text(
        "Введите радиус поиска в км (0.1 - 50)",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return RADIUS


async def get_radius(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "❌ Отмена":
        context.user_data['state'] = END
        await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text("Введите локацию для поиска:")
        return END
    
    elif text == "📍 5 км - по умолчанию":
        context.user_data["radius"] = 0.05

    else:
        try:
            rad = float(text)
            if rad < 0.1 or rad > 50:
                return await ask_radius(update, context, reply_radius=True)
            context.user_data["radius"] = rad / 100

        except (ValueError, TypeError):
            return await ask_radius(update, context, reply_radius=True)
            

    return await ask_date(update, context)


async def ask_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = DATE

    keyboard = [["📅 2023-01-01 - сегодня", "❌ Отмена"]]
    await update.message.reply_text(
        "Введите интервал времени:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return DATE


async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "❌ Отмена":
        context.user_data['state'] = END
        await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text("Введите локацию для поиска:")
        return END
    
    elif text == "📅 2023-01-01 - сегодня":
        context.user_data["date"] = ("2023-01-01", datetime.now().strftime("%Y-%m-%d"))
        
    else:
        try:
            index = text.find(' ')
            date1 = datetime.strptime(text[:index], "%Y-%m-%d")
            date2 = datetime.strptime(text[index + 1:], "%Y-%m-%d")

            if date1.date() > date2.date():
                await update.message.reply_text("Начальная дата не может быть больше конечной!\n"
                                                "Введите интервал времени:")
                return DATE
            elif date1.date() < date(2017, 1, 1):
                await update.message.reply_text("Данные доступны только с 2017-01-01! Измените начальную дату\n"
                                                "Введите интервал времени:")
                return DATE
            elif date2.date() > datetime.now().date():
                await update.message.reply_text("Конечная дата не может быть больше нынешней!\n"
                                                "Введите интервал времени:")
                return DATE
            context.user_data["date"] = (date1.strftime("%Y-%m-%d"), date2.strftime("%Y-%m-%d"))

        except (ValueError, TypeError):
            await update.message.reply_text("Введите интервал времени:")
            return DATE

    return await do_search(update, context)


async def do_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = context.user_data["location"]
    radius = context.user_data["radius"]
    date = context.user_data["date"]

    
    searching_msg = await update.message.reply_text(text="Ищу снимок", reply_markup=ReplyKeyboardRemove())
    error_text = None

    try:
        result = search(location, delta=radius, time_interval=date)
    except SearchError as e:
        error_text = str(e)
    except Exception as e:
        logger.exception("Неожиданная ошибка при поиске снимка")
        error_text = "Внутренняя ошибка бота. Попробуйте позже."
    finally:
        context.user_data['state'] = END
        await searching_msg.delete()

    if error_text is None:
        send_img_msg = await update.message.reply_text(text="Отправляю снимок...", reply_markup=ReplyKeyboardRemove())

        buf = io.BytesIO()
        result['image'].save(buf, format="PNG")
        buf.seek(0)

        await update.message.reply_document(buf, 
                filename=f"{result['metadata']['id']}.png",
                caption=(
                    f"<b>Адрес:</b> {result['address']}\n\n"
                    f"<b>Охват:</b> {result['coords']}\n\n"
                    f"<b>Id снимка:</b> {result['metadata']['id']}\n"
                    f"<b>Дата снимка:</b> {result['metadata']['datetime']}\n"
                    f"<b>Облачность:</b> {result['metadata']['cloud_cover']}%\n\n"
                    f"<b>Разрешение:</b> {result['resolution']} м\n"
                    f"<b>Размер:</b> {result['size']} пикселей"),
                parse_mode=ParseMode.HTML)

        await send_img_msg.delete()
    else:
        await update.message.reply_text(
            f"🛑 <b>Ошибка:</b> <i>{html.escape(error_text)}</i>",
            parse_mode=ParseMode.HTML)
    
    await update.message.reply_text("Введите локацию для поиска:")
    return END
