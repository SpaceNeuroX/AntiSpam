import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database_utils import add_chat, get_chat_settings
from handlers import setup_handlers
from text_content import get_start_text, get_info_text, get_help_text
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database setup
DB_USER = 'default'
DB_PASSWORD = 'M9qpGDUuaPN2'
DB_NAME = 'verceldb'
DB_HOST = 'ep-yellow-art-a4ueqjif.us-east-1.aws.neon.tech'
DB_PORT = '5432'
DB_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require'
engine = create_engine(DB_URI)
Session = sessionmaker(bind=engine)

# Bot and Dispatcher setup
bot = Bot(token="7266035860:AAGUEm92UxBtInV7LgheycAeg3lxZYAeVV0")
dp = Dispatcher()

# Load text content
start_text = get_start_text()
info_text = get_info_text()
help_text = get_help_text()

# Setup handlers
setup_handlers(dp, bot, Session, start_text, info_text, help_text)

async def main() -> None:
    print("Starting...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
