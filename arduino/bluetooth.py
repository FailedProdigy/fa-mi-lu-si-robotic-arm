import asyncio
from bleak import BleakClient, BleakScanner

tx_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"


async def find_device():
    devices = await BleakScanner.discover()

    for device in devices:
        if device.name == "HC-08":
            return device

    print("Couldn't find robotic arm")
    return None


async def main():
    arduino_device = await find_device()
    if not arduino_device:
        return
    async with BleakClient(arduino_device) as arduino:
        while (message := input("> ").strip().encode()) != "Q".encode():
            print(bytearray(message))
            await arduino.write_gatt_char(tx_uuid, message)
            print(":)")


asyncio.run(main())
