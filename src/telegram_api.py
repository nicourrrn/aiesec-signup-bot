from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest


class TelegramAPI:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dispatcher = Dispatcher()

    async def send_new_sign_up_event(self, chat_id: int, row: int):
        takeSUbtn = InlineKeyboardButton(text="Take SU", callback_data=f"take_su:{row}")
        keyboard_inline = InlineKeyboardMarkup(inline_keyboard=[[takeSUbtn]])
        try:
            await self.bot.send_message(
                text="New sign-up", chat_id=chat_id, reply_markup=keyboard_inline
            )
        except TelegramBadRequest as e:
            print(f"Exception: {e}")

    async def start_polling(self):
        await self.dispatcher.start_polling(self.bot)


channels = {
    "KY": -1002963172994,
    "KH": -1002925433001,
    "OD": -1002550017359,
    "TE": -1002700260136,
    "LV": -1002930120733,
    "DP": -1003056123859,
    "KP": -1002895850091,
    "CK": -1003023710033,
    "KU": -1002706595782,
    "IF": -1003096227491,
    "VN": -1002955518917,
    "NonRegion": -1002886938885
}
