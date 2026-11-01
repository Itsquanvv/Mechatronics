import utime
from machine import Pin

import MotorDriver
import LineSensor


rspeed = 900

Kp = 1.2
Ki = 0.0
Kd = 0.5

#hệ số multi để chia kp, ki, kd chuẩn xác hơn
multiP = 1
multiI = 1
multiD = 1

previous_error = 0
I = 0

led = Pin(2, Pin.OUT)

def pid_line_follow(error):
    global previous_error, I

    P = error
    I += error
    D = error - previous_error

    p_val = (Kp / (10 ** multiP)) * P 
    i_val = (Ki / (10 ** multiI)) * I
    d_val = (Kd / (10 ** multiD)) * D

    pid_val = p_val + i_val + d_val
    previous_error = error

    left_speed = int(rspeed - pid_val)
    right_speed = int(rspeed + pid_val)

    MotorDriver.motor_drive(left_speed, right_speed)

def setup():

    led.value(1) #bật led báo hiệu hiệu chuẩn
    print("Hiệu chuẩn cảm biến!")

    LineSensor.calibrate_sensors()

    led.value(0)
    print("Hiệu chuẩn thành công!")

    utime.sleep(2)

setup()

while True:
    position, is_lost = LineSensor.read_black_line()
    
    if is_lost:
        # Khi mất vạch hẳn: Xoay tại chỗ tìm lại vạch theo hướng lệch gần nhất
        if previous_error > 0:
            MotorDriver.motor_drive(-rspeed, rspeed)  # Xoay trái
        else:
            MotorDriver.motor_drive(rspeed, -rspeed)  # Xoay phải
    else:
        error = 3500 - position
        pid_line_follow(error)
        
    utime.sleep_ms(2)