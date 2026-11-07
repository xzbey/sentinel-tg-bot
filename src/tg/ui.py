from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from analysis.indices import indices
from analysis.composites import composites_names

def build_scene_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(name, callback_data=f"i:{name}") for name in indices],
                                 [InlineKeyboardButton(name, callback_data=f"composite:{name}") for name in composites_names] 
                                     + [InlineKeyboardButton("Свой вариант", callback_data=f"custom:composite")],
                                 [InlineKeyboardButton("Классификация", callback_data="classification")],
                                 [InlineKeyboardButton("Векторизация", callback_data="vectorization")]])

async def safe_delete(msg):
    try:
        await msg.delete()
    except TelegramError:
        pass


async def send_action_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    old_menu = context.user_data.pop("menu_msg", None)
    if old_menu:
        await safe_delete(old_menu)

    chat = update.effective_chat
    if context.user_data.get("scene") is not None:
        context.user_data["menu_msg"] = await chat.send_message(
            "Введите новую локацию (или отправьте GeoJSON) для поиска, либо выберите обработку текущего снимка:",
            reply_markup=build_scene_keyboard()
        )
    else:
        context.user_data["menu_msg"] = await chat.send_message(
            "Введите новую локацию (или отправьте GeoJSON) для поиска:"
        )