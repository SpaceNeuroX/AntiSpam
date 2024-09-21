import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from handlers import setup_handlers
from text_content import get_start_text, get_help_text

API_TOKEN = "7311526472:AAHVqVHIu0s7a2XqNIg4G6N0nnVrWm_2Dn4"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

start_text = get_start_text()
help_text = get_help_text()

setup_handlers(dp, bot, start_text, help_text)

async def main() -> None:
    print("Starting...")
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
