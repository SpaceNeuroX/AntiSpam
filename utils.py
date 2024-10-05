import subprocess
import os
from aiogram.types import Message, InputFile
import os
import json
import os
import subprocess
import shutil
import sys

THRESHOLDS_DB = "./thresholds.json"
USER_MESSAGES_DB = "./user_messages.json"
WRONG_MESSAGES = "./wrong_messages.json"
CHAT_SETTINGS_DB = "./chat_settings.json"
BANLIST_DB = "./banlistDB/banlist.json"

SPECIAL_USER_IDS = [7264930816]

def load_data(db_file):
    if os.path.exists(db_file):
        with open(db_file, "r") as file:
            return json.load(file)
    return {}

def save_data(db_file, data):
    with open(db_file, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

thresholds = load_data(THRESHOLDS_DB)
user_messages = load_data(USER_MESSAGES_DB)
chat_settings_data = load_data(CHAT_SETTINGS_DB)
banlist = load_data(BANLIST_DB)

def load_chat_settings():
    return chat_settings_data

def save_chat_settings(data):
    save_data(CHAT_SETTINGS_DB, data)

async def initialize_chat_settings(chat_id):
        chat_settings = {
            'subscribe': False,
            'mute': False,
            'delete_message': True,
            'ban': False,
            'notification': True
        }
        chat_settings_data = load_chat_settings()
        chat_settings_data[str(chat_id)] = chat_settings
        save_chat_settings(chat_settings_data)



def get_user_rank(message_count):
    if message_count < 100:
        return "Новичок 🌱"
    elif 100 <= message_count < 500:
        return "Опытный"
    elif 500 <= message_count < 1000:
        return "Сударь 👑"
    else:
        return "Царь 🦹‍♂️"
    
async def update_bot_command(message: Message):
    user_id = message.from_user.id

    if user_id not in SPECIAL_USER_IDS:
        await message.reply("Только владелец бота может обновить бота.")
        return

    try:
        temp_dir = 'temp_bot_repo'
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir)
        await message.reply("Клонирование репозитория...")
        subprocess.run(['git', 'clone', 'https://github.com/SpaceNeuroX/AntiSpam', temp_dir], check=True)

        await message.reply("Удаление старых файлов...")
        for file in os.listdir('.'):
            if file.endswith('.py'):
                os.remove(file)

        await message.reply("Копирование новых файлов...")
        for file in os.listdir(temp_dir):
            if file.endswith('.py'):
                shutil.copy(os.path.join(temp_dir, file), '.')

        shutil.rmtree(temp_dir, ignore_errors=True)

        await message.reply("Перезапуск бота...")
        os.execl(sys.executable, sys.executable, *sys.argv)

    except subprocess.CalledProcessError as e:
        await message.reply(f"Произошла ошибка при обновлении бота: {e}")
    except Exception as e:
        await message.reply(f"Произошла неизвестная ошибка: {e}")
		