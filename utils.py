import subprocess
import os
from aiogram.types import Message
import json
import subprocess
from handlers import has_permission, bot
from ruSpamLib import is_spam
from keyboard_utils import get_ban_keyboard
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
        temp_dir_base = 'temp_bot_repo_'
        temp_dir_number = 1
        while os.path.exists(f'{temp_dir_base}{temp_dir_number}'):
            temp_dir_number += 1
        temp_dir = f'{temp_dir_base}{temp_dir_number}'
        os.makedirs(temp_dir, exist_ok=True)

        git_token = os.getenv('GIT_TOKEN')
        if not git_token:
            await message.reply("Токен GitHub не найден в переменных окружения.")
            return

        repo_url = f'https://{git_token}@github.com/SpaceNeuroX/AntiSpam.git'

        await message.reply("Клонирование репозитория...")
        subprocess.run(['git', 'clone', repo_url, temp_dir], check=True)

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

        subprocess.Popen([sys.executable, 'main_bot.py'])
        os._exit(0)

    except subprocess.CalledProcessError as e:
        await message.reply(f"Произошла ошибка при обновлении бота: {e}")
    except Exception as e:
        await message.reply(f"Произошла неизвестная ошибка: {e}")

async def handle_message(message: Message, edited=False, original_text=None):
    pred_average = False
    chat_id = message.chat.id
    user_id = message.from_user.id
    threshold = thresholds.get(str(chat_id), 10)

    if str(chat_id) not in user_messages:
        user_messages[str(chat_id)] = {}
    if str(user_id) not in user_messages[str(chat_id)]:
        user_messages[str(chat_id)][str(user_id)] = 0
    user_messages[str(chat_id)][str(user_id)] += 1
    save_data(USER_MESSAGES_DB, user_messages)

    chat_settings = load_chat_settings().get(str(chat_id), {})

    pred_average, confidence = is_spam(message.text, model_name="spamNS_v6")

    if pred_average and user_messages[str(chat_id)][str(user_id)] < threshold:
        keyboard = get_ban_keyboard(message.from_user.id, message.chat.id)

        if chat_settings.get('delete_message', True):
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            confidence_percent = int(confidence * 100)
            
            if edited and original_text:
                await bot.send_message(
                    chat_id,
                    f"Изменённое сообщение от @{message.from_user.username} было удалено в {message.chat.title}:\n\n"
                    f"Оригинальное сообщение: <tg-spoiler>{original_text}</tg-spoiler>\n"
                    f"Изменённое сообщение: <tg-spoiler>{message.text}</tg-spoiler>\n"
                    f"Вероятность спама: {confidence_percent}%",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                await bot.send_message(
                    chat_id,
                    f"Сообщение от @{message.from_user.username} удалено в {message.chat.title}:\n\n"
                    f"<tg-spoiler>{message.text}, вероятность модели: {confidence_percent}%</tg-spoiler>",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

        if chat_settings.get('ban', False) and pred_average:
            if has_permission(message):
                await bot.send_message(chat_id, "Нельзя забанить администратора!")
                return

            await bot.ban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

        if chat_settings.get('mute', False) and pred_average:
            if has_permission(message):
                await bot.send_message(chat_id, "Нельзя замутить администратора!")
                return

            await bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.from_user.id, can_send_messages=False)