import math

from rpi_hardware_pwm import HardwarePWM

import utils


class Servo():
    def __init__(self, pwm_min, pwm_max, channel=0, hz=50, chip=0):
        self._pwm = HardwarePWM(pwm_channel=channel, hz=hz, chip=chip)

    def release(self):
        self._pwm.change_duty_cycle(0)

    def set_angle(self, angle):
        pulse = utils.to_linear(angle,
                                -math.pi/2, math.pi/2,
                                pwm_max, pwm_min)
        p = pulse * 100 / 20_000
        self._pwm.change_duty_cycle(p)
