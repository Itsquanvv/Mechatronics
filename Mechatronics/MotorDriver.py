
from machine import Pin, PWM

#motor trái
in1 = Pin(26, Pin.OUT)
in2 = Pin(27, Pin.OUT)
enA = PWM(Pin(32), freq=1000)

#motor phải
in3 = Pin(14, Pin.OUT)
in4 = Pin(12, Pin.OUT)
enB = PWM(Pin(33), freq=1000)

def set_motor(pwm_pin, in1_pin, in2_pin, speed):
    #giới hạn xung tốc độ theo 10-bit từ -1023 đến 1023
    if speed > 1023:
        speed = 1023
    elif speed < -1023:
        speed = -1023

    pwm_pin.duty(abs(speed)) #xung nhận giá trị dương

    if speed > 0: #motor tiến
        in1_pin.value(1)
        in2_pin.value(0)
    elif speed < 0: #motor lùi
        in1_pin.value(0)
        in2_pin.value(1)       
    else: #motor dừng
        in1_pin.value(0)
        in2_pin.value(0)   

def motor_drive(left_speed, right_speed):
    set_motor(enA, in1, in2, left_speed)
    set_motor(enB, in3, in4, right_speed)

def stop_motors():
    motor_drive(0, 0)