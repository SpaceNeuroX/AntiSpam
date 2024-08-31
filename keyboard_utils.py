from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def get_ban_keyboard(user_id, chat_id):
    main_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Забанить", callback_data=f"ban_{user_id}_{chat_id}")]
    ])
    return main_kb

def get_web_app_button(group_id):
    print(group_id)
    url = f"https://react-project-sigma-three.vercel.app/{group_id}"
    print(url)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в веб-приложение", web_app=WebAppInfo(url=url))]
    ])
    return keyboard
