import asyncio
import threading
from bleak import BleakScanner, BleakClient
import tkinter as tk
from tkinter import ttk

uart_service_uuid = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
rx_uuid = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
tx_uuid = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

pico = None
slider_value = 0 # Stores the latest slider value
last_sent_value = None # Keeps track of the last sent value to avoid unnecessary updates

async def connect_device():
    global pico
    devices = await BleakScanner.discover()
    pico_device = None

    for device in devices:
        if device.name == "mpy-uart":
            pico_device = device
            break

    if not pico_device:
        print("Couldn't find robotic arm")
        return False

    pico = BleakClient(pico_device)
    try:
        await pico.connect()
        print("Connected to the arm")
        return True
    except Exception as e:
        print(f"Failed to connect \n {e}")
        return False

async def send_value(value):
    if pico and pico.is_connected:
        try:
            await pico.write_gatt_char(tx_uuid, str(value).encode())
            print(f"Sent value {value}")
        except Exception as e:
            print(f"Failed to send value \n {e}")
    else:
        print(f"Pico not connected but here's the command: {value}")

def on_slider_change(value):
    global slider_value
    slider_value = int(float(value))  # Update the buffered slider value

async def periodic_send():
    global last_sent_value, slider_value

    while True:
        if slider_value != last_sent_value:  # Send only if value has changed
            await send_value(f"1:{slider_value}")
            last_sent_value = slider_value
        await asyncio.sleep(0.2)  # Send data every 200 milliseconds

def run_tk():
    root = tk.Tk()
    root.title("Bluetooth Slider Control")

    label = tk.Label(root, text="Slider Value :")
    label.pack(pady=10)

    slider = ttk.Scale(root, from_=0, to=65535, orient="horizontal", command=on_slider_change)
    slider.pack(pady=20, padx=20)

    def update_label():
        label.config(text=f"Slider Value : {slider_value}")
        root.after(100, update_label)  # Schedule the update every 100ms
    
    update_label()

    root.protocol("WM_DELETE_WINDOW", root.quit)  # Properly handle window close
    root.mainloop()

async def main():
    # Connect to the device
    connected = await connect_device()
    if not connected:
        return

    # Start the periodic Bluetooth sending loop as a background asyncio task
    asyncio.create_task(periodic_send())

    # Run tkinter in a separate thread
    tk_thread = threading.Thread(target=run_tk, daemon=True)
    tk_thread.start()

    # Keep the async main function alive as long as Tkinter is running
    while tk_thread.is_alive():
        await asyncio.sleep(0.1)

    if pico and pico.is_connected:
        await pico.disconnect()
        print("Disconnected from the device.")

asyncio.run(main())
