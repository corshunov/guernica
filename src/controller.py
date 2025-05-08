import math
import time

from mpv_client import MPVClient
from radar_ld2450 import LD2450
from rpi_hardware_pwm import HardwarePWM


class Controller():
    DMIN = 500
    DMAX = 3000
    BRMIN = 15000
    BRMAX = 65535
    BRDELTA = 1000
    PWMMAX = 2290
    PWMMIN = 580

    @staticmethod
    def distance(t):
        return math.sqrt(t[0]**2 + t[1]**2)
    
    @staticmethod
    def angle(t):
        return math.atan(t[0]/t[1])

    @staticmethod
    def clamp(v, low, high):
        return max(low, min(high, v))

    @staticmethod
    def pulse2pwm(pulse):
        pwm = pulse * 100 / 20000
        return pwm

    @classmethod
    def to_linear(cls, v, low, high, begin, end):
        v = cls.clamp(v, low, high)
        v = (v - low) / (high - low) * (end - begin) + begin
        return v

    @classmethod
    def dist2br(cls, d):
        br = int(cls.to_linear(d, self.DMIN, self.DMAX, self.BRMAX, self.BRMIN))
        return br

    def __init__(self, uartdev, verbose=True):
        self._uartdev = uartdev
        self._verbose = verbose

        self._drange = self._dmax - self._dmin

        self.radar = self._get_radar()
        self.mpv = MPVController()

        self.pwm = HardwarePWM(pwm_channel=0,hz=50,chip=0)

    def _get_radar(self):
        r = LD2450(self._uartdev)
        r.set_bluetooth_off(restart=True)
        r.set_multi_tracking()
        r.set_zone_filtering(mode=0)
        return r

    def start(self):
        br = 0
        while True:
            data = self.get_frame()
            if data is None:
                continue

            distance_angle_list = list(map(lambda t: (self.distance(t), self.angle(t)), data))
            print(distance_angle_list)
            if distance_angle_list:
                distance, angle = min(distance_angle_list, key=lambda t: t[0])

                # ==========

                br_prev = br
                br_new = self.dist2br(distance)
                br_diff = cls.clamp(br_new - br_prev, -self.BRDELTA, self.BRDELTA)
                br += br_diff

                self.mpv.set_drm_brightness(br, osd=True)

                # ==========

                pulse = self.to_linear(angle, -math.pi/2, math.pi/2, self.PWMMAX, self.PWMMIN)
                p = self.pulse_to_pwm(pulse)
                self.pwm.change_duty_cycle(p)

                # ==========

                if self.verbose:
                    print(f"IN: {self.radar.in_waiting:7} | "
                          f"Dist: {distance:7} | Brightness: {br:7} | "
                          f"Angle: {angle:7} | PWM: {p:7}")

if __name__ == "__main__":
    import sys

    try:
        uartdev = sys.argv[1]
    except:
        print("No argument for UART device provided")
        sys.exit(1)

    ctl = Controller(uartdev)
    ctl.start()
