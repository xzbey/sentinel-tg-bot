from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import asyncio

from analysis.vectorization import vectorization
from core.error import VectorizationError
from tg.classification_handlers import classification_scene
from tg.tg_constants import logger
from tg.ui import send_action_menu


async def vectorization_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    scene = context.user_data.get("scene")
    if scene is None:
        await query.message.reply_text("Сессия потеряна, сделайте новый поиск")
        return

    if context.user_data.get("class_array") is None:
        if not await classification_scene(update, context, scene, "Сначала классифицирую снимок..."):
            return
    class_array = context.user_data.get("class_array")

    status_msg = await query.message.reply_text("Векторизирую снимок...")
    try:
        gpf = await asyncio.to_thread(vectorization, class_array, scene.transform, scene.crs)
    except VectorizationError as e:
        await query.message.reply_text(str(e))
        return
    except Exception as e:
        logger.exception(f"Ошибка векторизации {str(e)}")
        await query.message.reply_text("Что-то пошло не так, попробуйте позже")
        return
    finally:
        await status_msg.delete()

    try:
        gpkg_text = await query.message.reply_text("Отправка GeoPackage...")
        await query.message.reply_document(gpf,
                                           caption=
                                                f"<b>Векторизация</b>\n\n"
                                                f"<b>Охват:</b> {scene.coords}\n\n"
                                                f"<b>Id снимка:</b> {scene.metadata['id']}\n"
                                                f"<b>Дата снимка:</b> {scene.date}\n"
                                                f"<b>Размер:</b> {scene.size} пикселей",
                                           parse_mode=ParseMode.HTML,
                                           filename=f"vect_{scene.metadata['id']}.gpkg",
                                           write_timeout=120)
        await gpkg_text.delete()
        await send_action_menu(update, context)

    except Exception as e:
        logger.exception(f"Ошибка отправки файла {str(e)}")
        await query.message.reply_text("Ошибка отправки данных векторизации, попробуйте еще раз или позже")