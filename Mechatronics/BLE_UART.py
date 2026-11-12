import bluetooth
from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_RX_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
_TX_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")

_UART_SERVICE = (
    _UART_UUID,
    (
        (_TX_UUID, _FLAG_NOTIFY),
        (_RX_UUID, _FLAG_WRITE),
    ),
)


class ESP32_BLE_UART:

    def __init__(self, ble, name="ESP32_Robot"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)

        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services(
            (_UART_SERVICE,)
        )

        self._connections = set()
        self._rx_buffer = bytearray()
        self._name = name
        self._advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("\n[Bluetooth BLE] Đã kết nối với điện thoại!")

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.discard(conn_handle)
            print("\n[Bluetooth BLE] Đã ngắt kết nối! Đang phát lại tín hiệu...")
            self._advertise()

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if value_handle == self._handle_rx:
                data = self._ble.gatts_read(self._handle_rx)
                self._rx_buffer.extend(data)

    def any(self):
        return len(self._rx_buffer)

    def read(self, sz=None):
        if not self._rx_buffer:
            return None
        if sz is None or sz >= len(self._rx_buffer):
            result = bytes(self._rx_buffer)
            self._rx_buffer.clear()
            return result
        else:
            result = bytes(self._rx_buffer[:sz])
            self._rx_buffer = self._rx_buffer[sz:]
            return result

    def send(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def _advertise(self):
        name_bytes = self._name.encode("utf-8")
        payload = bytearray([0x02, 0x01, 0x06, len(name_bytes) + 1, 0x09]) + name_bytes
        self._ble.gap_advertise(100000, adv_data=payload)
        print(f"[Bluetooth BLE] Đang phát tín hiệu tên: {self._name}")
        