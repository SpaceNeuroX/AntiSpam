import json
from utils import *
from aiogram import Dispatcher, types
from aiogram.types import Message, CallbackQuery
from AntiMat import filter_text
from ruSpamLib import is_spam
from keyboard_utils import get_ban_keyboard

async def has_permission(message: types.Message) -> bool:
    chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return chat_member.status in ["creator", "administrator"]

async def is_group(message: Message):
    if not message.chat.type in ['group', 'supergroup']:
        await message.reply("This command can only be used in a group or supergroup.")
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
                await message.reply(f"⚠️ Attention! User with ID {new_member.id} has joined the group. This is a potential spammer from our database!")

    @dp.message_handler(commands=['start'])
    async def process_start_command(message: Message):
        start_message = await message.answer(start_text, parse_mode='html')
        dp['start_message_id'] = start_message.message_id

    @dp.message_handler(commands= ['info'])
    async def process_info_command(message: Message):
        chat_id = message.chat.id

        if not await has_permission(message):
            await message.reply("Only an administrator or user with special permissions can access this information.")
            return

        log_channel_id = log_channels.get(str(chat_id), "Not set")
        threshold = thresholds.get(str(chat_id), 10)

        chat_settings = load_chat_settings().get(str(chat_id), {})

        subscribe_status = "Enabled" if chat_settings.get('subscribe', False) else "Disabled"
        mute_status = "Enabled" if chat_settings.get('mute', False) else "Disabled"
        delete_message_status = "Enabled" if chat_settings.get('delete_message', False) else "Disabled"
        ban_status = "Enabled" if chat_settings.get('ban', False) else "Disabled"
        notification_status = "Enabled" if chat_settings.get('notification', False) else "Disabled"
        matdelete = "Enabled" if chat_settings.get('deletemat', False) else "Disabled"

        info_text = (
            f"<b>Settings for group:</b> {message.chat.title}\n\n"
            f"<b>Log channel:</b> {log_channel_id} 📡\n"
            f"<b>Message threshold:</b> {threshold} ✉️\n\n"
            f"<b>Action settings:</b>\n"
            f"Subscribe to notifications: {subscribe_status} 🔔\n"
            f"Mute users: {mute_status} 🤐\n"
            f"Delete messages: {delete_message_status} 🗑️\n"
            f"Ban users: {ban_status} 🚫\n"
            f"Notifications: {notification_status} 📢\n"
            f"Delete profanity: {matdelete} 📢\n\n"
            f"<i>First version: Lost Samurai 0.4</i>"
        )
        await message.reply(info_text, parse_mode='html')

    @dp.message_handler(commands=['help'])
    async def process_help_command(message: Message):
        await message.answer(help_text, parse_mode='html')

    @dp.message_handler(commands=['setlog'])
    async def process_setlog_command(message: Message):
        await is_group(message)
        if not await has_permission(message):
            await message.reply("Only an administrator or user with special permissions can set the log channel.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Usage: /setlog <channel_id>")
            return

        log_channel_id = parts[1]
        log_channels[str(chat_id)] = log_channel_id
        save_data(LOG_CHANNELS_DB, log_channels)
        await message.reply(f"Log channel successfully set: {log_channel_id}")

    @dp.message_handler(commands=['me'])
    async def process_me_command(message: Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if str(chat_id) not in user_messages or str(user_id) not in user_messages[str(chat_id)]:
            await message.reply("You haven't sent any messages in this chat yet. 😢")
            return
        
        message_count = user_messages[str(chat_id)][str(user_id)]
        rank = get_user_rank(message_count)
        
        if message.from_user.is_bot:
            rank = "Bot 🤖"
        elif await has_permission(message):
            rank = "Ruler 👑"
        
        await message.reply(f"User: {message.from_user.full_name}\n"
                        f"ID: {user_id} 🔢\n"
                        f"Message count: {message_count} 💬\n"
                        f"Rank: {rank}")

    @dp.message_handler(commands=['setdeletemat'])
    async def process_setdeletemat_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply("Only an administrator or user with special permissions can change settings.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Usage: /setdeletemat <True/False>")
            return

        deletemat = parts[1].lower() == 'true'
        chat_settings = load_chat_settings()
        if str(chat_id) not in chat_settings:
            chat_settings[str(chat_id)] = {}
        chat_settings[str(chat_id)]['deletemat'] = deletemat
        save_chat_settings(chat_settings)
        await message.reply(f"Profanity deletion successfully {'enabled' if deletemat else 'disabled'}.")

    @dp.message_handler(commands=['setthreshold'])
    async def process_setthreshold_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply(
                "Only an administrator or user with special permissions can set the message threshold."
            )
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            await message.reply("Usage: /setthreshold <threshold>")
            return

        threshold = int(parts[1])
        thresholds[str(chat_id)] = threshold
        save_data(THRESHOLDS_DB, thresholds)
        await message.reply(f"Message threshold successfully set: {threshold}")

    @dp.message_handler(commands=['setmute'])
    async def process_setmute_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply("Only an administrator or user with special permissions can change settings.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Usage: /setmute <True/False>")
            return

        mute = parts[1].lower() == 'true'
        chat_settings = load_chat_settings()
        if str(chat_id) not in chat_settings:
            chat_settings[str(chat_id)] = {}
        chat_settings[str(chat_id)]['mute'] = mute
        save_chat_settings(chat_settings)
        await message.reply(f"User muting successfully {'enabled' if mute else 'disabled'}.")

    @dp.message_handler(commands=['setdeletemessage'])
    async def process_setdeletemessage_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply("Only an administrator or user with special permissions can change settings.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Usage: /setdeletemessage <True/False>")
            return

        delete_message = parts[1].lower() == 'true'
        chat_settings = load_chat_settings()
        if str(chat_id) not in chat_settings:
            chat_settings[str(chat_id)] = {}
        chat_settings[str(chat_id)]['delete_message'] = delete_message
        save_chat_settings(chat_settings)
        await message.reply(f"Message deletion successfully {'enabled' if delete_message else 'disabled'}.")

    @dp.message_handler(commands=['prof'])
    async def handle_prof_command(message: types.Message):
        argument = message.get_args()
        if argument:
            if '**' in filter_text(argument):
                await message.reply('❌ Profanity detected in the text!')
            else:
                is_spam_result = is_spam(message=argument, model_name="spamNS_v6")
                if is_spam_result:
                    await message.reply('❌ Advertisement detected!')
                else:
                    await message.reply('✅ The text contains no profanity or advertisements.')
        else:
            await message.reply('❌ Please enter a text for checking.')

    @dp.message_handler(commands = ['setban'])
    async def process_setban_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply("Only an administrator or user with special permissions can change settings.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Usage: /setban <True/False>")
            return

        ban = parts[1].lower() == 'true'
        chat_settings = load_chat_settings()
        if str(chat_id) not in chat_settings:
            chat_settings[str(chat_id)] = {}
        chat_settings[str(chat_id)]['ban'] = ban
        save_chat_settings(chat_settings)
        await message.reply(f"User banning successfully {'enabled' if ban else 'disabled'}.")

    @dp.message_handler(commands=['setnotification'])
    async def process_setnotification_command(message: Message):
        await is_group(message)

        if not await has_permission(message):
            await message.reply("Only an administrator or user with special permissions can change settings.")
            return

        chat_id = message.chat.id
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Usage: /setnotification <True/False>")
            return

        notification = parts[1].lower() == 'true'
        chat_settings = load_chat_settings()
        if str(chat_id) not in chat_settings:
            chat_settings[str(chat_id)] = {}
        chat_settings[str(chat_id)]['notification'] = notification
        save_chat_settings(chat_settings)
        await message.reply(f"Notifications successfully {'enabled' if notification else 'disabled'}.")

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
                        text="Cannot ban an administrator or chat owner."
                    )
                    return
                
                banlist = load_data(BANLIST_DB)
                if target_user_id not in banlist:
                    banlist.append(target_user_id)
                    save_data(BANLIST_DB, banlist)

                await bot.ban_chat_member(chat_id=target_chat_id, user_id=target_user_id)
                message_text = callback_query.message.text or "Message was deleted or unavailable"
                ban_message = f"✅ User {target_user_id} has been banned\n\n"
                ban_message += f"Banned by: {callback_query.from_user.full_name} (@{callback_query.from_user.username})\n"
                ban_message += f"{message_text}"
                await bot.edit_message_text(
                    text=ban_message,
                    chat_id=chat_id,
                    message_id=callback_query.message.message_id
                )
                await bot.answer_callback_query(callback_query.id, text="User successfully banned")

                banned_messages = load_data(BANNED_MESSAGES_DB)
                banned_messages.append({
                    "user_id": target_user_id,
                    "chat_id": target_chat_id,
                    "message": message_text
                })
                save_data(BANNED_MESSAGES_DB, banned_messages)

            except Exception as e:
                await bot.answer_callback_query(callback_query.id,
                                                text=f"Error while banning: {type(e).__name__}, {str(e)}")

        elif data.startswith("incorrect_"):
            with open(WRONG_MESSAGES, 'r') as file:
                wrong_messages = json.load(file)

            wrong_messages.append({"user_id": user_id, "chat_id": chat_id, "message": callback_query.message.text})

            with open(WRONG_MESSAGES, 'w') as file:
                json.dump(wrong_messages, file, ensure_ascii=False, indent=4)

            await bot.send_message(chat_id=-1002348384690, text=f"Incorrectly determined message:\n\n{callback_query.message.text}")
            await bot.edit_message_text(text="Thank you for your feedback! This will help us improve our models!",
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
                    await bot.send_message(chat_id, "Cannot ban an administrator!")
                    return
                
                await bot.ban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

            if chat_settings.get('mute', False) and pred_average:
                if has_permission(message):
                    await bot.send_message(chat_id, "Cannot mute an administrator!")
                    return
                
                await bot.restrict_chat_member(chat_id=message.chat.id, user_id=message.from_user.id, can_send_messages=False)

            if chat_settings.get('notification', True):
                log_channel_id = log_channels.get(str(message.chat.id))

                if log_channel_id:
                    keyboard = get_ban_keyboard(message.from_user.id, message.chat.id)
                    await bot.send_message(
                        log_channel_id,
                        f"Message from @{message.from_user.username} deleted in {message.chat.title}:\n\n{filtered_message_text}, model probability: {confidence}",
                        reply_markup=keyboard
                    )
                    if pred_average:
                        message_text = f"💬 Message deleted for advertising by @{message.from_user.username or message.from_user.id}! 🚫 Probability: {confidence}"
                    else:
                        message_text = f"💬 Message deleted for profanity by @{message.from_user.username or message.from_user.id}!"

                    await bot.send_message(
                        chat_id,
                        message_text
                    )