from smbus2 import SMBus

ADDRESS = 0x37
REGISTER = 0x51

def set_brightness(i2c_bus, value):
    message = [0x84, 0x03, 0x10, 0x00, value]

    checksum = ADDRESS*2 ^ REGISTER
    for v in message:
        checksum = checksum ^ v

    message.append(checksum)

    with SMBus(i2c_bus) as bus:
        bus.write_i2c_block_data(ADDRESS, REGISTER, message)

if __name__ == "__main__":
    import sys

    try:
        i2c_bus = sys.argv[1]
    except:
        print("No argument for I2C bus number provided")
        sys.exit(1)

    try:
        i2c_bus = int(i2c_bus)
        if i2c_bus < 0:
            raise Exception
    except:
        print("I2C bus number argument must be integer no less than 0")
        sys.exit(1)

    while True:
        try:
            value = input("Type brightness value [0 - 100]: ")
            try:
                value = int(value)
            except:
                print("Value must be integer!")
                continue

            value = max(0, min(100, value))
            print(f"Setting brightness to {value}.")
            set_brightness(i2c_bus, value)
        except KeyboardInterrupt:
            print("\nExiting...\n")
            break
