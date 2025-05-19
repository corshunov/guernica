from adafruit_servokit import ServoKit
import RPi.GPIO as GPIO

import utils


GPIO.setmode(GPIO.BCM)

class Hand():
    N_FINGERS = 5

    C = 20
    O = 80

    POSITIONS = {
        "close": [C,C,C,C,C],
        "open":  [O,O,O,O,O],
        0:       [C,C,C,C,C],
        1:       [C,O,C,C,C],
        2:       [C,O,O,C,C],
        3:       [C,O,O,O,C],
        4:       [C,O,O,O,C],
        5:       [O,O,O,O,O],
        6:       [O,C,C,C,O],
        7:       [O,O,C,C,C],
        8:       [O,O,O,C,C],
        9:       [O,O,O,O,C],
    }

    def __init__(self, inverted=False, power_pin=10):
        self._kit = ServoKit(channels=16)
        self._inverted = inverted

        self._power_pin = power_pin
        GPIO.setup(self._power_pin, GPIO.OUT)

        self._pos = [None,None,None,None,None]
        self.close()

    def _finger(self, i):
        return self._kit.servo[i]

    def _finger_pos(self, i):
        return self._pos[i]

    def _set_finger_pos(self, i, v):
        v = utils.clamp(v, 0, 100)
        if self._inverted:
            v = 100 - v
        self._pos[i] = v

        if i == 0:
            v = 100 - v

        angle = (100 - v) / 100 * 180
        self._finger(i).angle = int(angle)

    @property
    def pos(self):
        return self._pos.copy()

    @pos.setter
    def pos(self, pos):
        for i in range(self.N_FINGERS):
            self._set_finger_pos(i, pos[i])

    def close(self):
        self.pos = self.POSITIONS["close"]

    def open(self):
        self.pos = self.POSITIONS["open"]

    def show_digit(self, n):
        if (n < 0) or (n > 9):
            return

        self.pos = self.POSITIONS[n]

    def stop(self):
        GPIO.output(self._power_pin, GPIO.LOW)
        for i in range(self.N_FINGERS):
            self._finger(i).angle = None

    def start(self):
        GPIO.output(self._power_pin, GPIO.HIGH)
        self.pos = self._pos


if __name__ == "__main__":
    import time

    hand = Hand(inverted=True)
    time.sleep(3)

    for i in range(10):
        hand.close()
        time.sleep(0.5)
        hand.show_digit(i)
        time.sleep(3)

    hand.close()
