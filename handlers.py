from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

import io

from geo_search import search

from datetime import datetime, date

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text=
    "🌍 Это бот для поиска <b>Sentinel2 L2A</b> снимков по локации (адрес или координата точки), радиусу удаления от точки и интервалу времени.\n\n" \
    "📄 Чтобы ознакомиться с инструкцией, введите <code>/guide</code>.",
    parse_mode=ParseMode.HTML)

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text=
    "🌍 Это бот для поиска <b>Sentinel2 L2A</b> снимков.\n\n" \
    
    "<u>Для получения снимка необходимо по шагам ввести:</u>\n\n" \
    
    "   1️⃣ <b>Локацию</b>. Например:\n" \
    "   • Общее название - <code>РТУ МИРЭА</code>\n" \
    "   • Адрес - <code>Москва, просп. Вернадского, 78, стр. 4</code>\n" \
    "   • Координату точки - <code>55.669986, 37.480409</code>\n\n" \
    
    "   2️⃣ <b>Радиус удаления</b> от точки в километрах <b>(0.1 - 50 км)</b>\n" \
    "   или нажать на кнопку <b>📍 5 км - по умолчанию</b>.\n\n" \
    
    "   3️⃣ <b>Интервал времени</b> в формате:\n" \
    "   <code>ГГГГ-ММ-ДД ГГГГ-ММ-ДД</code>\n" \
    "   или нажать на кнопку <b>📅 2023-01-01 - сегодня</b>.\n" \
    "   ⚠️ Не раньше <code>2017-01-01</code> и не позже сегодняшней даты.\n\n" \
    
    "<u>На любом шаге можно нажать кнопку <b>Отмена</b>, которая вернет всё в исходное состояние.</u>\n" \
    "После данных действий бот будет искать снимок по заданным критериям и информировать вас о процессе.\n\n" \
    
    "<i>Введите локацию для поиска:</i>",
    parse_mode=ParseMode.HTML, 
    reply_markup=ReplyKeyboardRemove())

    return END

RADIUS, DATE = range(2)
END = ConversationHandler.END

async def ask_radius(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['location'] = update.message.text
    keyboard = [["📍 5 км - по умолчанию", "❌ Отмена"]]
    await update.message.reply_text(
        "Введите радиус поиска в км (0.1 - 50)",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return RADIUS

async def get_radius(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "❌ Отмена":
        await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text("Введите локацию для поиска:")
        return END
    
    elif text == "📍 5 км - по умолчанию":
        context.user_data["radius"] = 0.05

    else:
        try:
            rad = float(text)
            if rad < 0.1 or rad > 50:
                await update.message.reply_text("Введите радиус поиска:")
                return RADIUS
            context.user_data["radius"] = rad / 100

        except (ValueError, TypeError):
            await update.message.reply_text("Введите радиус поиска:")
            return RADIUS

    return await ask_date(update, context)


async def ask_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📅 2023-01-01 - сегодня", "❌ Отмена"]]
    await update.message.reply_text(
        "Введите интервал времени:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "❌ Отмена":
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
    search_result = search(location, delta=radius, time_interval=date)

    if search_result["success"]:
        await searching_msg.delete()
        send_img_msg = await update.message.reply_text(text="Отправляю снимок...", reply_markup=ReplyKeyboardRemove())

        buf = io.BytesIO()
        search_result['data']['image'].save(buf, format="PNG")
        buf.seek(0)

        await update.message.reply_document(buf, 
                filename=f"{search_result['data']['metadata']['id']}.png",
                caption=(
                    f"<b>Адрес:</b> {search_result['data']['address']}\n\n"
                    f"<b>Охват:</b> {search_result['data']['coords']}\n\n"
                    f"<b>Id снимка:</b> {search_result['data']['metadata']['id']}\n"
                    f"<b>Дата снимка:</b> {search_result['data']['metadata']['datetime']}\n"
                    f"<b>Облачность:</b> {search_result['data']['metadata']['cloud_cover']}%\n\n"
                    f"<b>Разрешение:</b> {search_result['data']['resolution']} м\n"
                    f"<b>Размер:</b> {search_result['data']['size']} пикселей"),
                parse_mode=ParseMode.HTML)

        await send_img_msg.delete()
    else:
        await searching_msg.delete()
        await update.message.reply_text(
            f"🛑 <b>Ошибка:</b> <i>{search_result['error']}</i>",
            parse_mode=ParseMode.HTML)
    
    await update.message.reply_text("Введите локацию для поиска:")
    return END



