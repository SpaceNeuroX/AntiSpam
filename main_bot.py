import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import filters
from handlers import setup_handlers
from text_content import get_start_text, get_help_text
from utils import SPECIAL_USER_IDS

API_TOKEN = "8097084613:AAHxNR0Xa2BE6BxGoqhe5C477pNel4APv-8"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

class IsAdminFilter(filters.BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

    async def check(self, message: types.Message):
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return chat_member.status in ["creator", "administrator"] if self.is_admin else chat_member.status not in ["creator", "administrator"]

dp.filters_factory.bind(IsAdminFilter)

start_text = get_start_text()
help_text = get_help_text()

setup_handlers(dp, bot, start_text, help_text)

async def main() -> None:
    print("Starting...")
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())