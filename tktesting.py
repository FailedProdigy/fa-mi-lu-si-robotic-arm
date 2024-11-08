import tkinter as tk
from tkinter import ttk



root = tk.Tk()
label = tk.Label(root, text="Slider Value :")
label.pack(pady=10)

def on_slider_change(value):
    print(f" {value}")
    label.configure(text=f"Slider Value : {value}")

slider_val = tk.IntVar()
    
slider = ttk.Scale(root, from_=0, to=100, orient="horizontal", command=on_slider_change)
slider.get()
slider.pack(pady=20, padx=20)

tk.mainloop()