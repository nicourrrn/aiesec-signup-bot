import aiohttp, asyncio, socket, ssl, certifi

async def main():
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=ssl_context)  # тільки IPv4
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get("https://www.googleapis.com") as resp:
            print(await resp.text())

asyncio.run(main())
