import asyncio
import threading
from bleak import BleakScanner, BleakClient
import tkinter as tk
from tkinter import ttk

tx_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"

pico = None
names = ["base" ,"bottom" ,"middle" ,"top" ,"hand"]
slider_values = [100, 100, 100, 100, 0]
last_sent_values = [0, 0, 0, 0, 0]

async def connect_device():
    global pico
    devices = await BleakScanner.discover()
    pico_device = None

    for device in devices:
        if device.name == "HC-08":
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
            await pico.write_gatt_char(tx_uuid, f"{names[slider_num]}:{value}".encode(), response=True)
            print(f"Sent value {names[slider_num]}:{value}")
        except Exception as e:
            print(f"Failed to send value \n {e}")
    else:
        print(f"Pico not connected but here's the command: {value}")

def make_slider_function(slider_num):
    def on_slider_change(value):
        slider_values[slider_num] = int(float(value))
    return on_slider_change

async def periodic_send():
    global last_sent_values, slider_values

    while True:
        for i in range(5):
            if slider_values[i] != last_sent_values[i]: # Send only if value has changed
                await send_value(i, slider_values[i])
                last_sent_values[i] = slider_values[i]
        await asyncio.sleep(0.1)

def run_tk():
    root = tk.Tk()
    root.title("Bluetooth Robot Control")

    labels = []
    sliders = []

    for i in range(5):
        label = tk.Label(root, text=f"Slider {names[i]} Value : 0")
        label.pack(pady=5)
        labels.append(label)

        slider = ttk.Scale(root, from_=0, to=300, value=slider_values[i],orient="horizontal", length=300, command=make_slider_function(i))
        slider.pack(pady=10, padx=20)
        sliders.append(slider)

    def update_labels():
        for i, label in enumerate(labels):
            label.config(text=f"Slider {names[i]} Value : {slider_values[i]}")
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
