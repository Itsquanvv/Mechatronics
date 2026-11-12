import bluetooth
import utime
from machine import Pin

from BLE_UART import ESP32_BLE_UART
import LineSensor
import MotorDriver

# --- CẤU HÌNH THÔNG SỐ MẶC ĐỊNH ---
rspeed = 800        # Tốc độ chạy thẳng (0 - 1023)
turn_speed = 500    # Tốc độ xoay khi vào cua vuông / tìm vạch

Kp = 1.5
Ki = 0.0
Kd = 0.8

multiP = 1
multiI = 1
multiD = 1

previous_error = 0
I = 0
onoff = False       # Mặc định dừng, chờ lệnh bật (07 01) qua Bluetooth

# LED báo trạng thái (sáng khi xe đang chạy)
led = Pin(2, Pin.OUT)
led.value(0)

# Khởi tạo Bluetooth BLE tích hợp
ble = bluetooth.BLE()
bt_serial = ESP32_BLE_UART(ble, name="ESP32_Robot")


# --- HÀM ĐỌC LỆNH BLUETOOTH ---
def process_bluetooth():
    global Kp, Ki, Kd, multiP, multiI, multiD, onoff, rspeed

    if bt_serial.any() >= 2:
        cmd = bt_serial.read(2)
        if not cmd or len(cmd) < 2:
            return

        param_type = cmd[0]
        value = cmd[1]

        print(f"[BLE CMD] Type={param_type}, Value={value}")

        if param_type == 1:
            Kp = value
        elif param_type == 2:
            multiP = value
        elif param_type == 3:
            Ki = value
        elif param_type == 4:
            multiI = value
        elif param_type == 5:
            Kd = value
        elif param_type == 6:
            multiD = value
        elif param_type == 7:
            onoff = bool(value)
            led.value(1 if onoff else 0)


        bt_serial.send(f"ACK:{param_type}={value}\n")


# --- HÀM TÍNH TOÁN PID ---
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

    # Tự động hãm nhẹ tốc độ khi vào cua cong
    actual_speed = max(400, rspeed - int(abs(error) * 0.1))

    left_speed = int(actual_speed - pid_val)
    right_speed = int(actual_speed + pid_val)

    MotorDriver.motor_drive(left_speed, right_speed)


# --- VÒNG LẶP CHÍNH ---
print("Hệ thống sẵn sàng! Kết nối BLE 'ESP32_Robot' và gửi HEX '07 01' để chạy.")

while True:
    process_bluetooth()

    if onoff:
        s = [
            1 if sensor.value() == LineSensor.BLACK_LINE_LEVEL else 0
            for sensor in LineSensor.sensors
        ]
        # đi thẳng là [0 0 1 0 0]
        # 1. Xử lý góc vuông RẼ TRÁI
        if s[0] == 1 and s[1] == 1 and s[2] == 1 and s[4] == 0:
            MotorDriver.motor_drive(turn_speed, turn_speed)
            utime.sleep_ms(60)
            while LineSensor.sensors[2].value() != LineSensor.BLACK_LINE_LEVEL:
                MotorDriver.motor_drive(-turn_speed, turn_speed)
                process_bluetooth()
                if not onoff:
                    break
                utime.sleep_ms(2)
            previous_error = 2000

        # 2. Xử lý góc vuông RẼ PHẢI
        elif s[0] == 0 and s[3] == 1 and s[2] == 1 and s[4] == 1:
            MotorDriver.motor_drive(turn_speed, turn_speed)
            utime.sleep_ms(60)
            while LineSensor.sensors[2].value() != LineSensor.BLACK_LINE_LEVEL:
                MotorDriver.motor_drive(turn_speed, -turn_speed)
                process_bluetooth()
                if not onoff:
                    break
                utime.sleep_ms(2)
            previous_error = -2000

        # 3. Chạy bám vạch PID bình thường & tìm vạch khi mất line
        else:
            position, is_lost = LineSensor.read_black_line()

            if is_lost:
                if previous_error > 0:
                    MotorDriver.motor_drive(-turn_speed, turn_speed)
                else:
                    MotorDriver.motor_drive(turn_speed, -turn_speed)
            else:
                error = 2000 - position
                pid_line_follow(error)
    else:
        MotorDriver.stop_motors()
        I = 0

    utime.sleep_ms(2)