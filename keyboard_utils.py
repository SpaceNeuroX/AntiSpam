from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def get_ban_keyboard(user_id, chat_id):
    main_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Забанить", callback_data=f"ban_{user_id}_{chat_id}")],
        [InlineKeyboardButton(text="Сообщение определено неверно", callback_data=f"incorrect_{user_id}_{chat_id}")]
    ])
    return main_kb
