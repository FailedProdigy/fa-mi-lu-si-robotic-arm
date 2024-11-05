import asyncio
from bleak import BleakScanner, BleakClient
from itertools import count, takewhile
from typing import Iterator


async def main():
    devices = await BleakScanner.discover()
    pico = None

    for device in devices:
        if device.name == "mpy-uart":
            pico = device


    if not pico:
        print("Couldn't find robotic arm")
        return

    uart_service_uuid = ""
    rx_uuid = ""
    tx_uuid = ""

    
    async with BleakClient(pico) as client:
        for service in client.services:
            if "UART" in service.description:
                uart_service_uuid = service.uuid
                print(f"UART Service UUID: {uart_service_uuid}")

                for characteristic in service.characteristics:
                    if "RX" in characteristic.description:
                        rx_uuid = characteristic.uuid
                        print(f"RX UUID: {rx_uuid}")
                        print(characteristic.properties)
                    if "TX" in characteristic.description:
                        tx_uuid = characteristic.uuid
                        print(f"TX UUID: {tx_uuid}")
                        print(characteristic.properties)
    
        while True:
            await client.write_gatt_char(
                rx_uuid,
                input("Enter the duty cycle : ").encode()
            )

asyncio.run(main())