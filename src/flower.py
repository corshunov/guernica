import math

from rpi_hardware_pwm import HardwarePWM

import utils


class Flower(HardwarePWM):
    def __init__(self, pwm_min, pwm_max, initial_dc=None):
        super().__init__(channel=0, hz=50, chip=0)

        self._pwm_min = pwm_min
        self._pwm_max = pwm_max
        self._per_micro = 1 / float(self._hz) * 10**6
        self._dc = 0
        self._stopped = True

        if initial_dc is not None:
            self.dc = initial_dc

    def percent2dc(self, value):
        value = utils.clamp(value, 0, 100)
        pulse = utils.to_linear(value,
                                0, 100,
                                self._pwm_min, self._pwm_max)

        dc = pulse * 100 / self._per_micro
        dc = int(dc)
        return dc

    def dc2percent(self, value):
        pulse = value * self._per_micro / 100
        pulse = utils.clamp(pulse, self._pwm_min, self._pwm_max)

        percent = utils.to_linear(pulse,
                                  self._pwm_min, self._pwm_max,
                                  0, 100)
        percent = int(percent)
        return percent

    def stop(self):
        self.change_duty_cycle(0)
        self.echo(0, os.path.join(self.pwm_dir, "enable"))
        self._stopped = True

    def start(self, initial_dc):
        self.change_duty_cycle(initial_dc)
        self.echo(1, os.path.join(self.pwm_dir, "enable"))
        self._stopped = False

    @property
    def dc(self):
        return self._dc

    @dc.setter
    def dc(self, value):
        self._dc = utils.clamp(value, 0, 100)

        if (self._dc == 0) and (not self._stopped):
            self.stop()
        else:
            dc = self.percent2dc(self._dc)

            if self._stopped:
                self.start(dc)
            else:
                self.change_duty_cycle(dc)
