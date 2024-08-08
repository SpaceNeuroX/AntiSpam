from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from ruSpamLib import is_spam
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import json
import os

bot = Bot(token="7311526472:AAExrmlPJiDXVWZHHTtn1R9MazUURj1Tdfo")
dp = Dispatcher()

LOG_CHANNELS_DB = "home/log_channels.json"
MODELS_DB = "home/models.json"
THRESHOLDS_DB = "home/thresholds.json"
USER_MESSAGES_DB = "home/user_messages.json"

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

@dp.message(Command('start'))
async def process_start_command(message: Message):
    start_message = await message.answer(
        f'<b>Привет, {message.from_user.first_name}</b>\n\n'
        'Я бот для проверки спама. Просто пригласи меня в группу и я буду удалять все спам сообщения.\n\n'
        'Так же у меня есть админ панель, просто нажми на кнопку ниже и тебе откроются расширенные настройки.\n\n'
        'Удачного использования!\n\n'
        '<i>Админы: @FlorikX, @NeuroSpaceX</i>\n\n'
        'Для получения дополнительной информации используйте команду /help.',
        parse_mode='html'
    )
    dp['start_message_id'] = start_message.message_id

@dp.message(Command('info'))
async def process_info_command(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    member = await bot.get_chat_member(chat_id, user_id)
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
    help_text = (
        "<b>Информация о боте</b>\n\n"
        "Я бот для проверки спама. Просто пригласи меня в группу и я буду удалять все спам сообщения.\n\n"
        "<b>Команды:</b>\n"
        "/start - Запуск бота\n"
        "/setlog channel_id - Установить лог-канал. Использовать можно только в группе или супер-группе. Только администратор или "
        f"пользователь с ID {', '.join(map(str, SPECIAL_USER_IDS))} может установить лог-канал.\n"
        "/setmodel model_name - Установить модель классификации. Использовать можно только в группе или супер-группе. Только "
        f"администратор или пользователь с ID {', '.join(map(str, SPECIAL_USER_IDS))} может установить модель классификации.\n"
        "/setthreshold threshold - Установить порог сообщений. Использовать можно только в группе или супер-группе. Только "
        f"администратор или пользователь с ID {', '.join(map(str, SPECIAL_USER_IDS))} может установить порог сообщений.\n\n"
        "<b>Доступные модели:</b>\n"
        "1. spamNS_large_v1\n"
        "2. spamNS_tiny_v1\n"
        "3. spamNS_v1\n"
        "4. spamNS_large_v2\n\n"
        "Пока что доступны 4 модели. Укажите название модели без кавычек.\n\n"
        "<b>Разработчики:</b>\n"
        "Бот, нейросеть разработаны: @NeuroSpaceX\n"
        "Помощь в разработке: @FlorikX\n\n"
        "Все права защищены.\n\n"
        "<b>Служба поддержки:</b>\n"
        "totoshkus@gmail.com\n\n"
    )

    await message.answer(help_text, parse_mode='html')

async def has_permission(message: Message) -> bool:
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    return (message.from_user.id in SPECIAL_USER_IDS) or (member.is_chat_admin() or member.is_chat_creator())

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

@dp.message(Command('getdata'))
async def process_getdata_command(message: Message):
    if message.from_user.id not in SPECIAL_USER_IDS:
        await message.reply("У вас нет прав на выполнение этой команды.")
        return

    log_channels_data = json.dumps(log_channels, indent=4, ensure_ascii=False)
    models_data = json.dumps(models, indent=4, ensure_ascii=False)
    thresholds_data = json.dumps(thresholds, indent=4, ensure_ascii=False)
    user_messages_data = json.dumps(user_messages, indent=4, ensure_ascii=False)

    response_text = (
        f"<b>Данные лог-каналов:</b>\n<pre>{log_channels_data}</pre>\n\n"
        f"<b>Данные моделей:</b>\n<pre>{models_data}</pre>\n\n"
        f"<b>Данные порогов сообщений:</b>\n<pre>{thresholds_data}</pre>\n\n"
        f"<b>Данные сообщений пользователей:</b>\n<pre>{user_messages_data}</pre>"
    )

    await message.reply(response_text, parse_mode='html')

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
    if data == 'button':
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=start_message_id)
        await bot.send_message(callback_query.from_user.id, "<b>Админ панель👀</b>\n\nСейчас админ панель только в разработке...", parse_mode='html')

    if callback_query.data.startswith('ban_'):
        user_id, chat_id = map(int, callback_query.data.split('_')[1:])
        print(user_id, chat_id)
        try:
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await bot.send_message(callback_query.id, text="Пользователь успешно забанен")
            await bot.answer_callback_query(callback_query.id, text="Пользователь успешно забанен")
        except Exception as e:
            await bot.answer_callback_query(callback_query.id, text=f"Ошибка при бане: {type(e).__name__}, {str(e)}")

def get_ban_keyboard(user_id, chat_id):
    main_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text = "Забанить", callback_data=f"ban_{user_id}_{chat_id}")]
    ],)
    return main_kb

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

    pred_average = is_spam(message.text, model_name=model_name)

    if pred_average:
        await message.delete()

        log_channel_id = log_channels.get(str(message.chat.id))
        if log_channel_id:
            keyboard = get_ban_keyboard(message.from_user.id, message.chat.id,)  # Use the get_ban_keyboard function
            await bot.send_message(log_channel_id, f"Сообщение от @{message.from_user.username} удалено в {message.chat.title}:\n\n{message.text}", reply_markup=keyboard)

async def main() -> None:
    print("Starting... ")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
