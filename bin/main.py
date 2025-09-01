import asyncio
import os, json
import dotenv
import sys
from src.google_spreadsheet_api import (
    DataProcessor,
    listen_updates,
    update_responsible,
    DataStorage,
)
from src.telegram_api import TelegramAPI, channels
from aiogram import types
from src.dto import NewSignUpEvent, SignUpEventResponse

dotenv.load_dotenv()

# Google Sheets API
with open("service_account.json", "r") as f:
    service_account_info = json.load(f)
spreadsheet_id = os.getenv("SPREADSHEET_ID") or ""
if not spreadsheet_id:
    raise ValueError("SPREADSHEET_ID environment variable is not set.")

data_processor = DataProcessor(service_account_info)
data_storage = DataStorage()

# Telegram Bot API
telegram_token = os.getenv("TELEGRAM_TOKEN")
if not telegram_token:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set.")
telegram_api = TelegramAPI(token=telegram_token)

@telegram_api.dispatcher.message()
async def handle_start_command(message):
    print(f"Received /start command from {message.from_user.username or message.from_user.full_name}"
        f" in chat {message.chat.id}")

    if message.text == "/stop_running_bot":
        sys.exit(0)

@telegram_api.dispatcher.channel_post()
async def handle_channel_post(message: types.Message):
    print(f"Received a channel post in chat {message.chat.id}: {message.text}")


@telegram_api.dispatcher.callback_query()
async def handle_take_su_callback(callback_query):
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id
    text = callback_query.message.text.splitlines()[1]
    row = int(callback_query.data.replace("take_su:", ""))
    contacted_by = callback_query.from_user.username or callback_query.from_user.full_name
    await update_responsible(
        data_processor,
        spreadsheet_id=spreadsheet_id,
        data=SignUpEventResponse(
            row=row,
            contacted_by=contacted_by,
            timestamp=callback_query.message.date.strftime("%m/%d/%Y %H:%M:%S"),
        ),
    )
    await telegram_api.bot.answer_callback_query(callback_query.id, text="SU taken!")
    await telegram_api.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=f"Taken by {contacted_by}\n{text}"
    )
    sign_up = data_storage.data[row]
    await telegram_api.bot.send_message(
        chat_id=callback_query.from_user.id,
        text=(f"Contact data for Sign Up:"
            f"\nName: {sign_up.name}"
            f"\nPhone: {sign_up.phone}"
            f"\nTimestamp: {sign_up.timestamp}"
        )
    )

async def handle_new_sign_up_event():
    global data_processor, spreadsheet_id, telegram_api, data_storage
    async for event in listen_updates(
        data_processor,
        spreadsheet_id=spreadsheet_id,
        range_name="rd_responses!A3:AE1500",
        state=data_storage.data,
    ):
        if not isinstance(event, NewSignUpEvent):
            print(f"Received non-sign-up event: {event}")
            continue
        name, phone, row, timestamp = (event.name, event.phone, event.row, event.timestamp)
        local_commitee = event.local_commitee

        print(f"New sign-up event: {name}, {phone}, {row}, {timestamp}, {local_commitee}")
        data_storage.add(row, event)
        await telegram_api.send_new_sign_up_event(
            chat_id=channels.get(local_commitee, channels["NonRegion"]),
            name=name,
            phone=phone,
            row=row,
            timestamp=timestamp,
            local_commitee=local_commitee,
        )

async def main():
    await data_processor.init_sheets_api()
    data_storage.load()

    tg_task = asyncio.create_task(telegram_api.start_polling())
    su_task = asyncio.create_task(handle_new_sign_up_event())

    try:
        await asyncio.gather(tg_task, su_task)
    except asyncio.CancelledError:
        print("Tasks were cancelled, shutting down...")
        tg_task.cancel()
        su_task.cancel()
        await asyncio.gather(tg_task, su_task, return_exceptions=True)

if __name__ == "__main__":
    print("Hello from aiesec-signup-bot!")
    asyncio.run(main())
    print("Exiting aiesec-signup-bot...")
