from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from ruSpamLib import is_spam
from database_utils import add_chat, get_chat_settings
from aiogram.filters import Command
from text_content import get_start_text, get_info_text, get_help_text
from keyboard_utils import get_ban_keyboard
import json
import os

# Load data files
LOG_CHANNELS_DB = "log_channels.json"
MODELS_DB = "models.json"
THRESHOLDS_DB = "thresholds.json"
USER_MESSAGES_DB = "user_messages.json"

SPECIAL_USER_IDS = [7264930816, 1529997307]

def load_data(db_file):
    if os.path.exists(db_file):
        with open(db_file, "r") as file:
            return json.load(file)
    return {}

def save_data(db_file, data):
    with open(db_file, "w") as file:
        json.dump(data, file)

log_channels = load_data(LOG_CHANNELS_DB)
models = load_data(MODELS_DB)
thresholds = load_data(THRESHOLDS_DB)
user_messages = load_data(USER_MESSAGES_DB)

async def has_permission(message: Message) -> bool:
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return (message.from_user.id in SPECIAL_USER_IDS) or (member.is_chat_admin() or member.is_chat_creator())

def setup_handlers(dp: Dispatcher, bot, Session, start_text, info_text, help_text):
    @dp.message(lambda message: message.new_chat_members)
    async def on_new_chat_members(message: Message):
        for new_member in message.new_chat_members:
            if new_member.id == bot.id:
                chat_id = message.chat.id
                chat_name = message.chat.title
                await initialize_chat_settings(chat_id, chat_name)

    async def initialize_chat_settings(chat_id, chat_name):
        add_chat(
            chat_id=chat_id,
            name=chat_name,
            subscribe=False,
            mute=False,
            delete_message=True,
            ban=False,
            notification=True
        )

    @dp.message(Command('start'))
    async def process_start_command(message: Message):
        start_message = await message.answer(start_text, parse_mode='html')
        dp['start_message_id'] = start_message.message_id

    @dp.message(Command('info'))
    async def process_info_command(message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        if not await has_permission(message):
            await message.reply("Только администратор или пользователь с особыми правами может установить лог-канал.")
            return

        log_channel_id = log_channels.get(str(chat_id), "Не установлен")
        model_name = models.get(str(chat_id), "spamNS_large_v1")
        threshold = thresholds.get(str(chat_id), 10)

        info_text = (
            f"<b>Настройки для группы:</b> {message.chat.title}\n\n"
            f"<b>Лог-канал:</b> {log_channel_id}\n"
            f"<b>Модель классификации:</b> {model_name}\n"
            f"<b>Порог сообщений:</b> {threshold}\n"
        )
        await message.reply(info_text, parse_mode='html')

    @dp.message(Command('help'))
    async def process_help_command(message: Message):
        await message.answer(help_text, parse_mode='html')

    @dp.message(Command('setlog'))
    async def process_setlog_command(message: Message):
        if not message.chat.type in ['group', 'supergroup']:
            await message.reply("Эту команду можно использовать только в группе или супер-группе.")
            return

        if not await has_permission(message):
            await message.reply("Только администратор или пользователь с особыми правами может установить лог-канал.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Использование команды: /setlog <channel_id>")
            return

        log_channel_id = parts[1]
        log_channels[str(chat_id)] = log_channel_id
        save_data(LOG_CHANNELS_DB, log_channels)
        await message.reply(f"Лог-канал успешно установлен: {log_channel_id}")

    @dp.message(Command('setmodel'))
    async def process_setmodel_command(message: Message):
        if not message.chat.type in ['group', 'supergroup']:
            await message.reply("Эту команду можно использовать только в группе или супер-группе.")
            return

        if not await has_permission(message):
            await message.reply("Только администратор или пользователь с особыми правами может установить модель классификации.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Использование команды: /setmodel <model_name>")
            return

        model_name = parts[1]
        models[str(chat_id)] = model_name
        save_data(MODELS_DB, models)
        await message.reply(f"Модель классификации успешно установлена: {model_name}")

    @dp.message(Command('setthreshold'))
    async def process_setthreshold_command(message: Message):
        if not message.chat.type in ['group', 'supergroup']:
            await message.reply("Эту команду можно использовать только в группе или супер-группе.")
            return

        if not await has_permission(message):
            await message.reply("Только администратор или пользователь с особыми правами может установить порог сообщений.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            await message.reply("Использование команды: /setthreshold <threshold>")
            return

        threshold = int(parts[1])
        thresholds[str(chat_id)] = threshold
        save_data(THRESHOLDS_DB, thresholds)
        await message.reply(f"Порог сообщений успешно установлен: {threshold}")

    @dp.callback_query()
    async def process_callback_query(callback_query: CallbackQuery):
        start_message_id = dp.get('start_message_id')
        data = callback_query.data
        user_id = callback_query.from_user.id
        chat_id = callback_query.message.chat.id

        if data == 'button':
            await bot.delete_message(chat_id=user_id, message_id=start_message_id)
            await bot.send_message(user_id, "<b>Админ панель👀</b>\n\nСейчас админ панель только в разработке...", parse_mode='html')

        elif data.startswith('ban_'):
            target_user_id, target_chat_id = map(int, data.split('_')[1:])
            try:
                await bot.ban_chat_member(chat_id=target_chat_id, user_id=target_user_id)
                message_text = callback_query.message.text or "Сообщение было удалено или недоступно"
                ban_message = f"✅ Пользователь {target_user_id} забанен\n\n"
                ban_message += f"Забанил: {callback_query.from_user.full_name} (@{callback_query.from_user.username})\n"
                ban_message += f"{message_text}"
                await bot.edit_message_text(
                    text=ban_message,
                    chat_id=chat_id,
                    message_id=callback_query.message.message_id
                )
                await bot.answer_callback_query(callback_query.id, text="Пользователь успешно забанен")
            except Exception as e:
                await bot.answer_callback_query(callback_query.id, text=f"Ошибка при бане: {type(e).__name__}, {str(e)}")

    @dp.message()
    async def process_message(message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        model_name = models.get(str(chat_id), "spamNS_large_v1")
        threshold = thresholds.get(str(chat_id), 10)

        if str(chat_id) not in user_messages:
            user_messages[str(chat_id)] = {}
        if str(user_id) not in user_messages[str(chat_id)]:
            user_messages[str(chat_id)][str(user_id)] = 0
        user_messages[str(chat_id)][str(user_id)] += 1
        save_data(USER_MESSAGES_DB, user_messages)

        if user_messages[str(chat_id)][str(user_id)] > threshold:
            return

        chat_settings = await get_chat_settings(chat_id)

        if chat_settings is None:
            await message.answer("Ошибка получения настроек чата.")
            return

        pred_average = is_spam(message.text, model_name="spamNS_large_v2")
        if pred_average:
            if chat_settings.delete_message:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            
            if chat_settings.ban:
                await bot.ban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

            if chat_settings.mute:
                await bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.from_user.id, can_send_messages=False)

            if chat_settings.notification:
                log_channel_id = log_channels.get(str(message.chat.id))
                if log_channel_id:
                    keyboard = get_ban_keyboard(message.from_user.id, message.chat.id)
                    await bot.send_message(log_channel_id, f"Сообщение от @{message.from_user.username} удалено в {message.chat.title}:\n\n{message.text}", reply_markup=keyboard)
