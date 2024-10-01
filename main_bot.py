# This code sets up handlers for a Telegram bot using the aiogram library.
# It includes handlers for various commands and message processing.
#
# Author: @NeuroSpaceX
#
# Libraries used:
# - aiogram: Library for building Telegram bots.
# - AntiMat: Module for filtering text (possibly for profanity).
# - ruSpamLib: Library for spam detection. Developed by @NeuroSpaceX.
#   This library is licensed under a non-commercial use license.
#   You are allowed to use it only for non-commercial purposes and must credit the author.
# - keyboard_utils: Module containing functions to generate keyboards.
# License:
# This code is licensed under a non-commercial use license.
# You are allowed to use it only for non-commercial purposes and must credit the author @NeuroSpaceX.
		
import asyncio
from aiogram import Bot, Dispatcher
from handlers import setup_handlers
from text_content import get_start_text, get_help_text

API_TOKEN = "7266035860:AAGUEm92UxBtInV7LgheycAeg3lxZYAeVV0"

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
