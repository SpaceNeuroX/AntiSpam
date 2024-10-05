from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram import types
from utils import load_chat_settings

def get_ban_keyboard(user_id, chat_id):
    main_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ban", callback_data=f"ban_{user_id}_{chat_id}")],
        [InlineKeyboardButton(text="Message incorrectly classified", callback_data=f"incorrect_{user_id}_{chat_id}")]
    ])
    return main_kb

def settings_keyboard(chat_id):
        chat_settings = load_chat_settings().get(str(chat_id), {})
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                text=f"🔒 Забанить: {'✅' if chat_settings.get('ban', False) else '❌'}",
                callback_data='toggle_ban_user'
            ),
            types.InlineKeyboardButton(
                text=f"🔇 Замутить: {'✅' if chat_settings.get('mute', False) else '❌'}",
                callback_data='toggle_mute_user'
            ),
            types.InlineKeyboardButton(
                text=f"📩 Уведомления: {'✅' if chat_settings.get('notification', False) else '❌'}",
                callback_data='toggle_notify_admin'
            ),
            types.InlineKeyboardButton(
                text=f"🗑 Удалить сообщения: {'✅' if chat_settings.get('delete_message', False) else '❌'}",
                callback_data='toggle_delete_message'
            ),
            types.InlineKeyboardButton(
                text=f"🗑 Удалить нецензурную лексику: {'✅' if chat_settings.get('deletemat', False) else '❌'}",
                callback_data='toggle_deletemat'  
            )
        )
        return keyboard