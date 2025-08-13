import logging
from typing import TypedDict

import aiohttp

from src.config import Config


class Bot:
    _from = TypedDict(
        "_from",
        {
            "first_name": str,
            "id": int,
            "is_bot": bool,
            "is_premium": bool,
            "language_code": str,
            "username": str,
        },
    )

    _chat = TypedDict("_chat", {"id": int, "type": str, "title": str, "username": str})

    Message = TypedDict(
        "Message", {"message_id": int, "text": str, "from": _from, "chat": _chat}
    )
    InlineKeyboardButton = TypedDict(
        "InlineKeyboardButton", {"text": str, "callback_data": str}
    )
    InlineKeyboard = TypedDict(
        "InlineKeyboard", {"inline_keyboard": list[list[InlineKeyboardButton]]}
    )

    def __init__(self, config: Config):
        self.token = config.bot_token
        self.session = aiohttp.ClientSession()
        self.updates = []

    def api_url(self, command: str) -> str:
        return f"https://api.telegram.org/bot{self.token}/{command}"

    async def execute_command(
        self, command: str, method: str = "get", json: dict = {}, **kwargs
    ) -> tuple[int, dict]:
        response = await self.session.request(
            method=method, url=self.api_url(command), json=json, **kwargs
        )
        return response.status, await response.json()

    async def get_me(self):
        return await self.execute_command("getMe")

    async def get_updates(
        self,
        only_new: bool = True,
        allowed_updates: list = ["message", "callback_query"],
    ):
        _, updates = await self.execute_command(
            "getUpdates", json={"allowed_updates": allowed_updates}
        )
        updates = updates.get("result", [])

        update_ids = updates and [update["update_id"] for update in updates]
        if only_new:
            updates = [
                update for update in updates if update["update_id"] not in self.updates
            ]

        self.updates.extend(update_ids)
        return updates

    async def send_message(self, id: int, text: str, reply_markup=None):
        data = {"text": text, "chat_id": id}
        if reply_markup:
            data["reply_markup"] = reply_markup

        status, response = await self.execute_command(
            "sendMessage", method="post", json=data
        )
        logging.warning(response)
        return status

    async def answer_callback(self, callback_query_id: str, text: str) -> int:
        data = {"callback_query_id": callback_query_id, "text": text}
        status, _ = await self.execute_command(
            "answerCallbackQuery", method="post", json=data
        )
        return status

    async def edit_message_text(
        self, chat_id: int, message_id: int, text: str, reply_markup=None
    ) -> int:
        data = {"chat_id": chat_id, "message_id": message_id, "text": text}
        if reply_markup:
            data["reply_markup"] = reply_markup

        status, _ = await self.execute_command(
            "editMessageText", method="post", json=data
        )
        return status

    async def close(self):
        await self.session.close()


def create_inline_keyboard(keys: list[list[tuple[str, str]]]) -> Bot.InlineKeyboard:
    keyboard: Bot.InlineKeyboard = {"inline_keyboard": []}
    for row in keys:
        keyboard["inline_keyboard"].append(
            [{"text": text, "callback_data": data} for text, data in row]
        )
    return keyboard
