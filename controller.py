import asyncio
import threading
from bleak import BleakScanner, BleakClient
import tkinter as tk
from tkinter import ttk

uart_service_uuid = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
rx_uuid = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
tx_uuid = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

pico = None
slider_values = [0, 0, 0, 0, 0]
last_sent_values = [0, 0, 0, 0, 0]

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

async def send_value(slider_num, value):
    if pico and pico.is_connected:
        try:
            await pico.write_gatt_char(tx_uuid, f"{slider_num}:{value}".encode())
            print(f"Sent value {slider_num}:{value}")
        except Exception as e:
            print(f"Failed to send value \n {e}")
    else:
        print(f"Pico not connected but here's the command: {value}")

def make_slider_function(slider_num):
    def on_slider_change(value):
        slider_values[slider_num - 1] = int(float(value))
    return on_slider_change

async def periodic_send():
    global last_sent_values, slider_values

    while True:
        for i in range(5):
            if slider_values[i] != last_sent_values[i]: # Send only if value has changed
                await send_value(i + 1, slider_values[i])
                last_sent_values[i] = slider_values[i]
        await asyncio.sleep(0.1)

def run_tk():
    root = tk.Tk()
    root.title("Bluetooth Robot Control")

    labels = []
    sliders = []

    for i in range(5):
        label = tk.Label(root, text=f"Slider {i + 1} Value : 0")
        label.pack(pady=5)
        labels.append(label)

        slider = ttk.Scale(root, from_=0, to=65535, orient="horizontal", length=300, command=make_slider_function(i + 1))
        slider.pack(pady=10, padx=20)
        sliders.append(slider)

    def update_labels():
        for i, label in enumerate(labels):
            label.config(text=f"Slider {i + 1} Value : {slider_values[i]}")
        root.after(100, update_labels)

    update_labels()

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
