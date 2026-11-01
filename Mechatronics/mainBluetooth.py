import utime
from machine import UART, Pin

# Import các mô-đun đã tách file
import LineSensor
import MotorDriver

# --- CẤU HÌNH THÔNG SỐ VÀ BIẾN TOÀN CỤC ---
lfspeed = 900          # Tốc độ nền (dải 0 - 1023)
Kp = 0.0
Ki = 0.0
Kd = 0.0

multiP = 1
multiI = 1
multiD = 1

previous_error = 0
I = 0
onoff = False

# LED báo trạng thái Calibration (GPIO 2 trên ESP32)
led = Pin(2, Pin.OUT)

# Cấu hình Bluetooth Serial qua UART2 (RX2=GPIO 16, TX2=GPIO 17 cho HC-05/HC-06)
bt_serial = UART(2, baudrate=115200, rx=16, tx=17)


# --- HÀM ĐỌC LỆNH BLUETOOTH ---
def process_bluetooth():
    global Kp, Ki, Kd, multiP, multiI, multiD, onoff
    
    if bt_serial.any() >= 2:
        cmd = bt_serial.read(2)
        if not cmd or len(cmd) < 2:
            return
            
        param_type = cmd[0]
        value = cmd[1]
        
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


# --- HÀM TÍNH TOÁN PID & ĐIỀU KHIỂN ---
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
    
    # Tính tốc độ 2 động cơ (thang -1023 đến 1023)
    lsp = int(lfspeed - pid_val)
    rsp = int(lfspeed + pid_val)
    
    MotorDriver.motor_drive(lsp, rsp)


# --- KHỞI TẠO VÀ HIỆU CHUẨN (SETUP) ---
def setup():
    # Bật LED báo bắt đầu quá trình hiệu chuẩn
    led.value(1)
    print("Bắt đầu hiệu chuẩn cảm biến (Xoay robot qua lại trên vạch)...")
    
    LineSensor.calibrate_sensors()
    
    # Tắt LED báo hoàn thành
    led.value(0)
    print("Hiệu chuẩn thành công! Sẵn sàng nhận lệnh.")


# --- VÒNG LẶP CHÍNH (MAIN LOOP) ---
setup()

while True:
    # 1. Đọc tín hiệu điều chỉnh thông số từ Bluetooth
    process_bluetooth()
    
    # 2. Xử lý di chuyển
    if onoff:
        position, is_lost = LineSensor.read_line_black()
        
        if is_lost:
            # Xử lý khi mất vạch hẳn: Xoay tại chỗ tìm lại vạch theo hướng lệch gần nhất
            if previous_error > 0:
                MotorDriver.motor_drive(-lfspeed, lfspeed)  # Xoay trái
            else:
                MotorDriver.motor_drive(lfspeed, -lfspeed)  # Xoay phải
        else:
            error = 3500 - position
            pid_line_follow(error)
    else:
        MotorDriver.stop_motors()
        I = 0  # Reset tích lũy khâu I khi robot dừng
        
    utime.sleep_ms(2)