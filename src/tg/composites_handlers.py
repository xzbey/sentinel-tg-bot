from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import asyncio

from analysis.export import make_geotiff
from core.error import SearchError, ParseError, IndicesError
from core.config import allowableBands
from analysis.composites import composites_names, make_composite_preview, parse_composite_text
from core.scene import Scene
from tg.tg_constants import logger, COMPOSITE, END
from services.image_sentinel import fetch_missing_bands


async def send_composite(message, scene: Scene, title: str, bands: list[str]):
    try:
        async with scene.lock:
            await asyncio.to_thread(fetch_missing_bands, scene, bands)

        preview = await asyncio.to_thread(make_composite_preview, scene, bands)
        bands.append("dataMask")
        geotiff = await asyncio.to_thread(make_geotiff, scene, bands)

    except (IndicesError, SearchError, ParseError) as e:
        await message.reply_text(str(e))
        return
    except Exception as e:
        logger.exception(f"Ошибка создания композита {str(e)}")
        await message.reply_text("Что-то пошло не так, попробуйте позже")
        return

    caption = (f"<b>Композит</b>: {title}\n"
               f"<b>Каналы</b>: {", ".join(bands)}\n\n"
               f"<b>Охват:</b> {scene.coords}\n\n"
               f"<b>Id снимка:</b> {scene.metadata['id']}\n"
               f"<b>Дата снимка:</b> {scene.date}\n"
               f"<b>Размер:</b> {scene.size} пикселей")

    try:
        if preview is not None:
            photo_text = await message.reply_text("Отправка изображения...")
            photo_msg = await message.reply_photo(preview,
                                                  caption=caption,
                                                  parse_mode=ParseMode.HTML,
                                                  do_quote=True)
            await photo_text.delete()
        else:
            photo_msg = await message.reply_text(caption,
                                                 parse_mode=ParseMode.HTML,
                                                 do_quote=True)

        len_tiff = len(geotiff) / (1024 * 1024)
        if len_tiff > 50:
            await photo_msg.reply_text(f"Документ слишком большой, размер: {len_tiff:.1f} МБ\n"
                                       f"Уменьшите радиус/полигон или число каналов!")
            return

        gtiff_text = await message.reply_text("Отправка geotiff...")
        await photo_msg.reply_document(geotiff, 
                                        filename=f"{title}_{scene.metadata['id']}.tif",
                                        do_quote=True,
                                        write_timeout=120)
        await gtiff_text.delete()

    except Exception as e:
        logger.exception(f"Ошибка отправки файла или фото {str(e)}")
        await message.reply_text("Ошибка отправки композита, попробуйте еще раз или позже")


async def composite_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    name = query.data.split(":")[1]
    scene = context.user_data.get("scene")
    if scene is None:
        await query.message.reply_text("Сессия потеряна, сделайте новый поиск")
        return
    if name not in composites_names:
        await query.message.reply_text("Неизвестный композит")
        return

    await send_composite(query.message, scene, name, composites_names[name])


async def ask_composite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if context.user_data.get("scene") is None:
        await update.message.reply_text("Сессия потеряна, сделайте новый поиск", reply_markup=ReplyKeyboardRemove())
        return END

    context.user_data['state'] = COMPOSITE
    keyboard = [["❌ Отмена"]]
    await query.message.reply_text("Введите каналы через пробел, например, B04 B03 B02!\n"
                                   f"Доступные каналы S2B L2A: <b>{' '.join(allowableBands)}</b>\n",
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return COMPOSITE


async def get_composite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "❌ Отмена":
        context.user_data['state'] = END
        await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
        return END

    scene = context.user_data.get("scene")
    if scene is None:
        context.user_data['state'] = END
        await update.message.reply_text("Сессия потеряна, сделайте новый поиск", reply_markup=ReplyKeyboardRemove())
        return END

    try:
        bands = parse_composite_text(text)
    except ParseError as e:
        await update.message.reply_text(f"{str(e)}\nПопробуйте еще раз!")
        return COMPOSITE

    
    await update.message.reply_text("Строю композит...", reply_markup=ReplyKeyboardRemove())
    await send_composite(update.message, scene, "Свой набор", bands)

    context.user_data['state'] = END
    return END

        