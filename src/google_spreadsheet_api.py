import asyncio
import pickle
from datetime import datetime
from typing_extensions import AsyncGenerator

from aiogoogle.client import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds
from .dto import NewSignUpEvent, SignUpEventResponse


class DataStorage:
    def __init__(self, data: dict = dict()):
        self.data = data

    def save(self):
        pickle.dump(self.data, open("data.pkl", "wb"))

    def load(self):
        try:
            self.data = pickle.load(open("data.pkl", "rb"))
        except Exception as e:
            print(f"Error loading data: {e}")
            self.data = {}

    def add(self, row: int, item: NewSignUpEvent):
        if row not in self.data.keys():
            self.data[row] = item
            self.save()


class DataProcessor:
    def __init__(
        self,
        service_account_info: dict,
        scopes: list = ["https://www.googleapis.com/auth/spreadsheets"],
    ):
        self.credentials = ServiceAccountCreds(
            scopes=scopes,
            **service_account_info,
        )
        self.api = Aiogoogle(service_account_creds=self.credentials)

    async def init_sheets_api(self):
        self.sheets_api = await self.api.discover("sheets", "v4")

    async def write_data(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: list,
        value_input_option: str = "RAW",
    ):
        response = await self.api.as_service_account(
            self.sheets_api.spreadsheets.values.update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                json={"values": values},
            )
        )
        return response

    async def read_data(
        self,
        spreadsheet_id: str,
        range_name: str,
    ):
        response = await self.api.as_service_account(
            self.sheets_api.spreadsheets.values.get(
                spreadsheetId=spreadsheet_id,
                range=range_name,
            )
        )
        return response

short_lc_names = {
    "Non-region": "NonRegion",
    "Київ": "KY",
    "Харків": "KH",
    "Одеса": "OD",
    "Тернопіль": "TE",
    "Львів": "LV",
    "Дніпро": "DN",
    "Кропивницький": "KP",
    "Черкаси": "CK",
    "КУ": "KU",
    "Івано-Франківськ": "IF",
    "Вінниця": "VN",
}

async def listen_updates(
    data_processor: DataProcessor,
    spreadsheet_id: str,
    range_name: str,
    state: dict = dict(),
) -> AsyncGenerator[NewSignUpEvent | str, None]:
    global short_lc_names
    phones = [item.phone for item in state.values()]
    while True:
        try:
            response = await data_processor.read_data(spreadsheet_id, range_name)
            values = response.get("values", [])
            user_phones = [(row[3], i+3) for i, row in enumerate(values) if len(row[3]) > 0]
            for i, (phone, spread_row) in enumerate(user_phones):
                if phone not in phones:
                    phones.append(phone)
                    row = values[spread_row - 3]
                    print(f"Region: {row[-1]}, Short: {short_lc_names.get(row[-1], 'Unknown')}")
                    yield NewSignUpEvent(
                        name=row[0],
                        local_commitee=short_lc_names.get(row[-1], "Unknown"),
                        phone=phone,
                        row=spread_row,
                        timestamp=datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                    )
        except Exception as e:
            yield f"Error reading data: {e}"
        await asyncio.sleep(5)


async def update_responsible(
    data_processor: DataProcessor, spreadsheet_id: str, data: SignUpEventResponse
):
    range_name = f"rd_responses!AF{data.row}:AG{data.row}"
    values = [[data.contacted_by, data.timestamp]]
    response = await data_processor.write_data(spreadsheet_id, range_name, values)
    return response
