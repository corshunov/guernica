import time

from adafruit_servokit import ServoKit
import RPi.GPIO as GPIO

import utils


GPIO.setmode(GPIO.BCM)

class Hand():
    N_FINGERS = 5

    N = None
    C = 20
    O = 80

    DELAY = 0.5

    POSITIONS = {
        "none":  [N,N,N,N,N],
        "close": [C,C,C,C,C],
        "open":  [O,O,O,O,O],
        "0":     [C,C,C,C,C],
        "1":     [C,O,C,C,C],
        "2":     [C,O,O,C,C],
        "3":     [C,O,O,O,C],
        "4":     [C,O,O,O,O],
        "5":     [O,O,O,O,O],
        "6":     [O,C,C,C,O],
        "7":     [O,O,C,C,C],
        "8":     [O,O,O,C,C],
        "9":     [O,O,O,O,C],
    }

    def __init__(self, inverted=False, power_pin=10):
        self.inverted = inverted

        self._power_pin = power_pin
        self._position = self.POSITIONS['none']
        self._stopped = True

        GPIO.setup(self._power_pin, GPIO.OUT)
        self.set_position_by_name("close")

    def _finger(self, index):
        return self._kit.servo[index]

    @property
    def position(self):
        return self._position.copy()

    @property
    def stopped(self):
        return self._stopped

    def set_finger_position(self, index, value):
        if self._stopped:
            self.start()

        v = utils.clamp(value, 0, 100)

        if self.inverted:
            v = 100 - v

        self._position[index] = v

        if index == 0:
            v = 100 - v

        angle = (100 - v) / 100 * 180
        self._finger(index).angle = int(angle)

    def set_position(self, position, stop=False):
        for i in range(self.N_FINGERS):
            self.set_finger_position(i, position[i])

        if stop:
            time.sleep(self.DELAY)
            self.stop()

    def set_position_by_name(self, name, stop=False):
        if name not in self.POSITIONS:
            print(f"Position '{name}' not found")
            return

        position = self.POSITIONS[name]
        self.set_position(position, stop=stop)

    def start(self):
        GPIO.output(self._power_pin, GPIO.HIGH)
        self._kit = ServoKit(channels=16)
        self.set_position(self._position)
        self._stopped = False

    def stop(self):
        for i in range(self.N_FINGERS):
            self._finger(i).angle = None
        GPIO.output(self._power_pin, GPIO.LOW)
        self._stopped = True


if __name__ == "__main__":
    hand = Hand(inverted=False)
    time.sleep(3)

    for i in range(10):
        print(f'Showing {i}\n')
        hand.set_position("close")
        time.sleep(0.5)
        hand.set_position(str(i))
        time.sleep(3)

    hand.set_position("close", stop=True)
