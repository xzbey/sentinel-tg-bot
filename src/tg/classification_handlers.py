from telegram import Update
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


CLASSIFICATION_BANDS = ["B03", "B04", "B08", "B11", "dataMask"]

async def classification_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    scene = context.user_data.get("scene")
    if scene is None:
        await query.message.reply_text("Сессия потеряна, сделайте новый поиск")
        return

    status_msg = await query.message.reply_text("Классифицирую снимок...")
    try:
        async with scene.lock:
            await asyncio.to_thread(fetch_missing_bands, scene, CLASSIFICATION_BANDS)
        array = await asyncio.to_thread(compute_classification, scene)

        preview = await asyncio.to_thread(make_class_preview, array)
        geotiff = await asyncio.to_thread(make_index_geotiff, array, scene.crs, scene.transform, name="classification", dtype="uint8", nodata=0)

    except (IndicesError, SearchError, ParseError, ClassificationError) as e:
        await query.message.reply_text(str(e))
        return
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
                                                        f"<b>Классификация</b>\n\n"
                                                        f"<b>Охват:</b> {scene.coords}\n\n"
                                                        f"<b>Id снимка:</b> {scene.metadata['id']}\n"
                                                        f"<b>Дата снимка:</b> {scene.date}\n"
                                                        f"<b>Размер:</b> {scene.size} пикселей",
                                                    parse_mode=ParseMode.HTML)
        await photo_text.delete()

        gtiff_text = await query.message.reply_text("Отправка geotiff...")
        await photo_msg.reply_document(geotiff, 
                                        filename=f"classification_{scene.metadata['id']}.tif",
                                        do_quote=True,
                                        write_timeout=120)
        await gtiff_text.delete()
        await send_action_menu(update, context)

    except Exception as e:
        logger.exception(f"Ошибка отправки файла или фото {str(e)}")
        await query.message.reply_text("Ошибка отправки данных индекса, попробуйте еще раз или позже")