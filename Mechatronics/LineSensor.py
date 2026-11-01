from machine import ADC, Pin
import utime

sensor_pins = [26, 27, 14, 12, 13, 15, 2, 4]
sensors = []



for pin in sensor_pins:
    adc = ADC(Pin(pin)) #khai báo chân adc
    adc.atten(ADC.ATTN_11DB) # cấu hình đọc dải điện áp 0 - 3.3V
    sensors.append(adc) #array sensors sẽ nhận các chân adc

#giống thuật toán minmax (alpha = -vô cùng, beta = +vô cùng)

min_vals = [4095] * 8 #tạo mảng [4095, 4095, 4095, 4095, 4095, 4095, 4095, 4095]
max_vals = [0] * 8    #tạo mảng [0, 0, 0, 0, 0, 0, 0, 0]


#hàm này để đánh giá độ đậm nhạt của line thực tế
def calibrate_sensors():
    for _ in range(400):
        for i in range(8): #đọc cảm biến 8 mắt
            v = sensors[i].read()
            min_vals[i] = min(min_vals[i], v)
            max_vals[i] = max(max_vals[i], v)
        utime.sleep_ms(10)

def read_black_line():
    weighted_sum = 0
    sum_vals = 0

    for i in range(8):
        raw = sensors[i].read()
        #chuyển giá trị của sensor từ 0-4095 về 0-1000
        val = (raw - min_vals[i]) * 1000 // (max_vals[i] - min_vals[i] + 1)
        val = max(0, min(1000, val)) #ghim giá trị val từ 0-1000

        weighted_sum += val * (i * 1000)
        sum_vals += val

    if sum_vals == 0:
         return 3500 #trả về khi không thấy vạch

    return weighted_sum // sum_vals # trả về giá trị từ 0 đến 7000



