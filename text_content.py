SPECIAL_USER_IDS = [7264930816, 1529997307]

def get_start_text():
    return (
    '<b>Hello!</b>\n\n'
    'I am a bot for spam detection. Just invite me to your group, and I will remove all spam messages.\n\n'
    'Sometimes I might make mistakes in identifying spam, but I am constantly improving my performance and working on it.\n\n'
    'Happy usage!\n\n'
    '<i>Admin: @NeuroSpaceX</i>\n\n'
    'For more information, use the /help command.'
)


def get_help_text():
    return (
        "<b>Bot Information</b>\n\n"
        "I am a bot for spam detection. Just invite me to your group, and I will remove all spam messages.\n\n"
        "<b>Commands:</b>\n"
        "/start - Start the bot\n"
        "/info - Get information about the current group settings\n"
        "/setlog channel_id - Set the log channel. Can only be used in a group or supergroup.\n"
        "/setthreshold threshold - Set the message threshold for spam filtering.\n"
        "/setmute True/False - Enable or disable muting users.\n"
        "/setdeletemessage True/False - Enable or disable message deletion.\n"
        "/setban True/False - Enable or disable banning users for spam.\n"
        "/setnotification True/False - Enable or disable notifications.\n\n"
        "<b>Developers:</b>\n"
        "Bot and neural network developed by: @NeuroSpaceX\n"
        "All rights reserved.\n\n"
        "Huge thanks to @alexCoder23 for hosting the bot! ❤️\n\n"
        "<b>Support:</b>\n"
        "totoshkus@gmail.com\n\n"
    )
