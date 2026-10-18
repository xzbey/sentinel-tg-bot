from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import TelegramError

import html
import logging
import asyncio

from analysis.parse import parse_file
from pipeline.pipeline import search
from core.error import SearchError, ParseError

from datetime import datetime, date

logger = logging.getLogger(__name__)

RADIUS, DATE = range(2)
END = ConversationHandler.END

async def ask_radius(update: Update, context: ContextTypes.DEFAULT_TYPE, repeat: bool = False):
    if not repeat:
        context.user_data.clear()
        context.user_data['location'] = update.message.text
        context.user_data['state'] = RADIUS

    keyboard = [["📍 5 км - по умолчанию", "❌ Отмена"]]
    await update.message.reply_text(
        "Введите радиус поиска в км (0.1 - 50)",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return RADIUS


async def get_file_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc.file_name or not doc.file_name.lower().endswith(".geojson"):
        await update.message.reply_text("Принимаются только файлы GeoJSON!")
        return

    if doc.file_size and doc.file_size > (20 * 1024 * 1024):
        await update.message.reply_text("Файл слишком большой, лимит 20 МБ.")
        return

    try:
        tg_file = await doc.get_file()
        data = await asyncio.to_thread(parse_file, await tg_file.download_as_bytearray())

        context.user_data.clear()
        match data["state"]:
            case "point":
                context.user_data["state"] = RADIUS
                context.user_data["geometry"] = data["geometry"]
                return await ask_radius(update, context, repeat=True)
            case "polygon":
                context.user_data["state"] = DATE
                context.user_data["geometry"] = data["geometry"]
                return await ask_date(update, context)

    except TelegramError:
        await update.message.reply_text("Не удалось скачать файл, попробуйте еще раз")
        return END
    except ParseError as e:
        await update.message.reply_text(str(e))
        return END
    except Exception as e:
        error_text = f"Неожиданная ошибка при поиске снимка: {str(e)}"
        logger.exception(error_text)
        await update.message.reply_text(error_text)
        return END


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
                return await ask_radius(update, context, repeat=True)
            context.user_data["radius"] = rad / 100

        except (ValueError, TypeError):
            return await ask_radius(update, context, repeat=True)
            

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
    location = context.user_data.get("location")
    geometry = context.user_data.get("geometry")
    radius = context.user_data.get("radius")
    date = context.user_data.get("date")
    
    searching_msg = await update.message.reply_text(text="Ищу снимок", reply_markup=ReplyKeyboardRemove())
    error_text = None

    try:
        result = await asyncio.to_thread(search, 
                                         location = location, 
                                         geometry = geometry,
                                         delta = radius, 
                                         time_interval = date)
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

        try:
            photo_msg = await update.message.reply_photo(result["preview"], 
                    caption=(
                        f"<b>Адрес:</b> {html.escape(result['address'])}\n\n"
                        f"<b>Охват:</b> {result['coords']}\n\n"
                        f"<b>Id снимка:</b> {result['metadata']['id']}\n"
                        f"<b>Дата снимка:</b> {result['metadata']['datetime']}\n"
                        f"<b>Облачность:</b> {result['metadata']['cloud_cover']}%\n\n"
                        f"<b>Разрешение:</b> {result['resolution']} м\n"
                        f"<b>Размер:</b> {result['size']} пикселей"),
                    parse_mode=ParseMode.HTML)

            len_tiff = len(result["tiff"]) / (1024 * 1024)
            if len_tiff > 50:
                await photo_msg.reply_text(f"Документ слишком большой, размер: {len_tiff:.1f} МБ\n"
                                        f"Уменьшите радиус или полигон!")
            else:
                await photo_msg.reply_document(result["tiff"],
                                            filename=f"{result['metadata']['id']}.tiff",
                                            do_quote=True)
        except Exception as e:
            logger.exception(f"Ошибка отправки файла/фото {str(e)}")
            await update.message.reply_text("Возникла непредвиденная ошибка при отправке файла!")

        await send_img_msg.delete()
    else:
        await update.message.reply_text(
            f"🛑 <b>Ошибка:</b> <i>{html.escape(error_text)}</i>",
            parse_mode=ParseMode.HTML)
    
    await update.message.reply_text("Введите локацию для поиска:")
    return END
