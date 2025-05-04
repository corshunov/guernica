from smbus2 import SMBus


class BrightnessController():
    ADDRESS = 0x37
    REGISTER = 0x51

    def __init__(self, bus_num):
        self.bus_num = bus_num

    def _checksum(self, message):
        v = self.ADDRESS*2 ^ self.REGISTER
        for i in message:
            v = v ^ i

        return v

    def set(self, value):
        message = [0x84, 0x03, 0x10, 0x00, value]
        checksum = self._checksum(message)
        message.append(checksum)

        with SMBus(self.bus_num) as bus:
            bus.write_i2c_block_data(self.ADDRESS, self.REGISTER, message)

if __name__ == "__main__":
    import sys

    try:
        bus_num = sys.argv[1]
    except:
        print("No argument for I2C bus number provided")
        sys.exit(1)

    try:
        bus_num = int(bus_num)
        if bus_num < 0:
            raise Exception
    except:
        print("I2C bus number argument must be integer no less than 0")
        sys.exit(1)

    ctl = BrightnessController(bus_num=2)
    while True:
        try:
            v = input("Type brightness value [0 - 100]: ")
            try:
                v = int(v)
            except:
                print("Value must be integer!")
                continue

            v = max(0, min(100, v))
            print(f"Setting brightness to {v}.")
            ctl.set(v)
        except KeyboardInterrupt:
            print("\nExiting...\n")
            break
