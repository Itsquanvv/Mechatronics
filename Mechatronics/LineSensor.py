from machine import Pin


# Danh sách chân 5 cảm biến TCRT5000 theo thứ tự Trái -> Phải
sensor_pins = [23, 22, 21, 19, 18]
sensors = [Pin(pin, Pin.IN) for pin in sensor_pins]

# Đảo giá trị nếu module của bạn xuất mức LOW (0) khi đè lên vạch đen
# Đặt ACTIVE_LEVEL = 1 nếu lên vạch đen là HIGH (1)
# Đặt ACTIVE_LEVEL = 0 nếu lên vạch đen là LOW (0)
BLACK_LINE_LEVEL = 1

def read_black_line():
    weighted_sum = 0
    sum_vals = 0

    for i in range(5):
        # Đọc trạng thái Digital 0/1 của từng mắt
        val = 1 if sensors[i].value() == BLACK_LINE_LEVEL else 0

        weighted_sum += val * (i * 1000)
        sum_vals += val

    # Nếu không mắt nào bắt được vạch (mất vạch)
    if sum_vals == 0:
        return 2000, True  # Trả về vị trí trung tâm 2000 và cờ is_lost = True

    # Trả về vị trí tính được từ 0 đến 4000 (Trung tâm là 2000) và is_lost = False
    return weighted_sum // sum_vals, False