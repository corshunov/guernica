from datetime import datetime, timedelta
import math
from pathlib import Path
import random
import time

import audio
from baby import Baby
from mpv_client import MPVClient
from radar_ld2450 import LD2450
from flower import Flower
import utils


class ControllerBase():
    def __init__(self, cfg_path):
        self.root_dir = Path.cwd()
        self.error_log = self.root_dir / "controller_error.log"
        self.configure(cfg_path)

    def log(self, text):
        with self.error_log.open("a") as f:
            f.write(text)

    def configure(self, cfg_path):
        cfg = utils.load_json(cfg_path)

        self.flag_radar = "radar" in self.cfg
        if self.flag_radar:
            self.init_radar()

        self.flag_brightness = "brightness" in self.cfg
        if self.flag_brightness:
            self.init_brightness()

        self.flag_overlay = "overlay" in self.cfg
        if self.flag_overlay:
            self.init_overlay()

        self.flag_flower = "flower" in self.cfg
        if self.flag_flower:
            self.init_flower()

        self.flag_baby = "baby" in self.cfg
        if self.flag_baby:
            self.init_baby()

        self.flag_hand = "hand" in self.cfg
        if self.flag_hand:
            self.init_hand()

        self.flag_audio = "audio" in self.cfg
        if self.flag_audio:
            self.init_audio()

    def init_radar(self):
        cfg = self.cfg['radar']
        self.RADAR_UARTDEV = cfg['uartdev']
        self.RADAR_DISTANCE_MIN = cfg['distance_min']
        self.RADAR_DISTANCE_MAX = cfg['distance_max']

        r = LD2450(self.RADAR_UARTDEV)
        r.set_bluetooth_off(restart=True)
        r.set_multi_tracking()
        r.set_zone_filtering(mode=0)
        self.radar = r

    def init_brightness(self):
        cfg = self.cfg['brightness']
        self.BRIGHTNESS_MIN = cfg['min']
        self.BRIGHTNESS_MAX = cfg['max']
        self.BRIGHTNESS_DELTA = cfg['delta']
        self.BRIGHTNESS_OSD = cfg['osd']

        self.mpv = MPVClient()
        self.brightness = self.BRIGHTNESS_MIN
        self.brightness_do_not_change_until_dt = datetime.now()
        self.brightness_next_time_check_dt = datetime.now()

    def process_brightness(self):
        if self.dt < self.brightness_do_not_change_until_dt:
            return

        if self.dt > self.brightness_next_time_check_dt:
            remaining_time = float(self.mpv.get_property("time-remaining"))
            if remaining_time is not None:
                self.brightness_next_time_check_dt = self.dt + timedelta(seconds=1)
                if remaining_time < 2:
                    self.brightness_do_not_change_until_dt = self.dt + timedelta(seconds=3)
                    return
            else:
                self.log(f"{self.df}: failed to get property 'time-remaining' from MPV")

        if self.human_present:
            br_new = utils.to_linear(self.distance,
                                     self.RADAR_DISTANCE_MIN, self.RADAR_DISTANCE_MAX,
                                     self.BRIGHTNESS_MAX, self.BRIGHTNESS_MIN))
            br_new = int(br_new)
        else:
            br_new = self.BRIGHTNESS_MIN

        br_diff = utils.clamp(br_new - self.brightness,
                              -self.BRIGHTNESS_DELTA,
                              self.BRIGHTNESS_DELTA)
        self.brightness += br_diff

        if self.BRIGHTNESS_DRM:
            self.mpv.set_drm_brightness(self.brightness, osd=self.BRIGHTNESS_OSD)
        else:
            self.mpv.set_brightness(self.brightness, osd=self.BRIGHTNESS_OSD)

    def init_overlay(self):
        cfg = self.cfg['overlay']
        self.OVERLAY_X_MIN = cfg['x_min']
        self.OVERLAY_X_MAX = cfg['x_max']
        self.OVERLAY_BLINK_X_THRESHOLD = cfg['blink_x_threshold']
        self.OVERLAY_BLINK_PAUSE_MIN = cfg['blink_pause_min']
        self.OVERLAY_BLINK_PAUSE_MAX = cfg['blink_pause_max']
        self.OVERLAY_OSD = cfg['osd']

        self.overlay_blink = False
        self.overlay_x = (self.OVERLAY_X_MIN + self.OVERLAY_X_MAX) // 2
        self.overlay_next_blink_dt = datetime.now()

    def process_overlay(self):
        if self.human_present:
            x_new = utils.to_linear(
                self.angle,
                self.radar.ANGLE_MIN,
                self.radar.ANGLE_MAX,
                self.OVERLAY_X_MIN,
                self.OVERLAY_X_MAX))
            x_new = int(x_new)

            if abs(x_new - self.overlay_x) > self.OVERLAY_BLINK_X_THRESHOLD:
                self.overlay_blink = True

            self.overlay_x = x_new

        if self.dt > self.overlay_next_blink_dt:
            self.overlay_blink = True

        if self.overlay_blink:
            self.mpv.set_x_overlay('halflids', 400, osd=False)
            time.sleep(0.2)
            self.mpv.set_x_overlay('fulllids', 400, osd=False)
            time.sleep(0.2)

        if self.human_present:
            self.mpv.set_x_overlay('eye', self.overlay_x, osd=self.OVERLAY_OSD)

        if self.overlay_blink:
            self.mpv.set_x_overlay('fulllids', -2000, osd=False)
            time.sleep(0.2)
            self.mpv.set_x_overlay('halflids', -2000, osd=False)

            blink_delta = timedelta(seconds=random.randint(self.OVERLAY_BLINK_PAUSE_MIN,
                                                           self.OVERLAY_BLINK_PAUSE_MAX))
            self.overlay_next_blink_dt = self.dt + blink_delta

    def init_flower(self):
        cfg = self.cfg['flower']
        self.FLOWER_PWM_MIN = cfg['pwm_min']
        self.FLOWER_PWM_MAX = cfg['pwm_max']
        self.FLOWER_DUTY_CYCLE_DELTA = cfg['duty_cycle_delta']

        self.flower = Flower(pwm_min=self.FLOWER_PWM_MIN,
                             pwm_max=self.FLOWER_PWM_MAX,
                             initial_dc=0)

    def process_flower(self):
        if self.human_present:
            dc_new = utils.to_linear(self.distance,
                                     self.RADAR_DISTANCE_MIN,
                                     self.RADAR_DISTANCE_MAX,
                                     0, 100))
        else:
            dc_new = 0

        dc_diff = utils.clamp(dc_new - self.flower.dc,
                              -self.FLOWER_DUTY_CYCLE_DELTA,
                              self.FLOWER_DUTY_CYCLE_DELTA)

        self.flower.dc += dc_diff

    def init_baby(self):
        cfg = self.cfg['baby']
        self.BABY_UARTDEV = cfg['uartdev']
        self.BABY_BLINK_PAUSE_MIN = cfg['blink_pause_min']
        self.BABY_BLINK_PAUSE_MAX = cfg['blink_pause_max']
        self.BABY_X_DELTA = cfg['x_delta']

        self.baby = Baby(self.BABY_UARTDEV)
        self.baby_next_blink_dt = datetime.now()

    def process_baby(self):
        if self.human_present:
            x_new = utils.to_linear(
                self.angle,
                self.radar.ANGLE_MIN,
                self.radar.ANGLE_MAX,
                -100, 100)
            x_new = int(x_new)

            x_diff = utils.clamp(x_new - self.baby.x,
                                 -self.BABY_X_DELTA,
                                 self.BABY_X_DELTA)

            self.baby.x += x_diff

        if self.dt > self.baby_next_blink_dt:
            self.baby.blink()

            blink_delta = timedelta(seconds=random.randint(self.BABY_BLINK_PAUSE_MIN,
                                                           self.BABY_BLINK_PAUSE_MAX))
            self.baby_next_blink_dt = self.dt + blink_delta

    def init_audio(self):
        cfg = self.cfg['audio']
        self.AUDIO_DEVICE = cfg['device']
        if self.flag_brightness:
            self.AUDIO_BRIGHTNESS_THRESHOLD = cfg['brightness_threshold']
        self.AUDIO_PAUSE_MIN = cfg['pause_min']
        self.AUDIO_PAUSE_MAX = cfg['pause_max']

        audio.killall()
        self.audio_state = 0
        self.audio_files = None
        self.audio_file = None
        self.audio_proc = None
        self.audio_start_dt = None
        self.audio_pause_until_dt = None

    def process_audio(self):
        if self.audio_state == 0: # not playing
            if self.human_present:
                if self.flag_brightness and self.brightness < self.AUDIO_BRIGHTNESS_THRESHOLD:
                    return

                self.audio_files = audio.get_files(self.root_dir / "audio")
                if len(self.audio_files) == 0:
                    return

                random.shuffle(self.audio_files)

                self.audio_file = self.audio_files.pop()
                self.audio_proc = audio.play(self.AUDIO_DEVICE, self.audio_file)
                self.audio_start_dt = self.dt
                self.audio_state = 1

        elif self.audio_state == 1: # playing audio file
            if self.audio_proc.poll() is not None:
                if self.audio_proc.returncode != 0:
                    log_text = (f"{self.dt}: audio failed "
                                f"(return code {self.audio_proc.returncode})")
                    self.log(log_text)
                    
                    self.audio_state = 0
                elif self.human_present:
                    if len(self.audio_files) != 0:
                        audio_delta = timedelta(random.randint(self.AUDIO_PAUSE_MIN,
                                                               self.AUDIO_PAUSE_MAX))
                        self.audio_pause_until_dt = self.dt + audio_delta
                        self.audio_state = 2
                    else:
                        self.audio_state = 3
                else:
                    self.audio_state = 0

        elif self.audio_state == 2: # paused (there is at least 1 audio file left)
            if self.human_present:
                if self.dt > self.audio_pause_until_dt:
                    self.audio_file = self.audio_files.pop()
                    self.audio_proc = audio.play(self.AUDIO_DEVICE, self.audio_file)
                    self.audio_start_dt = self.dt
                    self.audio_state = 1
            else:
                self.audio_state = 0

        elif self.audio_state == 3: # played all audio files
            if not self.human_present:
                self.audio_state = 0

    def init_hand(self):
        cfg = self.cfg['hand']
        self.HAND_INVERTED = cfg['inverted']

        self.hand = Hand(inverted=self.HAND_INVERTED)

    def process_hand(self):
        pass
        #for ts, num in ts_num_list:
        #    ts_dt = start_dt + timedelta(seconds=ts)
        #    while True:
        #        dt = datetime.now()
        #        print(dt)
        #        if dt > ts_dt:
        #            print(f"!!!!!!!!!!!!!!!!!!!!!!!! {ts}          {num}")
        #            hand.show_number(num)
        #            time.sleep(1.5)
        #            hand.close()
        #            break

        #while True:
        #    if audio_proc.poll() is not None:
        #        break

    def process(self):
        self.text = (f"IN: {self.radar.in_waiting:7}"
                     f" | Human: {'yes' if self.human_present else 'no '}"
                     f" | Distance: {self.distance:7.2f if self.distance else '  ---  '}"
                     f" | Angle: {self.angle:7.2f if self.angle else '  ---  '}")

        if self.flag_brightness:
            self.process_brightness()
            self.text += f" | Brightness: {self.brightness:7}"

        if self.flag_overlay:
            self.process_overlay()
            self.text += (f" | Overlay blink: {'yes' if self.overlay_blink else 'no '}"
                          f" | Overlay X: {self.overlay_x:5}")

        if self.flag_flower:
            self.process_flower()
            self.text += f" | Flower: {self.pwm_value:7}"

        if self.flag_baby:
            self.process_baby()

        if self.flag_hand:
            self.process_hand()
            self.text += f" | Hand state: {self.hand_state:3}"

        if self.flag_audio:
            self.process_audio()
            self.text += f" | Audio state: {self.audio_state:3}"

    def start(self):
        n_radar_failures = 0
        while True:
            self.dt = datetime.now()

            data = self.radar.get_frame()
            if data is None:
                if n_radar_failures >= 10:
                    self.log(f"{self.dt}: radar failed - exiting")
                    sys.exit(1)

                n_radar_failures += 1
                continue

            n_radar_failures = 0

            distance_angle_list = list(
                map(lambda t: (self.radar.distance(t), self.radar.angle(t)), data))

            self.human_present = False
            if distance_angle_list:
                self.distance, self.angle = min(distance_angle_list, key=lambda t: t[0])

                if self.distance < self.RADAR_DISTANCE_MAX:
                    self.human_present = True
            else:
                self.distance = None
                self.angle = None

            self.process()
