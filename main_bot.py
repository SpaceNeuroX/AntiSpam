import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import filters
from handlers import setup_handlers
from text_content import get_start_text, get_help_text
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token="7753365116:AAFSjj4qNJrhaEN7YQabLVoVsRIWaU_R83Y")
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
