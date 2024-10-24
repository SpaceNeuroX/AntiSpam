import json
from utils import *
from aiogram import Dispatcher, types
import aiohttp
from aiogram.types import Message, CallbackQuery
from ruSpamLib import is_spam
import platform
import sys
from keyboard_utils import settings_keyboard
from aiogram.types import Message, InputFile
from io import BytesIO
from aiogram import Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import psutil
from ping3 import ping
from keyboard_utils import get_ban_keyboard
import logging
from logging.handlers import RotatingFileHandler
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

original_messages = {}

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = RotatingFileHandler('bot_actions.log', maxBytes=1024*1024, backupCount=5, encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

sys.stdout.reconfigure(encoding='utf-8')

logger.info("Logging configured successfully with UTF-8 support!")
storage = MemoryStorage()

async def has_permission(message: types.Message) -> bool:
    user_id = message.from_user.id
    chat_member = await message.bot.get_chat_member(message.chat.id, user_id)
    return chat_member.status in ["creator", "administrator"]

async def is_group(message: Message):
    if not message.chat.type in ['group', 'supergroup']:
        await message.reply("Эта команда может использоваться только в группе или супергруппе.")
        return

def setup_handlers(dp: Dispatcher, bot, start_text, help_text):
    @dp.message_handler(lambda message: message.new_chat_members)
    async def on_new_chat_members(message: Message):
        for new_member in message.new_chat_members:
            if new_member.id == bot.id:
                chat_id = message.chat.id
                await initialize_chat_settings(chat_id)
            elif new_member.id in banlist:
                chat_id = message.chat.id
                await message.reply(f"⚠️ Внимание! Пользователь с ID {new_member.id} присоединился к группе. Он находиться в базе данных нежелательных рекламщиков!")

    @dp.message_handler(commands=['send_logs'], is_admin = True)
    async def send_logs_command(message: Message):
        user_id = message.from_user.id
        if user_id in SPECIAL_USER_IDS:
            with open('bot_actions.log', 'rb') as file:
                await message.reply_document(InputFile(file, filename='bot_actions.log'))
            logger.info(f"Файл логов отправлен пользователю с ID {user_id}")
        else:
            await message.reply("Только администратор может получить файл логов.")
            

    @dp.message_handler(commands=['dump_data'], is_admin = True)
    async def dump_data_command(message: Message):
        user_id = message.from_user.id
        if user_id not in SPECIAL_USER_IDS:
            await message.reply("Эта команда доступна только для администратора.")
            return

        data = {
            "thresholds": load_data(THRESHOLDS_DB),
            "user_messages": load_data(USER_MESSAGES_DB),
            "chat_settings": load_data(CHAT_SETTINGS_DB),
            "wrong_messages": load_data(WRONG_MESSAGES)
        }

        formatted_data = json.dumps(data, ensure_ascii=False, indent=4)

        file_buffer = BytesIO()
        file_buffer.write(formatted_data.encode('utf-8'))
        file_buffer.seek(0)

        await message.reply_document(InputFile(file_buffer, filename="dump_data.json"))

    @dp.message_handler(commands=['start'])
    async def process_start_command(message: Message):
        start_message = await message.answer(start_text, parse_mode='html')
        dp['start_message_id'] = start_message.message_id

    @dp.message_handler(commands=['info'], is_admin = True)
    async def process_info_command(message: Message):
        chat_id = message.chat.id
        threshold = thresholds.get(str(chat_id), 10)

        chat_settings = load_chat_settings().get(str(chat_id), {})

        mute_status = "Включено" if chat_settings.get('mute', False) else "Выключено"
        delete_message_status = "Включено" if chat_settings.get('delete_message', False) else "Выключено"
        ban_status = "Включено" if chat_settings.get('ban', True) else "Выключено"

        info_text = (
            f"<b>Настройки для группы:</b> {message.chat.title}\n\n"
            f"<b>Порог сообщений:</b> {threshold} ✉️\n\n"
            f"<b>Настройки действий:</b>\n"
            f"Замутить пользователей: {mute_status} 🤐\n"
            f"Удалить сообщения: {delete_message_status} 🗑️\n"
            f"Забанить пользователей: {ban_status} 🚫\n"
            f"<i>Версия: Lost Samurai 0.5</i>"
        )
        await message.reply(info_text, parse_mode='html', reply_markup=settings_keyboard(chat_id))

    @dp.message_handler(commands=['help'])
    async def process_help_command(message: Message):
        await message.answer(help_text, parse_mode='html')

    @dp.message_handler(commands=['me'])
    async def process_me_command(message: Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if str(chat_id) not in user_messages or str(user_id) not in user_messages[str(chat_id)]:
            await message.reply("Вы ещё не отправляли сообщений в этом чате. 😢")
            return
        
        message_count = user_messages[str(chat_id)][str(user_id)]
        rank = get_user_rank(message_count)
        
        if message.from_user.is_bot:
            rank = "Бот 🤖"
        elif await has_permission(message):
            rank = "Правитель 👑"
        
        await message.reply(f"Пользователь: {message.from_user.full_name}\n"
                            f"ID: {user_id} 🔢\n"
                            f"Количество сообщений: {message_count} 💬\n"
                            f"Ранг: {rank}")

    @dp.message_handler(commands=['status'], is_admin = True)
    async def ping_handler(message: types.Message):
        google_ping_result = ping('google.com')
        telegram_ping_result = ping('149.154.167.40')
        
        google_ping_time = f"{google_ping_result * 1000:.2f} мс" if google_ping_result is not None else "Ошибка пинга"
        telegram_ping_time = f"{telegram_ping_result * 1000:.2f} мс" if telegram_ping_result is not None else "Ошибка пинга"

        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')

        system_info = platform.uname()
        python_version = platform.python_version()
        num_cores = psutil.cpu_count(logical=True)
        uptime = os.popen('uptime -p').read().strip()

        battery = psutil.sensors_battery()
        
        if battery is not None:
            battery_status = battery.percent  
            battery_power_plugged = "Да" if battery.power_plugged else "Нет"
        else:
            battery_status = "Нет информации о батарее"
            battery_power_plugged = "N/A"

        response = (
            f"Статус сервера:\n"
            f"- Пинг до Google: {google_ping_time} 🕒\n"
            f"- Пинг до Telegram: {telegram_ping_time} 🕒\n"
            f"- Загрузка CPU: {cpu_usage}% 🖥️\n"
            f"- Использование памяти: {memory_info.percent}% из {memory_info.total // (1024 ** 2)} МБ 🧠\n"
            f"- Использование диска: {disk_info.percent}% из {disk_info.total // (1024 ** 3)} ГБ 💾\n"
            f"- Доступная память: {memory_info.available // (1024 ** 2)} МБ 📦\n"
            f"- Доступное место на диске: {disk_info.free // (1024 ** 3)} ГБ 🗄️\n"
            f"- Система: {system_info.system} {system_info.release} ({system_info.machine})\n"
            f"- Python версия: {python_version} 🐍\n"
            f"- Количество ядер CPU: {num_cores} 🖥️\n"
            f"- Время работы сервера: {uptime} ⏱️\n"
            f"- Заряд батареи: {battery_status}% 🔋\n"
            f"- Зарядка: {battery_power_plugged} 🔌"
        )

        await message.reply(response, parse_mode='Markdown')
    
    #@dp.message_handler(content_types=["new_chat_members"]) 
    #async def delete_new_chat_member_message(message: types.Message):
    # await bot.delete_message(message.chat.id, message.message_id)
    # print("удалено")


    @dp.message_handler(commands=['checkban'])
    async def check_ban_command(message: Message):
        args = message.get_args()

        if not args:
            await message.reply("Пожалуйста, укажите идентификатор пользователя после команды.")
            return

        user_id_to_check = args.strip()

        try:
            user_id_to_check_int = int(user_id_to_check)
        except ValueError:
            await message.reply("Идентификатор пользователя должен быть числом.")
            return

        if user_id_to_check_int in banlist:
            await message.reply(f"❌ Пользователь с ID {user_id_to_check} находится в списке спамеров!.")
        else:
            await message.reply(f"✅ Пользователь с ID {user_id_to_check} не находится в списке спамеров.")


    @dp.message_handler(commands=['updatebanlist'], is_admin = True)
    async def update_banlist_command(message: Message):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://lols.bot/spam/banlist.json') as resp:
                    if resp.status == 200:
                        banlist_data = await resp.json()
                        with open(BANLIST_DB, 'w') as f:
                            json.dump(banlist_data, f)
                        await message.reply("Список банов успешно обновлен.")
                        print("Процесс обновления списка банов завершен.")
                    else:
                        await message.reply("Не удалось получить список банов. Проверьте URL-адрес.")
        except aiohttp.ClientError as e:
            await message.reply("Произошла ошибка при обновлении списка банов.")
            print(f"Ошибка при обновлении списка банов: {e}")
            
    @dp.message_handler(commands=['setthreshold'], is_admin = True)
    async def process_setthreshold_command(message: Message):
        await is_group(message)

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            await message.reply("Использование: /setthreshold <порог>")
            return

        threshold = int(parts[1])
        thresholds[str(chat_id)] = threshold
        save_data(THRESHOLDS_DB, thresholds)
        await message.reply(f"Порог сообщений успешно установлен: {threshold}")

    @dp.message_handler(commands=['prof'], is_admin=True)
    async def handle_prof_command(message: types.Message):
        argument = message.get_args()
        if argument:
            text_to_check = message.text[len(message.text.split()[0]) + 1:]

            loading_message = await message.reply('⏳ Проверка текста...')

            is_spam_result, confidence = is_spam(message=text_to_check, model_name="spamNS_v6", multi_model=False)

            await loading_message.delete()

            if is_spam_result:
                await message.reply(f'❌ Обнаружена реклама! Уверенность: {confidence:.2f}')
            else:
                await message.reply('✅ Текст не содержит рекламы.')
        else:
            await message.reply('❌ Пожалуйста, введите текст для проверки.')


    @dp.message_handler(commands=['ban'], is_admin=True)
    async def ban_user(message: types.Message):
        if not message.reply_to_message:
            await message.reply("Команда должна быть ответом на сообщение.")
            return
        
        user_to_ban = message.reply_to_message.from_user
        try:
            await message.chat.kick(user_to_ban.id)
            await message.reply(f"Пользователь {user_to_ban.full_name} был забанен.")
        except Exception as e:
            await message.reply(f"Не удалось забанить пользователя. Ошибка: {e}")


    # @dp.message_handler(commands=['update_bot'])
    # async def process_update_bot_command(message: Message):
    #    await update_bot_command(message)

    @dp.callback_query_handler()
    async def process_callback_query(callback_query: CallbackQuery):
        data = callback_query.data

        user_id = callback_query.from_user.id
        chat_id = callback_query.message.chat.id

        chat_member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                
        if data.startswith('ban_'):
            target_user_id, target_chat_id = map(int, data.split('_')[1:])
            if chat_member.status not in ['administrator', 'creator']:
                await bot.answer_callback_query(
                    callback_query.id,
                    text="Только админ может забанить!"
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
                
                await bot.delete_message(chat_id=chat_id, message_id=callback_query.message.message_id)
                await bot.answer_callback_query(callback_query.id, text="✅ Пользователь успешно забанен!", show_alert=True)

            except Exception as e:
                await bot.answer_callback_query(callback_query.id,
                                                text=f"Ошибка при бане: {type(e).__name__}, {str(e)}", show_alert=True)
        elif data.startswith('toggle_'):
            setting = data.split('_')[1]
            print(setting)
            if setting == "delete":
                setting = "delete_message"
            elif setting == "notify":
                setting = "notification"

            chat_settings = load_chat_settings()

            if str(chat_id) not in chat_settings:
                chat_settings[str(chat_id)] = {}

            admins = await bot.get_chat_administrators(chat_id)
            admin_ids = [admin.user.id for admin in admins]

            if callback_query.from_user.id not in admin_ids:
                await bot.answer_callback_query(callback_query.id, text="Вы не администратор, поэтому не можете изменять настройки.", show_alert=True)
                return

            current_value = chat_settings[str(chat_id)].get(setting, False)
            chat_settings[str(chat_id)][setting] = not current_value
            save_chat_settings(chat_settings)

            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                reply_markup=settings_keyboard(chat_id)
            )
            await bot.answer_callback_query(callback_query.id, text=f"Настройка '{setting}' изменена на {'✅' if not current_value else '❌'}", show_alert=True)

        elif data.startswith("incorrect_"):
            target_user_id, target_chat_id = map(int, data.split('_')[1:])
            chat_member = await bot.get_chat_member(chat_id=target_chat_id, user_id=target_user_id)
            if chat_member.status not in ['administrator', 'creator']:
                await bot.answer_callback_query(
                    callback_query.id,
                    text="Только админ может пометить сообщение!"
                )
                return
            
            with open(WRONG_MESSAGES, 'r', encoding='utf-8') as file:
                wrong_messages = json.load(file)

            wrong_messages.append({"user_id": user_id, "chat_id": chat_id, "message": callback_query.message.text})

            with open(WRONG_MESSAGES, 'w', encoding='utf-8') as file:
                json.dump(wrong_messages, file, ensure_ascii=False, indent=4)

            await bot.delete_message(chat_id=chat_id, message_id=callback_query.message.message_id)

    @dp.message_handler(commands=['setlog'], is_admin = True)
    async def log_channel(message: types.Message):
        log_id = message.text.split()[1]
        channel_name = message.chat.full_name
        add_log = add_log_channel(channel_name, log_id)
        if add_log == "log_id must be integer":
            await message.reply("Лог айди должен включать себя только цифры. Удостовертесь в правильности написания")
            return
        
        await message.reply(f"Лог канал установлен  {log_id}")
        add_log_channel(channel_name, log_id)
        
       


    @dp.message_handler(commands=['id'], is_admin = True)
    async def print_chat_id(message: types.Message):
        chat_id = message.chat.id
        await message.reply(text=f"{chat_id}")
       

    @dp.message_handler()
    async def process_message(message: types.Message):
        original_messages[message.message_id] = message.text
        await handle_message(message)

    async def getting_data_from_json_by_key_meaning(dp_name, key):
            data = load_data(dp_name)
            meaning = data[key]
            return meaning




    @dp.edited_message_handler()
    async def process_edited_message(message: Message):
        original_text = original_messages.get(message.message_id, "Оригинальный текст не найден")
        await handle_message(message, edited=True, original_text=original_text)

     




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

        url_pattern = re.compile(r"https?://\S+|www\.\S+")
        username_pattern = re.compile(r"@(\w+)")

        text_without_links_and_usernames = url_pattern.sub('', message.text).strip()
        text_without_links_and_usernames = username_pattern.sub('', text_without_links_and_usernames).strip()

        if username_pattern.fullmatch(message.text.strip()):
            return

        pred_average, confidence = is_spam(text_without_links_and_usernames, model_name="spamNS_v6")

        if pred_average and user_messages[str(chat_id)][str(user_id)] < threshold:
            keyboard = get_ban_keyboard(message.from_user.id, message.chat.id)

            if chat_settings.get('delete_message', False) and (not chat_settings.get('ban', True)) and (not chat_settings.get('mute', False)):
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

            log_id = await getting_data_from_json_by_key_meaning("log_channel.json", message.chat.full_name)
            try:
             if await has_permission(message) == False:
              if chat_settings.get('ban', True) and pred_average:
                print(log_id)
                
                await bot.send_message(chat_id=-1002266096303, text=f"[Лог] Пользователь @{message.from_user.username} ({message.from_user.id}) был забанен в {message.chat.title} за сообщение: <tg-spoiler>{message.text}</tg-spoiler>", parse_mode='html')
                await bot.send_message(chat_id=log_id, text=f"[Лог] Пользователь @{message.from_user.username} ({message.from_user.id}) был забанен в {message.chat.title} за сообщение: <tg-spoiler>{message.text}</tg-spoiler>", parse_mode='html')
                await bot.send_message(chat_id=message.chat.id, text=f"Заданный лог канал не найден\n<i>1. Убедитесь что в лог канале есть бот и  у него есть все нужные права.\n2. Убедитесь, что вы правильно задали chatID. Вы можете написать /id в лог чате, в ответ получите id.</i>\nНадеюсь вам это поможет!", parse_mode='html')
                
                await bot.ban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                


             if chat_settings.get('mute', False) and pred_average:
                await bot.send_message(chat_id=-1002266096303, text=f"[Лог] Пользователь @{message.from_user.username} ({message.from_user.id}) был замучен в {message.chat.title} за сообщение: <tg-spoiler>{message.text}</tg-spoiler>", parse_mode='html')
                await bot.send_message(chat_id=log_id, text=f"[Лог] Пользователь @{message.from_user.username} ({message.from_user.id}) был забанен в {message.chat.title} за сообщение: <tg-spoiler>{message.text}</tg-spoiler>", parse_mode='html')
                await bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.from_user.id, can_send_messages=False)
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            
             else:
                await bot.send_message(chat_id=log_id, text=f"[лог] Пользователь @{message.from_user.username} ({message.from_user.id}) является админом, но отправил спам сообщение: <tg-spoiler>{message.text}</tg-spoiler>", parse_mode='html')
                await bot.send_message(chat_id=-1002266096303, text=f"[лог] Пользователь @{message.from_user.username} ({message.from_user.id}) является админом, но отправил спам сообщение: <tg-spoiler>{message.text}</tg-spoiler>", parse_mode='html')

            except:
                 await bot.send_message(chat_id=message.chat.id, text=f"Заданный лог канал не найден\n<i>1. Убедитесь что в лог канале есть бот и  у него есть все нужные права.\n2. Убедитесь, что вы правильно задали chatID. Вы можете написать /id в лог чате, в ответ получите id.</i>\nНадеюсь вам это поможет!", parse_mode='html')