import aiogram

from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


class TelegramAPI:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dispatcher = Dispatcher()

    async def send_new_sign_up_event(
        self, chat_id: int | str, name: str, phone: str, row: int, timestamp: str
    ):
        message = (
            f"New sign-up event:\n"
            f"Name: {name}\n"
            f"Phone: {phone}\n"
            f"Row: {row}\n"
            f"Timestamp: {timestamp}"
        )
        button1 = InlineKeyboardButton(text="Take SU", callback_data="Take SU")
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=[[button1]])
        await self.bot.send_message(
            text=message, chat_id=chat_id, reply_markup=keyboard_inline
        )

    async def start_polling(self):
        await self.dispatcher.start_polling()
