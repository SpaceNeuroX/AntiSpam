import os
import json

LOG_CHANNELS_DB = "./log_channels.json"
THRESHOLDS_DB = "./thresholds.json"
USER_MESSAGES_DB = "./user_messages.json"
WRONG_MESSAGES = "./wrong_messages.json"
BANNED_MESSAGES_DB = "./banned_messages.json"
CHAT_SETTINGS_DB = "./chat_settings.json"
BANLIST_DB = ".banlistDB/banlist.json"

SPECIAL_USER_IDS = [7264930816]

def load_data(db_file):
    if os.path.exists(db_file):
        with open(db_file, "r") as file:
            return json.load(file)
    return {}

def save_data(db_file, data):
    with open(db_file, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

log_channels = load_data(LOG_CHANNELS_DB)
thresholds = load_data(THRESHOLDS_DB)
user_messages = load_data(USER_MESSAGES_DB)
banned_messages = load_data(BANNED_MESSAGES_DB)
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
            'notification': True,
            'deletemat': False
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
    