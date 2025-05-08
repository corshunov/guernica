from datetime import datetime, timedelta
import time

from adafruit_servokit import ServoKit

import audio


def clamp(v, low, high):
    return max(low, min(high, v))

class Hand():
    N_FINGERS = 5
    CLOSE_V = 20
    OPEN_V = 80

    def __init__(self, uartdev=None):
        self._kit = ServoKit(channels=16)

        self._pos = [self.CLOSE_V] * self.N_FINGERS
        self.close()

    def _finger(self, i):
        return self._kit.servo[i]
        #return self._kit.servo[i+11]

    def _get_finger_pos(self, i):
        return self._pos[i]

    def _set_finger_pos(self, i, v):
        v = clamp(v, 0, 100)
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
        self.pos = [self.CLOSE_V] * self.N_FINGERS

    def open(self):
        self.pos = [self.OPEN_V] * self.N_FINGERS

    def show_number(self, n):
        if (n < 0) or (n > 5):
            raise Exception("Invalid number")

        self.close()

        pos = self.pos

        if n == 5:
            v = self.OPEN_V
        else:
            v = self.CLOSE_V

        pos[0] = v

        for i in range(1, self.N_FINGERS):
            if i <= n:
                v = self.OPEN_V
            else:
                v = self.CLOSE_V

            pos[i] = v

        self.pos = pos


if __name__ == "__main__":
    import sys

    uartdev = ""
    audio_path = ""
    ts_num_list = [
        # (ts, number)
        (2.3, 4),
        (6.0, 1)
    ]

    hand = Hand(uartdev)

    audio_proc = audio.play(path)
    start_dt = datetime.now()

    for ts, num in timestamps:
        ts_dt = start_dt + timedelta(seconds=ts)
        while True:
            if datetime.now() > ts_dt:
                print(ts, num)
                hand.show_number(num)
                time.sleep(1.5)
                hand.close()
                break

    while True:
        if audio_proc.poll() is not None:
            break
