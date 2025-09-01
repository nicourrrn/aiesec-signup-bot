import aiogram

from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest


class TelegramAPI:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dispatcher = Dispatcher()

    async def send_new_sign_up_event(
        self, chat_id: int | str, name: str, phone: str, row: int, timestamp: str, local_commitee: str
    ):
        message = (
            f"New sign-up for\n"
            # f"Name: {name}\n"
            # f"Phone: {phone}\n"
            # f"Timestamp: {timestamp}\n"
            f"Local Committee: #{local_commitee}\n"
        )
        button1 = InlineKeyboardButton(text="Take SU", callback_data=f"take_su:{row}")
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=[[button1]])
        try:
            await self.bot.send_message(
                text=message, chat_id=chat_id, reply_markup=keyboard_inline
            )
        except TelegramBadRequest:
            print(f"Chat {chat_id} not found. Please check the chat ID.")

    async def start_polling(self):
        await self.dispatcher.start_polling(self.bot)


channels = {
    "KY": -1002963172994,
    "KH": -1002925433001,
    "OD": -1002550017359,
    "TE": -1002700260136,
    "LV": -1002930120733,
    "DN": -1003056123859,
    "KP": -1002895850091,
    "CK": -1003023710033,
    "KU": -1002706595782,
    "IF": -1003096227491,
    "VN": -1002955518917,
    "NonRegion": -1002886938885
}
