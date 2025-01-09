import bluetooth
from machine import Pin, PWM, ADC
from time import sleep
from ble_setup import BLESimplePeripheral

ble = bluetooth.BLE()
bt = BLESimplePeripheral(ble)

base = PWM(Pin("GP1"))
bottom = PWM(Pin("GP2"))
middle = PWM(Pin("GP3"))
top = PWM(Pin("GP4"))
hand = PWM(Pin("GP5"))

base.freq(50)
bottom.freq(50)
middle.freq(50)
top.freq(50)
hand.freq(50)

led = Pin("LED",Pin.OUT)

# Testing the arms
# base : full range
# bottom : 6000 - 3000
# middle : full
# top : full
# hand : 1670 - 2500 (close - open)

knob = ADC(Pin("GP28", Pin.PULL_UP))

def analog_to_pwm_duty_cycle(analog_value,  pulse_min=500, pulse_max=2500, pwm_frequency=50):
    period = 1_000_000 / pwm_frequency  # Converts Hz to microseconds
    
    # Map the analog value to the pulse width range
    pulse_width = pulse_min + (analog_value / 65535) * (pulse_max - pulse_min)
    
    # Calculate duty cycle
    duty_cycle = (pulse_width / period) * 65535
    
    return int(duty_cycle)

# Whenever we read from the bluetooth module
def on_rx(value):
    value = value.decode()
    print(f"RX {value}")

    motor = value.split(":")[0]
    number = int(value.split(":")[1])

    if motor == "1":
        base.duty_u16(analog_to_pwm_duty_cycle(number))
    elif motor == "2":
        bottom.duty_u16(analog_to_pwm_duty_cycle(number))
    elif motor == "3":
        middle.duty_u16(analog_to_pwm_duty_cycle(number))
    elif motor == "4":
        top.duty_u16(analog_to_pwm_duty_cycle(number))
    elif motor == "5":
        if number > 35000:
            hand.duty_u16(analog_to_pwm_duty_cycle(0))
        else:
            hand.duty_u16(analog_to_pwm_duty_cycle(5000))

# Enable bluetooth control
bt.on_write(on_rx)

while True:
    knob_val = knob.read_u16()
    # hand.duty_u16(analog_to_pwm_duty_cycle(knob_val))
    # print(knob_val)
    if bt.is_connected():
        led.on()
    else:
        led.off()
    sleep(0.02)
