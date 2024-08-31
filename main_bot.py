import asyncio
from aiogram import Bot, Dispatcher
from handlers import setup_handlers
from text_content import get_start_text, get_info_text, get_help_text

bot = Bot(token="7266035860:AAGUEm92UxBtInV7LgheycAeg3lxZYAeVV0")
dp = Dispatcher()

start_text = get_start_text()
info_text = get_info_text()
help_text = get_help_text()

setup_handlers(dp, bot, start_text, info_text, help_text)

async def main() -> None:
    print("Starting...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
