import asyncio
from aiogram import Bot

async def get_chat_info():
    async with Bot(token="7266035860:AAGUEm92UxBtInV7LgheycAeg3lxZYAeVV0") as bot:
        chat_id = -1002047364016  # replace with the correct group ID
        try:
            chat = await bot.get_chat(chat_id)
            print(chat.title)
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(get_chat_info())
