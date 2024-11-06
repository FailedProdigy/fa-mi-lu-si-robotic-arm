import asyncio
from bleak import BleakScanner, BleakClient


async def main():
    devices = await BleakScanner.discover()
    pico = None

    for device in devices:
        if device.name == "mpy-uart":
            pico = device


    if not pico:
        print("Couldn't find robotic arm")
        return

    uart_service_uuid = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
    # double check which should be rx and tx
    tx_uuid = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
    rx_uuid = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

    
    async with BleakClient(pico) as client:

        while True:
            await client.write_gatt_char(
                rx_uuid,
                input("Enter the duty cycle : ").encode()
            )

asyncio.run(main())