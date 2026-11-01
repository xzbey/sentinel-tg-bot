from numpy import ndarray
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import asyncio

from analysis.classification import compute_classification
from core.error import SearchError, ParseError, IndicesError, ClassificationError
from tg.tg_constants import logger
from services.image_sentinel import fetch_missing_bands
from analysis.render import make_index_geotiff
from analysis.class_render import make_class_preview
from tg.ui import send_action_menu
from core.scene import Scene


CLASSIFICATION_BANDS = ["B03", "B04", "B08", "B11", "dataMask"]

ZERO_DELTA = {"water": 0.0, "built": 0.0, "veg": 0.0}
STEP = {"water": 0.02, "built": 0.1, "veg": 0.05}
COUNT_STEPS = {"water": 1, "built": -1, "veg": -1}

NAMES = {"water": "Вода", "built": "Застройка / Открытый грунт", "veg": "Растительность"}


def class_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Больше воды", callback_data="class:water:more"),
         InlineKeyboardButton("Меньше воды", callback_data="class:water:less")],
        [InlineKeyboardButton("Больше застройки", callback_data="class:built:more"),
         InlineKeyboardButton("Меньше застройки", callback_data="class:built:less")],
        [InlineKeyboardButton("Больше растительности", callback_data="class:veg:more"),
         InlineKeyboardButton("Меньше растительности", callback_data="class:veg:less")],
    ])

def format_steps(delta) -> str:
    parts = []
    for key, name in NAMES.items():
        steps = round(delta[key] * COUNT_STEPS[key] / STEP[key])
        if steps:
            parts.append(f"{name}: {steps:+d}")
    return ", ".join(parts) if parts else "по умолчанию"


async def send_classification(update: Update, context: ContextTypes.DEFAULT_TYPE, scene: Scene, array: ndarray, delta: dict):
    context.user_data["class_array"] = array
    query = update.callback_query

    status_msg = await query.message.reply_text("Классифицирую снимок...")
    try:
        preview = await asyncio.to_thread(make_class_preview, array)
        geotiff = await asyncio.to_thread(make_index_geotiff, array, scene.crs, scene.transform, name="classification", dtype="uint8", nodata=0)
    except Exception as e:
        logger.exception(f"Ошибка создания композита {str(e)}")
        await query.message.reply_text("Что-то пошло не так, попробуйте позже")
        return
    finally:
        await status_msg.delete()

    try:
        photo_text = await query.message.reply_text("Отправка изображения...")
        photo_msg = await query.message.reply_photo(preview, 
                                                    caption=
                                                        f"<b>Классификация</b>\n"
                                                        f"<b>Корректировка:</b> {format_steps(delta)}\n\n"
                                                        f"<b>Охват:</b> {scene.coords}\n\n"
                                                        f"<b>Id снимка:</b> {scene.metadata['id']}\n"
                                                        f"<b>Дата снимка:</b> {scene.date}\n"
                                                        f"<b>Размер:</b> {scene.size} пикселей",
                                                    parse_mode=ParseMode.HTML,
                                                    reply_markup=class_keyboard())
        await photo_text.delete()

        gtiff_text = await query.message.reply_text("Отправка geotiff...")
        await photo_msg.reply_document(geotiff, 
                                        filename=f"class_{scene.metadata['id']}.tif",
                                        do_quote=True,
                                        write_timeout=120)
        await gtiff_text.delete()
        await send_action_menu(update, context)

    except Exception as e:
        logger.exception(f"Ошибка отправки файла или фото {str(e)}")
        await query.message.reply_text("Ошибка отправки данных индекса, попробуйте еще раз или позже")


async def classification_scene(update: Update, context: ContextTypes.DEFAULT_TYPE, scene: Scene,
                               status_text: str = "Классифицирую снимок...") -> bool:
    query = update.callback_query

    context.user_data["class_delta"] = ZERO_DELTA.copy()
    delta = context.user_data.get("class_delta")

    status_msg = await query.message.reply_text(status_text)
    try:
        async with scene.lock:
            await asyncio.to_thread(fetch_missing_bands, scene, CLASSIFICATION_BANDS)
        array = await asyncio.to_thread(compute_classification, scene, context.user_data.get("class_delta"))

    except (IndicesError, SearchError, ParseError, ClassificationError) as e:
        await query.message.reply_text(str(e))
        return False
    except Exception as e:
        logger.exception(f"Ошибка классификации {str(e)}")
        await query.message.reply_text("Что-то пошло не так, попробуйте позже")
        return False
    finally:
        await status_msg.delete()

    await send_classification(update, context, scene, array, delta)
    return True


async def classification_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    scene = context.user_data.get("scene")
    if scene is None:
        await query.message.reply_text("Сессия потеряна, сделайте новый поиск")
        return

    await classification_scene(update, context, scene)


async def classification_set_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    scene = context.user_data.get("scene")
    delta = context.user_data.get("class_delta")
    if scene is None or delta is None:
        await query.message.reply_text("Сессия потеряна, сделайте новый поиск")
        return

    _, key, action = query.data.split(":")

    new_delta = delta.copy()
    new_delta[key] = round(delta[key] + COUNT_STEPS[key] * (1 if action == "more" else -1) * STEP[key], 4)

    try:
        array = await asyncio.to_thread(compute_classification, scene, new_delta)
    except ClassificationError as e:
        await query.message.reply_text(str(e))
        return
    except Exception as e:
        logger.exception(f"Ошибка классификации {str(e)}")
        await query.message.reply_text("Что-то пошло не так, попробуйте позже")
        return

    context.user_data["class_delta"] = new_delta

    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    await send_classification(update, context, scene, array, new_delta)