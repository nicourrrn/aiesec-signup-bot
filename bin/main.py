import asyncio
import os, json
import dotenv
from src.google_spreadsheet_api import (
    DataProcessor,
    listen_updates,
    update_responsible,
    DataStorage,
)
from src.dto import NewSignUpEvent, SignUpEventResponse


dotenv.load_dotenv()

# Google Sheets API
with open("service_account.json", "r") as f:
    service_account_info = json.load(f)
spreadsheet_id = os.getenv("SPREADSHEET_ID")
if not spreadsheet_id:
    raise ValueError("SPREADSHEET_ID environment variable is not set.")

data_processor = DataProcessor(service_account_info)
data_storage = DataStorage()

# Telegram Bot API


async def main():
    # Initialize
    await data_processor.init_sheets_api()
    data_storage.load()

    # Start listening for google spreadsheet updates
    async for update in listen_updates(
        data_processor,
        spreadsheet_id=spreadsheet_id,
        range_name="A2:D1000",
        state=data_storage.data,
    ):
        print(f"Received update:\n    {update}")
        match update:
            case NewSignUpEvent(name=name, phone=phone, row=row, timestamp=timestamp):
                print(f"New sign-up event: {name}, {phone}, {row}, {timestamp}")
                response = SignUpEventResponse(
                    row=row,
                    contacted_by="bot",
                    timestamp=timestamp,
                )
                await update_responsible(
                    data_processor,
                    spreadsheet_id=spreadsheet_id,
                    data=response,
                )
                print(f"Response: {response}")
            case _:
                print("Unknown update format")


if __name__ == "__main__":
    print("Hello from aiesec-signup-bot!")
    asyncio.run(main())
    print("Exiting aiesec-signup-bot...")
