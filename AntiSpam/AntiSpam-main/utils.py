import subprocess
import os
from aiogram.types import Message
import json
import asyncio
import subprocess
import shutil
import sys

THRESHOLDS_DB = "./thresholds.json"
USER_MESSAGES_DB = "./user_messages.json"
WRONG_MESSAGES = "./wrong_messages.json"
CHAT_SETTINGS_DB = "./chat_settings.json"
BANLIST_DB = "./banlistDB/banlist.json"

SPECIAL_USER_IDS = [7264930816, 5795045879]

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
            'mute': False,
            'delete_message': True,
            'ban': False,
            'delete_links': False
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
        temp_dir_base = 'temp_bot_repo_'
        temp_dir_number = 1
        while os.path.exists(f'{temp_dir_base}{temp_dir_number}'):
            temp_dir_number += 1
        temp_dir = f'{temp_dir_base}{temp_dir_number}'
        os.makedirs(temp_dir, exist_ok=True)

        git_token = os.getenv('GIT_TOKEN')
        if not git_token:
            await message.reply("❌ Токен GitHub не найден в переменных окружения.")
            return

        repo_url = f'https://{git_token}@github.com/SpaceNeuroX/AntiSpam.git'

        status_msg = await message.reply("Клонирование репозитория... [0%]")
        
        subprocess.run(['git', 'clone', repo_url, temp_dir], check=True)
        await status_msg.edit_text("Клонирование репозитория... [30%]")

        await asyncio.sleep(1)
        await status_msg.edit_text("Удаление старых файлов... [50%]")
        for file in os.listdir('.'):
            if file.endswith('.py'):
                os.remove(file)

        await asyncio.sleep(1)
        await status_msg.edit_text("Копирование новых файлов... [70%]")
        for file in os.listdir(temp_dir):
            if file.endswith('.py'):
                shutil.copy(os.path.join(temp_dir, file), '.')

        await asyncio.sleep(1)
        await status_msg.edit_text("Удаление временных файлов... [90%]")
        shutil.rmtree(temp_dir, ignore_errors=True)

        await asyncio.sleep(1)
        await status_msg.edit_text("Перезапуск бота... [100%]")

        
        await asyncio.sleep(1)
        await status_msg.edit_text("✅ Успешно! ... [100%]")

        subprocess.Popen([sys.executable, 'main_bot.py'])
        os._exit(0)

    except subprocess.CalledProcessError as e:
        await status_msg.edit_text(f"❌ Произошла ошибка при обновлении бота: {e}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Произошла неизвестная ошибка: {e}")


def add_log_channel(channel_name, log_id):
    
    check = type(log_id)
    print(check)
    print(log_id.isalpha())
    if check == int or str and log_id.replace("-", "").isdigit() == True:
     
     print(f"Лог канал установлен - {channel_name}, {log_id}")
     data = {channel_name : log_id}
     save_data("log_channel.json", data)

    else:
     return "log_id must be integer"





