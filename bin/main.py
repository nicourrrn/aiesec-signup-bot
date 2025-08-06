import asyncio
import logging
from typing import Optional

from src.config import Config
from src.services.database import DataBase, Range
from src.services.comunicator import Bot, create_inline_keyboard  # твій клас

logging.basicConfig(level=logging.INFO)

SHEET_ID = "1nIVD7hAbwVvp1ffI9PolDbtPP_3jjXTI7ixyU24_YGk"
CHAT_ID = "@testbestsest"

city_chats = {
    "Київ": "@Kyiv_RCR_SU_Traker",
    "Львів": "@Lviv_RCR_SU_Traker",
}


def callaback_query(update: dict) -> str:
    try:
        return update["callback_query"]["data"]
    except KeyError:
        return ""


def message(update: dict) -> Optional[str]:
    try:
        return update["message"]["text"]
    except KeyError:
        return None


async def main():
    config = Config()
    database = DataBase(config)

    if not database.tokens.load_tokens(config):
        await database.tokens.login(database.session)

    if database.tokens.token_expired():
        refreshed = await database.tokens.refresh(database.session)
        if not refreshed:
            await database.tokens.login(database.session)

    config.save_tokens(
        database.tokens.access_token,
        database.tokens.refresh_token,
        database.tokens.expires_in,
    )

    bot = Bot(config)

    names = Range(
        SHEET_ID,
        "LEADS",
        Range.Cell(2, "A"),
        Range.Cell(600, "E"),
    )
    manager = names.copy(Range.Cell(1, "E"))

    range_state = await database.get_range(names)

    async def handle_update(update: dict):
        # Обробка callback_query
        if "callback_query" in update:
            data = callaback_query(update)
            if "take" in data:
                callback = update["callback_query"]
                callback_id = callback["id"]
                callback_message = callback["message"]
                callback_from = callback["from"]

                chat_id = callback_message["chat"]["id"]
                message_id = callback_message["message_id"]

                await bot.answer_callback(callback_id, "You took the lead")
                await bot.edit_message_text(
                    chat_id,
                    message_id,
                    f"{callback_message['text']}\n\nManage by @{callback_from.get('username', 'unknown')}",
                    reply_markup=create_inline_keyboard([]),
                )

                manager.start.row = int(data.replace("take", ""))
                await database.update_range(manager, [[callback_from.get("username", "unknown")]])

        # Обробка текстових повідомлень (якщо треба)
        elif "message" in update:
            text = message(update)
            if text:
                logging.info(f"Received message: {text}")
                # Тут можна додати логіку обробки команд /my_leads, /stop тощо

    async def poll_updates():
        while True:
            try:
                updates = await bot.get_updates()
                for update in updates:
                    await handle_update(update)
            except Exception as e:
                logging.error(f"Error while polling updates: {e}")
            await asyncio.sleep(1)

    async def monitor_new_leads():
        nonlocal range_state
        while True:
            try:
                new_range_state = await database.get_range(names)
                for row_i, row in enumerate(new_range_state[len(range_state):]):
                    row_i += len(range_state) + manager.start.row + 1
                    city = row[3] if len(row) > 3 else None
                    chat_id = city_chats.get(city, CHAT_ID)

                    await bot.send_message(
                        chat_id,
                        f"New lead: {row[0]}\nPhone: {row[1]}\nTelegram: {row[2] if len(row) > 2 else '-'}\nLC: {city or 'Невідомо'}",
                        reply_markup=create_inline_keyboard([[("Я візьму", f"take{row_i}")]]),
                    )
                range_state = new_range_state
            except Exception as e:
                logging.error(f"Error fetching new leads: {e}")

            if database.tokens.token_expired():
                await database.tokens.refresh(database.session)

            await asyncio.sleep(5)

    poll_task = asyncio.create_task(poll_updates())
    leads_task = asyncio.create_task(monitor_new_leads())

    try:
        await asyncio.gather(poll_task, leads_task)
    finally:
        poll_task.cancel()
        leads_task.cancel()
        await database.close()
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
