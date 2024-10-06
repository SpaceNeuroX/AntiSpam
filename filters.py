from aiogram.dispatcher.filters import BoundFilter
from aiogram import types

class IsAdminFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin, bot):
        self.is_admin = is_admin
        self.bot = bot

    async def check(self, message: types.Message):
        chat_member = await self.bot.get_chat_member(message.chat.id, message.from_user.id)
        return chat_member.status in ["creator", "administrator"]
