import json
from utils import *
from aiogram import Dispatcher, types
from aiogram.types import Message, CallbackQuery
from AntiMat import filter_text
from ruSpamLib import is_spam
from aiogram.types import Message, InputFile
from io import BytesIO
from aiogram import Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import psutil
from ping3 import ping
from keyboard_utils import get_ban_keyboard

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
                await message.reply(f"⚠️ Внимание! Пользователь с ID {new_member.id} присоединился к группе. Это потенциальный спаммер из нашей базы данных!")

    @dp.message_handler(commands=['dump_data'])
    async def dump_data_command(message: Message):
        user_id = message.from_user.id
        if user_id not in SPECIAL_USER_IDS:
            await message.reply("Эта команда доступна только для администратора.")
            return

        data = {
            "log_channels": load_data(LOG_CHANNELS_DB),
            "thresholds": load_data(THRESHOLDS_DB),
            "user_messages": load_data(USER_MESSAGES_DB),
            "banned_messages": load_data(BANNED_MESSAGES_DB),
            "chat_settings": load_data(CHAT_SETTINGS_DB)
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

    @dp.message_handler(commands=['info'])
    async def process_info_command(message: Message):
        chat_id = message.chat.id

        if not await has_permission(message):
            await message.reply_video(video=open('./video/reverse-flash-cw.mp4', 'rb'))        
            await message.reply("Только администратор или пользователь с особыми правами может получить эту информацию.")
            return

        log_channel_id = log_channels.get(str(chat_id), "Не установлено")
        threshold = thresholds.get(str(chat_id), 10)

        chat_settings = load_chat_settings().get(str(chat_id), {})

        subscribe_status = "Включено" if chat_settings.get('subscribe', False) else "Выключено"
        mute_status = "Включено" if chat_settings.get('mute', False) else "Выключено"
        delete_message_status = "Включено" if chat_settings.get('delete_message', False) else "Выключено"
        ban_status = "Включено" if chat_settings.get('ban', False) else "Выключено"
        notification_status = "Включено" if chat_settings.get('notification', False) else "Выключено"
        matdelete = "Включено" if chat_settings.get('deletemat', False) else "Выключено"

        info_text = (
            f"<b>Настройки для группы:</b> {message.chat.title}\n\n"
            f"<b>Канал логов:</b> {log_channel_id} 📡\n"
            f"<b>Порог сообщений:</b> {threshold} ✉️\n\n"
            f"<b>Настройки действий:</b>\n"
            f"Подписка на уведомления: {subscribe_status} 🔔\n"
            f"Замутить пользователей: {mute_status} 🤐\n"
            f"Удалить сообщения: {delete_message_status} 🗑️\n"
            f"Забанить пользователей: {ban_status} 🚫\n"
            f"Уведомления: {notification_status} 📢\n"
            f"Удалить нецензурную лексику: {matdelete} 📢\n\n"
            f"<i>Первая версия: Lost Samurai 0.4</i>"
        )
        await message.reply(info_text, parse_mode='html', reply_markup=settings_keyboard(chat_id))

    def settings_keyboard(chat_id):
        chat_settings = load_chat_settings().get(str(chat_id), {})
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                text=f"🔒 Забанить: {'✅' if chat_settings.get('ban', False) else '❌'}",
                callback_data='toggle_ban_user'
            ),
            types.InlineKeyboardButton(
                text=f"🔇 Замутить: {'✅' if chat_settings.get('mute', False) else '❌'}",
                callback_data='toggle_mute_user'
            ),
            types.InlineKeyboardButton(
                text=f"📩 Уведомления: {'✅' if chat_settings.get('notification', False) else '❌'}",
                callback_data='toggle_notify_admin'
            ),
            types.InlineKeyboardButton(
                text=f"🗑 Удалить сообщения: {'✅' if chat_settings.get('delete_message', False) else '❌'}",
                callback_data='toggle_delete_message'
            ),
            types.InlineKeyboardButton(
                text=f"🗑 Удалить нецензурную лексику: {'✅' if chat_settings.get('deletemat', False) else '❌'}",
                callback_data='toggle_deletemat'  
            )
        )
        return keyboard

    @dp.message_handler(commands=['help'])
    async def process_help_command(message: Message):
        await message.answer(help_text, parse_mode='html')

    @dp.message_handler(commands=['setlog'])
    async def process_setlog_command(message: Message):
        await is_group(message)
        if not await has_permission(message):
            await message.reply_video(video=open('./video/reverse-flash-cw.mp4', 'rb'))
            await message.reply("Только администратор или пользователь с особыми правами может установить канал логов.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Использование: /setlog <id_канала>")
            return

        log_channel_id = parts[1]
        log_channels[str(chat_id)] = log_channel_id
        save_data(LOG_CHANNELS_DB, log_channels)
        await message.reply(f"Канал логов успешно установлен: {log_channel_id}")

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

    @dp.message_handler(commands=['ping'])
    async def ping_handler(message: types.Message):
        ping_result = ping('google.com')
        ping_time = f"{ping_result * 1000:.2f} мс" if ping_result is not None else "Ошибка пинга"

        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')

        response = (
            f"**Статус сервера:**\n"
            f"- **Пинг:** {ping_time} мс 🕒\n"
            f"- **Загрузка CPU:** {cpu_usage}% 🖥️\n"
            f"- **Использование памяти:** {memory_info.percent}% из {memory_info.total // (1024 ** 2)} МБ 🧠\n"
            f"- **Использование диска:** {disk_info.percent}% из {disk_info.total // (1024 ** 3)} ГБ 💾\n"
            f"- **Доступная память:** {memory_info.available // (1024 ** 2)} МБ 📦\n"
            f"- **Доступное место на диске:** {disk_info.free // (1024 ** 3)} ГБ 🗄️"
        )
        await message.reply(response, parse_mode='Markdown')

    @dp.message_handler(commands=['setthreshold'])
    async def process_setthreshold_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply_video(video=open('./video/reverse-flash-cw.mp4', 'rb'))
            await message.reply(
                "Только администратор или пользователь с особыми правами может установить порог сообщений."
            )
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            await message.reply("Использование: /setthreshold <порог>")
            return

        threshold = int(parts[1])
        thresholds[str(chat_id)] = threshold
        save_data(THRESHOLDS_DB, thresholds)
        await message.reply(f"Порог сообщений успешно установлен: {threshold}")

    @dp.message_handler(commands=['prof'])
    async def handle_prof_command(message: types.Message):
        argument = message.get_args()
        if argument:
            if '**' in filter_text(argument):
                await message.reply('❌ Обнаружена нецензурная лексика в тексте!')
            else:
                is_spam_result, confidence = is_spam(message=message.text, model_name="spamNS_v6", multi_model=False)
                if is_spam_result:
                    await message.reply(f'❌ Обнаружена реклама! Уверенность: {confidence:.2f}')

                else:
                    await message.reply('✅ Текст не содержит нецензурной лексики или рекламы.')
        else:
            await message.reply('❌ Пожалуйста, введите текст для проверки.')

    
    @dp.callback_query_handler()
    async def process_callback_query(callback_query: CallbackQuery):
        data = callback_query.data
        user_id = callback_query.from_user.id
        chat_id = callback_query.message.chat.id

        if data.startswith('ban_'):
            target_user_id, target_chat_id = map(int, data.split('_')[1:])
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
            with open(WRONG_MESSAGES, 'r') as file:
                wrong_messages = json.load(file)

            wrong_messages.append({"user_id": user_id, "chat_id": chat_id, "message": callback_query.message.text})

            with open(WRONG_MESSAGES, 'w') as file:
                json.dump(wrong_messages, file, ensure_ascii=False, indent=4)

            await bot.send_message(chat_id=-1002348384690, text=f"Неправильно определённое сообщение:\n\n{callback_query.message.text}")
            await bot.edit_message_text(text="Спасибо за обратную связь! Это поможет нам улучшить наши модели!",
                                        chat_id=chat_id, message_id=callback_query.message.message_id)
            
    
    @dp.message_handler()
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

        chat_settings = load_chat_settings().get(str(chat_id), {})

        pred_average, confidence = is_spam(message.text, model_name="spamNS_v6")
        
        filtered_message_text = filter_text(message.text)

        if (pred_average and user_messages[str(chat_id)][str(user_id)] < threshold) or (message.text != filtered_message_text and chat_settings.get('deletemat', False)):
            

            if chat_settings.get('delete_message', True):
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

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

            if chat_settings.get('notification', True):
                log_channel_id = log_channels.get(str(message.chat.id))

                if log_channel_id:
                    keyboard = get_ban_keyboard(message.from_user.id, message.chat.id)
                    await bot.send_message(
                        log_channel_id,
                        f"Сообщение от @{message.from_user.username} удалено в {message.chat.title}:\n\n{filtered_message_text}, вероятность модели: {confidence}",
                        reply_markup=keyboard
                    )
                    if pred_average:
                        message_text = f"💬 Сообщение удалено за рекламу от @{message.from_user.username or message.from_user.id}! 🚫 Вероятность: {confidence}"
                    else:
                        message_text = f"💬 Сообщение удалено за нецензурную лексику от @{message.from_user.username or message.from_user.id}!"

                    await bot.send_message(
                        chat_id,
                        message_text
                    )