from datetime import datetime
import math
import random
import time

from mpv_client import MPVClient
from radar_ld2450 import LD2450
from rpi_hardware_pwm import HardwarePWM
import audio


def clamp(v, low, high):
    return max(low, min(high, v))

def to_linear(v, low, high, begin, end):
    v = clamp(v, low, high)
    v = (v - low) / (high - low) * (end - begin) + begin
    return v

class Controller():
    DMIN = 500
    DMAX = 3000
    BRMIN = 15000
    BRMAX = 65535
    BRDELTA = 1000
    PWMMAX = 2290
    PWMMIN = 580
    PAUSEMIN = 4
    PAUSEMAX = 8

    def __init__(self, uartdev):
        self.radar = self._init_radar(uartdev)
        self.mpv = MPVController()
        self.pwm = HardwarePWM(pwm_channel=0, hz=50, chip=0)

    def _init_radar(self, uartdev):
        r = LD2450(uartdev)
        r.set_bluetooth_off(restart=True)
        r.set_multi_tracking()
        r.set_zone_filtering(mode=0)
        return r

    def start(self):
        distance = self.DMAX
        angle = 0
        br = 0
        audio_state = 0
        while True:
            data = self.get_frame()
            if data is None:
                continue

            dt = datetime.now()

            distance_angle_list = list(
                map(lambda t: (self.radar.distance(t), self.radar.angle(t)), data))

            human_present = False
            if distance_angle_list:
                distance, angle = min(distance_angle_list, key=lambda t: t[0])
                if distance < self.DMAX:
                    human_present = True

            if not human_present:
                distance = self.DMAX
                # angle remains the same

            # ==========
            # Brightness

            br_prev = br
            br_new = int(
                to_linear(distance, self.DMIN, self.DMAX, self.BRMAX, self.BRMIN))
            br_diff = clamp(br_new - br_prev, -self.BRDELTA, self.BRDELTA)
            br += br_diff

            self.mpv.set_drm_brightness(br, osd=True)

            # =====
            # Servo

            if human_present:
                pulse = to_linear(angle, -math.pi/2, math.pi/2, self.PWMMAX, self.PWMMIN)
                p = pulse * 100 / 20000
                self.pwm.change_duty_cycle(p)
            else:
                # TODO
                # If no human present, still output PWM signal during 1 second.
                # After, do not output PWM signal.

            # =====
            # Audio

            if audio_state == 0: # not playing
                if human_present:
                    audio_files = audio.get_files()
                    audio_files = random.shuffle(audio_files)
                    path = audio_files.pop()
                    audio_proc = audio.play(path)
                    audio_state = 1
            elif audio_state == 1: # playing audio file
                if audio_proc.poll() is not None:
                    if human_present:
                        if len(audio_files) != 0:
                            pause_end_dt = dt + random.randint(self.PAUSEMIN, self.PAUSEMAX)
                            audio_state = 2
                        else:
                             audio_state = 3
                    else:
                        audio_state = 0
            elif audio_state == 2: # paused (there is at least 1 audio file left)
                if human_present:
                    if dt > pause_end_dt:
                        path = audio_files.pop()
                        audio_proc = audio.play(path)
                        audio_state = 1
                else:
                    audio_state = 0
            elif audio_state == 3: # played all audio files
                if not human_present:
                    audio_state = 0

            # ==========

            print(f"IN: {self.radar.in_waiting:7} | "
                  f"Human: {human_present:<7} | "
                  f"Distance: {distance:7} | Brightness: {br:7} | "
                  f"Angle: {angle:7} | PWM: {p:7} | "
                  f"Audio state: {audio_state:3}")

if __name__ == "__main__":
    import sys

    try:
        uartdev = sys.argv[1]
    except:
        print("No argument for UART device provided")
        sys.exit(1)

    ctl = Controller(uartdev)
    ctl.start()
