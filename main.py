import bluetooth
import random
import struct
import time
from machine import Pin, PWM, ADC, UART
from time import sleep
from ble_advertising import advertising_payload
from micropython import const

# Bluetooth setup

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

class BLESimplePeripheral:
    def __init__(self, ble, name="mpy-uart"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            print("New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)
    
    def on_write(self, callback):
        self._write_callback = callback


ble = bluetooth.BLE()
bt = BLESimplePeripheral(ble)

def on_rx(value):
    print(f"RX{value}")

bt.on_write(on_rx)

base = PWM(Pin("GP1"))
base.freq(50)

led = Pin("LED",Pin.OUT)

# Testing the arms
# base : full range
# bottom : 6000 - 3000
# middle : full
# top : full
# hand : 1670 - 2500 (close - open)while True:
#     knob_val = knob.read_u16()
#     base.duty_u16(analog_to_pwm_duty_cycle(knob_val))
#     sleep(0.02)

knob = ADC(Pin("GP28", Pin.PULL_UP))

def analog_to_pwm_duty_cycle(analog_value,  pulse_min=500, pulse_max=2500, pwm_frequency=50):
    period = 1_000_000 / pwm_frequency  # Converts Hz to microseconds (20,000 µs for 50 Hz)
    
    # Map the analog value to the pulse width range
    pulse_width = pulse_min + (analog_value / 65535) * (pulse_max - pulse_min)
    
    # Calculate duty cycle
    duty_cycle = (pulse_width / period) * 65535
    
    return int(duty_cycle)

while True:
    knob_val = knob.read_u16()
    base.duty_u16(analog_to_pwm_duty_cycle(knob_val))
    if bt.is_connected():
        led.on()
    else:
        led.off()
    sleep(0.02)
