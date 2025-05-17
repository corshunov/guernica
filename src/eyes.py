import serial

import utils


class Eyes():
    def __init__(self, uartdev, remote=True):
        self.uartdev = uartdev
        self._ser = self._get_serial()

        if remote:
            mode_cmd = b"remote"
        else:
            mode_cmd = b"local"
        for _ in range(3):
            self._ser.write(mode_cmd)
            time.sleep(0.5)

    def _get_serial(self):
        try:
            return serial.Serial(self.uartdev, 9600, timeout=1)
        except:
            raise Exception(f"Failed to open UART device '{uartdev}'.") from None

    def __del__(self):
        try:
            self._ser.close()
        except:
            pass

    @property
    def in_waiting(self):
        return self._ser.in_waiting

    def blink(self):
        self._ser.write(b"blink")

    def set_angle(self, angle):
        value = utils.clamp(angle, 70, 150)
        value = str(value).encode()
        self._ser.write(value)


if __name__ == "__main__":
    import sys
    import time

    try:
        uartdev = sys.argv[1]
    except:
        print("No argument for UART device provided")
        sys.exit(1)

    eyes = Eyes(uartdev)
    for _ in range(5):
        eyes.blink()
        time.sleep(3)
