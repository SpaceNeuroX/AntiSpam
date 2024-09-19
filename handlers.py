import json
import os
from aiogram import Dispatcher, types
from aiogram.types import Message, CallbackQuery
from ruSpamLib import is_spam
from aiogram.filters import Command
from keyboard_utils import get_ban_keyboard

LOG_CHANNELS_DB = "./log_channels.json"
THRESHOLDS_DB = "./thresholds.json"
USER_MESSAGES_DB = "./user_messages.json"
WRONG_MESSAGES = "./wrong_messages.json"
BANNED_MESSAGES_DB = "./banned_messages.json"
CHAT_SETTINGS_DB = "./chat_settings.json"
BANLIST_DB = "./banlist.json"

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

async def has_permission(message: types.Message) -> bool:
    chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return chat_member.status in ["creator", "administrator"]

async def is_group(message: Message):
    if not message.chat.type in ['group', 'supergroup']:
        await message.reply("Эту команду можно использовать только в группе или супер-группе.")
        return

def setup_handlers(dp: Dispatcher, bot, start_text, help_text):
    @dp.message(lambda message: message.new_chat_members)
    async def on_new_chat_members(message: Message):
        for new_member in message.new_chat_members:
            if new_member.id == bot.id:
                chat_id = message.chat.id
                await initialize_chat_settings(chat_id)
            elif new_member.id in banlist:
                chat_id = message.chat.id
                await message.reply(f"🚨 Внимание! Пользователь с ID {new_member.id} присоединился к группе. Это возможный спамер из нашей базы данных!")

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

    @dp.message(Command('start'))
    async def process_start_command(message: Message):
        start_message = await message.answer(start_text, parse_mode='html')
        dp['start_message_id'] = start_message.message_id

    @dp.message(Command('info'))
    async def process_info_command(message: Message):
        chat_id = message.chat.id

        if not await has_permission(message):
            await message.reply("Только администратор или пользователь с особыми правами может получить информацию.")
            return

        log_channel_id = log_channels.get(str(chat_id), "Не установлен")
        threshold = thresholds.get(str(chat_id), 10)

        chat_settings = load_chat_settings().get(str(chat_id), {})

        subscribe_status = "Включена" if chat_settings.get('subscribe', False) else "Отключена"
        mute_status = "Включен" if chat_settings.get('mute', False) else "Отключен"
        delete_message_status = "Включено" if chat_settings.get('delete_message', False) else "Отключено"
        ban_status = "Включен" if chat_settings.get('ban', False) else "Отключен"
        notification_status = "Включены" if chat_settings.get('notification', False) else "Отключены"

        info_text = (
            f"<b>Настройки для группы:</b> {message.chat.title}\n\n"
            f"<b>Лог-канал:</b> {log_channel_id}\n"
            f"<b>Порог сообщений:</b> {threshold}\n\n"
            f"<b>Настройки действий:</b>\n"
            f"Подписка на уведомления: {subscribe_status}\n"
            f"Мутирование пользователей: {mute_status}\n"
            f"Удаление сообщений: {delete_message_status}\n"
            f"Бан пользователей: {ban_status}\n"
            f"Уведомления: {notification_status}\n"
        )
        await message.reply(info_text, parse_mode='html')

    @dp.message(Command('help'))
    async def process_help_command(message: Message):
        await message.answer(help_text, parse_mode='html')

    @dp.message(Command('setlog'))
    async def process_setlog_command(message: Message):
        await is_group(message)
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

    @dp.message(Command('setthreshold'))
    async def process_setthreshold_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply(
                "Только администратор или пользователь с особыми правами может установить порог сообщений.")
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

    @dp.message(Command('setmute'))
    async def process_setmute_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply("Только администратор или пользователь с особыми правами может изменить настройки.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Использование команды: /setmute <True/False>")
            return

        mute = parts[1].lower() == 'true'
        chat_settings = load_chat_settings()
        if str(chat_id) not in chat_settings:
            chat_settings[str(chat_id)] = {}
        chat_settings[str(chat_id)]['mute'] = mute
        save_chat_settings(chat_settings)
        await message.reply(f"Мутирование пользователей успешно {'включено' if mute else 'отключено'}.")

    @dp.message(Command('setdeletemessage'))
    async def process_setdeletemessage_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply("Только администратор или пользователь с особыми правами может изменить настройки.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Использование команды: /setdeletemessage <True/False>")
            return

        delete_message = parts[1].lower() == 'true'
        chat_settings = load_chat_settings()
        if str(chat_id) not in chat_settings:
            chat_settings[str(chat_id)] = {}
        chat_settings[str(chat_id)]['delete_message'] = delete_message
        save_chat_settings(chat_settings)
        await message.reply(f"Удаление сообщений успешно {'включено' if delete_message else 'отключено'}.")

    @dp.message(Command('setban'))
    async def process_setban_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply("Только администратор или пользователь с особыми правами может изменить настройки.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Использование команды: /setban <True/False>")
            return

        ban = parts[1].lower() == 'true'
        chat_settings = load_chat_settings()
        if str(chat_id) not in chat_settings:
            chat_settings[str(chat_id)] = {}
        chat_settings[str(chat_id)]['ban'] = ban
        save_chat_settings(chat_settings)
        await message.reply(f"Бан пользователей успешно {'включен' if ban else 'отключен'}.")

    @dp.message(Command('setnotification'))
    async def process_setnotification_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply("Только администратор или пользователь с особыми правами может изменить настройки.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Использование команды: /setnotification <True/False>")
            return

        notification = parts[1].lower() == 'true'
        chat_settings = load_chat_settings()
        if str(chat_id) not in chat_settings:
            chat_settings[str(chat_id)] = {}
        chat_settings[str(chat_id)]['notification'] = notification
        save_chat_settings(chat_settings)
        await message.reply(f"Уведомления успешно {'включены' if notification else 'отключены'}.")

    @dp.callback_query()
    async def process_callback_query(callback_query: CallbackQuery):
        start_message_id = dp.get('start_message_id')
        data = callback_query.data
        user_id = callback_query.from_user.id
        chat_id = callback_query.message.chat.id

        if data.startswith('ban_'):
            target_user_id, target_chat_id = map(int, data.split('_')[1:])

            if callback_query.from_user.id == 1529997307:
                await bot.answer_callback_query(
                    callback_query.id,
                    text="Вы заблокированы владельцем и не можете выполнять эту операцию."
                )
                return

            try:
                chat_member = await bot.get_chat_member(chat_id=target_chat_id, user_id=target_user_id)
                if chat_member.status in ['administrator', 'creator']:
                    await bot.answer_callback_query(
                        callback_query.id,
                        text="Нельзя забанить администратора или владельца чата."
                    )
                    return
                
                banlist = load_data(BANLIST_DB)
                if target_user_id not in banlist:
                    banlist.append(target_user_id)
                    save_data(BANLIST_DB, banlist)

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

                banned_messages = load_data(BANNED_MESSAGES_DB)
                banned_messages.append({
                    "user_id": target_user_id,
                    "chat_id": target_chat_id,
                    "message": message_text
                })
                save_data(BANNED_MESSAGES_DB, banned_messages)

            except Exception as e:
                await bot.answer_callback_query(callback_query.id,
                                                text=f"Ошибка при бане: {type(e).__name__}, {str(e)}")

        elif data.startswith("incorrect_"):
            with open(WRONG_MESSAGES, 'r') as file:
                wrong_messages = json.load(file)

            wrong_messages.append({"user_id": user_id, "chat_id": chat_id, "message": callback_query.message.text})

            with open(WRONG_MESSAGES, 'w') as file:
                json.dump(wrong_messages, file, ensure_ascii=False, indent=4)

            await bot.send_message(chat_id=-1002348384690, text=f"Неправильно определенное сообщение:\n\n{callback_query.message.text}")
            await bot.edit_message_text(text="Спасибо за отклик! Это поможет нам делать более качественные модели!",
                                        chat_id=chat_id, message_id=callback_query.message.message_id)


    @dp.message()
    async def process_message(message: Message):
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

        if user_messages[str(chat_id)][str(user_id)] > threshold:
            return

        chat_settings = load_chat_settings().get(str(chat_id), {})

        pred_average = is_spam(message.text, model_name="spamNS_v6")

        if pred_average:
            if chat_settings.get('delete_message',True):
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

            if chat_settings.get('ban', False):
                await bot.ban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

            if chat_settings.get('mute', False):
                await bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.from_user.id,
                                               can_send_messages=False)

            if chat_settings.get('notification', True):
                log_channel_id = log_channels.get(str(message.chat.id))

                if log_channel_id:
                    keyboard = get_ban_keyboard(message.from_user.id, message.chat.id)
                    await bot.send_message(log_channel_id,
                                           f"Сообщение от @{message.from_user.username} удалено в {message.chat.title}:\n\n{message.text}",
                                           reply_markup=keyboard)
                    await bot.send_message(
                        chat_id,
                        f"💬 Сообщение от @{message.from_user.username} было удалено за рекламу! 🚫\n"
                        "Если существует лог-канал, модераторы уже получили это сообщение на проверку. 👮♂️\n\n"
                        "⚠️ **Напоминаем:**\n"
                        "❌ Пожалуйста, не размещайте рекламные сообщения, чтобы избежать блокировки!"
                    )


