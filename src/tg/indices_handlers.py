from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import asyncio

from analysis.render import make_index_geotiff, make_index_preview
from core.error import SearchError, ParseError, IndicesError
from analysis.indices import compute_index, indices
from tg.tg_constants import logger
from services.image_sentinel import fetch_missing_bands

async def indices_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    name = query.data.split(":")[1]
    scene = context.user_data.get("scene")
    if scene is None:
        await query.message.reply_text("Сессия потеряна, сделайте новый поиск")
        return

    try:
        async with scene.lock:
            await asyncio.to_thread(fetch_missing_bands, scene, indices[name])
        array = await asyncio.to_thread(compute_index, scene, name)

        preview = await asyncio.to_thread(make_index_preview, array, name)
        geotiff = await asyncio.to_thread(make_index_geotiff, array, scene.crs, scene.transform)

    except (IndicesError, SearchError, ParseError) as e:
        await query.message.reply_text(str(e))
        return
    except Exception as e:
        logger.exception(f"Ошибка расчета индекса {str(e)}")
        await query.message.reply_text("Что-то пошло не так, попробуйте позже")
        return

    try:
        photo_text = await query.message.reply_text("Отправка изображения...")
        photo_msg = await query.message.reply_photo(preview, 
                                                    caption=
                                                        f"<b>Индекс</b>: {name}\n\n"
                                                        f"<b>Охват:</b> {scene.coords}\n\n"
                                                        f"<b>Id снимка:</b> {scene.metadata['id']}\n"
                                                        f"<b>Дата снимка:</b> {scene.date}\n"
                                                        f"<b>Размер:</b> {scene.size} пикселей",
                                                    parse_mode=ParseMode.HTML,
                                                    do_quote=True)
        await photo_text.delete()

        gtiff_text = await query.message.reply_text("Отправка geotiff...")
        await photo_msg.reply_document(geotiff, 
                                       filename=f"{name}_{scene.metadata['id']}.tif",
                                       do_quote=True,
                                       write_timeout=120)
        await gtiff_text.delete()

    except Exception as e:
        logger.exception(f"Ошибка отправки файла или фото {str(e)}")
        await query.message.reply_text("Ошибка отправки данных индекса, попробуйте еще раз или позже")