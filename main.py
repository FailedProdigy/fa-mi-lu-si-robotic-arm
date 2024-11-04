from machine import Pin, PWM, ADC
from time import sleep

lerp = lambda a, b, t : (1 - t) * a + t * b
base = PWM(Pin("GP1"))
base.freq(50)

# Testing the arms
# base : full range
# bottom : 6000 - 3000
# middle : full
# top : full
# hand : 1670 - 2500 (close - open)

knob = ADC(Pin("GP28", Pin.IN))

def analog_to_pwm_duty_cycle(analog_value,  pulse_min=500, pulse_max=2500, pwm_frequency=50):
    period = 1_000_000 / pwm_frequency  # Converts Hz to microseconds (20,000 µs for 50 Hz)
    
    # Map the analog value to the pulse width range
    pulse_width = pulse_min + (analog_value / 65535) * (pulse_max - pulse_min)
    
    # Calculate duty cycle
    duty_cycle = (pulse_width / period) * 65535
    
    return int(duty_cycle)

while True:
    knob_val = knob.read_u16()
    print(f"duty cycle {analog_to_pwm_duty_cycle(knob_val)}")
    base.duty_u16(analog_to_pwm_duty_cycle(knob_val))
    sleep(0.02)
