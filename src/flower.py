import math

from rpi_hardware_pwm import HardwarePWM

import utils


class Flower(HardwarePWM):
    def __init__(self):
        super().__init__(channel=0, hz=50, chip=0)

        self._pwm = 0
        self._stopped = True

    def pwm2dc(self, value):
        dc = value * 100 / self.per_micro
        dc = int(dc)
        return dc

    def dc2pwm(self, value):
        pwm = value * self.per_micro / 100
        pwm = int(pwm)
        return pwm

    @property
    def per_micro(self):
        return 1. / float(self._hz) * 10**6

    @property
    def pwm(self):
        return self._pwm

    @pwm.setter
    def pwm(self, value):
        self._pwm = value

        if self._pwm == 0:
            if self._stopped:
                return

            self.stop()
            self._stopped = True
        else:
            dc = self.pwm2dc(self._pwm)

            if self._stopped:
                self.start(dc)
                self._stopped = False
            else:
                self.change_duty_cycle(dc)
