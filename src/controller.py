from datetime import datetime, timedelta
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

    ANGLE_FACTOR = 2/3

    BRMIN = 15000
    BRMAX = 65535
    BRDELTA = 1000

    OVERLAYXMIN = 650
    OVERLAYXMAX = 950

    PWMMAX = 2290
    PWMMIN = 580

    PAUSEMIN = 4
    PAUSEMAX = 8

    def __init__(self, uartdev):
        self.radar = self._init_radar(uartdev)
        self.mpv = MPVClient()
        #self.pwm = HardwarePWM(pwm_channel=0, hz=50, chip=0)

    def _init_radar(self, uartdev):
        r = LD2450(uartdev)
        r.set_bluetooth_off(restart=True)
        r.set_multi_tracking()
        r.set_zone_filtering(mode=0)
        return r

    def start(self):
        distance = self.DMAX
        angle = 0

        br = self.BRMIN

        next_blink_dt = datetime.now()
        x = int((self.OVERLAYXMAX + self.OVERLAYXMIN) / 2)

        audio_state = 0

        while True:
            data = self.radar.get_frame()
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

            print(f"IN: {self.radar.in_waiting:7} | "
                  f"Human: {'yes' if human_present else 'no '} | "
                  f"Distance: {distance:7.2f} | Angle: {angle:7.2f}", end=" | ")

            # ==========
            # Brightness

            #br_prev = br
            #br_new = int(
            #    to_linear(distance, self.DMIN, self.DMAX, self.BRMAX, self.BRMIN))
            #br_diff = clamp(br_new - br_prev, -self.BRDELTA, self.BRDELTA)
            #br += br_diff

            #self.mpv.set_drm_brightness(br, osd=True)

            #print(f"Brightness: {br:7}")

            # =====
            # Eye

            blink = False
            if human_present:
                x_new = int(to_linear(
                    angle,
                    -math.pi/2*self.ANGLE_FACTOR,
                    math.pi/2*self.ANGLE_FACTOR,
                    self.OVERLAYXMIN,
                    self.OVERLAYXMAX))

                if abs(x_new - x) > 100:
                    blink = True

                x = x_new

            #if dt > next_blink_dt:
                #blink = True

            if blink:
                self.mpv.set_x_overlay('halflids', 400, osd=True)
                time.sleep(0.2)
                self.mpv.set_x_overlay('fulllids', 400, osd=True)
                time.sleep(0.2)

            if human_present:
                self.mpv.set_x_overlay('eye', x, osd=True)

            if blink:
                self.mpv.set_x_overlay('fulllids', -2000, osd=True)
                time.sleep(0.2)
                self.mpv.set_x_overlay('halflids', -2000, osd=True)

                #delta = random.randint(5,10) 
                delta = 3
                next_blink_dt = dt + timedelta(seconds=delta)

            print(f"Blink: {'yes' if blink else 'no '} | Overlay X: {x:5}")

            # =====
            # Servo

            #if human_present:
            #    pulse = to_linear(angle, -math.pi/2, math.pi/2, self.PWMMAX, self.PWMMIN)
            #    p = pulse * 100 / 20000
            #    self.pwm.change_duty_cycle(p)
            #else:
            #    pass
            #    # TODO
            #    # If no human present, still output PWM signal during 1 second.
            #    # After, do not output PWM signal.

            # print(f"PWM: {p:7}")

            # =====
            # Audio

            #if audio_state == 0: # not playing
            #    if human_present:
            #        audio_files = audio.get_files()
            #        audio_files = random.shuffle(audio_files)
            #        path = audio_files.pop()
            #        audio_proc = audio.play(path)
            #        audio_state = 1
            #elif audio_state == 1: # playing audio file
            #    if audio_proc.poll() is not None:
            #        if human_present:
            #            if len(audio_files) != 0:
            #                pause_end_dt = dt + random.randint(self.PAUSEMIN, self.PAUSEMAX)
            #                audio_state = 2
            #            else:
            #                 audio_state = 3
            #        else:
            #            audio_state = 0
            #elif audio_state == 2: # paused (there is at least 1 audio file left)
            #    if human_present:
            #        if dt > pause_end_dt:
            #            path = audio_files.pop()
            #            audio_proc = audio.play(path)
            #            audio_state = 1
            #    else:
            #        audio_state = 0
            #elif audio_state == 3: # played all audio files
            #    if not human_present:
            #        audio_state = 0

            # print(f"Audio state: {audio_state:3}")

            # ==========

if __name__ == "__main__":
    import sys

    try:
        uartdev = sys.argv[1]
    except:
        print("No argument for UART device provided")
        sys.exit(1)

    ctl = Controller(uartdev)
    ctl.start()
