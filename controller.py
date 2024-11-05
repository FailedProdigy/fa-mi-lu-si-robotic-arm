import asyncio
from bleak import BleakScanner, BleakClient
from itertools import count, takewhile
from typing import Iterator

# TIP: you can get this function and more from the ``more-itertools`` package.
def sliced(data: bytes, n: int) -> Iterator[bytes]:
    """
    Slices *data* into chunks of size *n*. The last slice may be smaller than
    *n*.
    """
    return takewhile(len, (data[i : i + n] for i in count(0, n)))

async def main():
    devices = await BleakScanner.discover()
    pico = None

    for device in devices:
        if device.name == "mpy-uart":
            pico = device


    if not pico:
        print("Couldn't find robotic arm")
        return

    # Scan for the rx and tx services
    uart_service_uuid = ""
    rx_uuid = ""
    tx_uuid = ""

    
    async with BleakClient(pico) as client:
        for service in client.services:
            if "UART" in service.description:
                uart_service_uuid = service.uuid
                print("UART Service UUID:", uart_service_uuid)

                for characteristic in service.characteristics:
                    if "RX" in characteristic.description:
                        rx_uuid = characteristic.uuid
                        print("RX UUID:", rx_uuid)
                        print(characteristic.properties)
                    if "TX" in characteristic.description:
                        tx_uuid = characteristic.uuid
                        print("TX UUID:", tx_uuid)
                        print(characteristic.properties)
    

        await client.write_gatt_char(rx_uuid,b'hello world')

asyncio.run(main())