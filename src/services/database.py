import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TypedDict

import aiohttp
from aiohttp.client import ClientSession

from src.config import Config


class DataBaseTokens:
    GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"

    Token = TypedDict(
        "Token",
        {
            "access_token": str,
            "expires_in": int,
            "scope": str,
            "refresh_token": str,
            "token_type": str,
            "id_token": str,
        },
    )

    Code = TypedDict(
        "Code",
        {
            "device_code": str,
            "user_code": str,
            "expires_in": int,
            "interval": int,
            "verification_url": str,
        },
    )

    def __init__(self, config: Config):
        self.client_id = config.google["client_id"]
        self.client_secret = config.google["client_secret"]
        self.scope = config.google["scope"]

    def token_expired(self) -> bool:
        return datetime.now() > self.expires_in

    def load_tokens(self, config: Config) -> bool:
        self.access_token: str = config.google.get("access_token", None)
        self.refresh_token: str = config.google.get("refresh_token", None)
        self.expires_in: datetime = config.google.get("expires_in", None)
        return self.access_token is not None

    async def refresh(self, session: ClientSession) -> bool:
        resp = await session.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if resp.status != 200:
            return False
        tokens: DataBaseTokens.Token = await resp.json()
        self.access_token = tokens["access_token"]
        self.expires_in = datetime.now() + timedelta(seconds=tokens["expires_in"])
        return True

    async def login(self, session: ClientSession):
        resp = await session.post(
            "https://oauth2.googleapis.com/device/code",
            data={"client_id": self.client_id, "scope": self.scope},
        )
        code: DataBaseTokens.Code = await resp.json()
        print(f"Please enter: {code['user_code']} at:\n{code['verification_url']}")
        device_code, interval = code["device_code"], code["interval"]
        while True:
            await asyncio.sleep(interval)
            tokens: DataBaseTokens.Token = await (
                await session.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "device_code": device_code,
                        "grant_type": DataBaseTokens.GRANT_TYPE,
                    },
                )
            ).json()
            if "error" not in tokens:
                self.access_token = tokens["access_token"]
                self.refresh_token = tokens["refresh_token"]
                self.expires_in = datetime.now() + timedelta(
                    seconds=tokens["expires_in"]
                )
                break


class Range:
    @dataclass
    class Cell:
        row: int
        comumn: str

        def __str__(self) -> str:
            return f"{self.comumn}{self.row}"

    def __init__(
        self, id: str, name: str, start: Cell, end: Cell | None = None
    ) -> None:
        self.id = id
        self.name = name
        self.start = start
        self.end = end

    def copy(self, start: Cell, end: Cell | None = None) -> "Range":
        return Range(self.id, self.name, start, end)

    def __str__(self) -> str:
        return f"{self.name}!{self.start}" + (f":{self.end}" if self.end else "")

    @property
    def url(self) -> str:
        return f"https://sheets.googleapis.com/v4/spreadsheets/{self.id}/values/{self}"


class DataBase:
    def __init__(self, config: Config) -> None:
        self.session = aiohttp.ClientSession()
        self.tokens = DataBaseTokens(config)

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.tokens.access_token}"}

    async def get_me(self) -> dict:
        resp = await self.session.get(
            "https://www.googleapis.com/oauth2/v3/userinfo", headers=self.headers
        )
        return await resp.json()

    async def get_range(self, data_range: Range) -> dict:
        resp = await self.session.get(data_range.url, headers=self.headers)
        return (await resp.json()).get("values", [])

    async def update_range(self, data_range: Range, values: list[list]) -> dict:
        url = f"{data_range.url}?valueInputOption=USER_ENTERED"
        resp = await self.session.put(
            url,
            headers=self.headers,
            json={"values": values, "range": str(data_range)},
        )
        try:
            return await resp.json()
        except Exception as e:
            print(e)
            print(resp.status)
        return {}

    async def close(self):
        await self.session.close()
