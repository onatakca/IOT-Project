import asyncio
from bleak import BleakScanner

async def scan():
    async with BleakScanner() as scanner:
        await asyncio.sleep(5)
        for dev in scanner.discovered_devices_and_advertisement_data.items():
            print(dev)
            print("--------------------------------")

asyncio.run(scan())