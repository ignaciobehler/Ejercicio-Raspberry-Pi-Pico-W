from wlan import connect_wifi
import uasyncio as asyncio

async def main():
    connect_wifi()

asyncio.run(main())