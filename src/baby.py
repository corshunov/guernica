import serial

import utils


class Baby():
    def __init__(self, uartdev):
        self.uartdev = uartdev
        self._ser = self._get_serial()

        self.x = 120

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

    def blink(self):
        cmd = b"blink\n"
        self._ser.write(cmd)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        value = utils.clamp(value, 80, 150)
        cmd = f"{value}\n".encode()
        self._ser.write(cmd)

        self._x = value


if __name__ == "__main__":
    import sys
    import time

    try:
        uartdev = sys.argv[1]
    except:
        print("No argument for UART device provided")
        sys.exit(1)

    baby = Baby(uartdev)
    for _ in range(5):
        baby.blink()
        time.sleep(3)
