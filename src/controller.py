from datetime import datetime, timedelta
import math
from pathlib import Path
import random
import time

import serial

import audio
from hand import Hand
from mpv_client import MPVClient
from radar_ld2450 import LD2450
from rpi_hardware_pwm import HardwarePWM
import utils


class Controller():
    def __init__(self, base_dpath):
        self.base_dpath = Path(base_dpath)
        self.error_log = self.base_dpath / "controller_error.log"

        self.configure()

    def __del__(self):
        if self.flag_flower:
            try:
                self.flower.stop()
            except:
                pass

        if self.flag_baby:
            try:
                self.baby.close()
            except:
                pass

        if self.flag_horse:
            try:
                self.horse.close()
            except:
                pass

    def log(self, text):
        with self.error_log.open("a") as f:
            f.write(f"{text}\n")

    def configure(self):
        path = self.base_dpath / "conf.cfg"
        self.cfg = utils.load_json(path)

        self.flag_radar = "radar" in self.cfg
        if self.flag_radar:
            self.init_radar()

        self.flag_video = "video" in self.cfg
        if self.flag_video:
            self.flag_video_brightness = "brightness" in self.cfg['video']
            self.flag_video_overlay = "overlay" in self.cfg['video']

            self.init_video()
        else:
            self.flag_video_brightness = False
            self.flag_video_overlay = False

        self.flag_audio = "audio" in self.cfg
        if self.flag_audio:
            self.init_audio()

        self.flag_flower = "flower" in self.cfg
        if self.flag_flower:
            self.init_flower()

        self.flag_baby = "baby" in self.cfg
        if self.flag_baby:
            self.init_baby()

        self.flag_horse = "horse" in self.cfg
        if self.flag_horse:
            self.init_horse()

        self.flag_hand = "hand" in self.cfg
        if self.flag_hand:
            self.init_hand()

    def init_radar(self):
        cfg = self.cfg['radar']
        self.RADAR_UARTDEV = cfg['uartdev']
        self.RADAR_DISTANCE_MIN = cfg['distance_min']
        self.RADAR_DISTANCE_MAX = cfg['distance_max']
        self.RADAR_DISTANCE_DELTA = cfg['distance_delta']
        self.RADAR_DISTANCE_ACTION = cfg['distance_action']

        r = LD2450(self.RADAR_UARTDEV)
        r.set_bluetooth_off(restart=True)
        r.set_multi_tracking()
        r.set_zone_filtering(mode=0)
        self.radar = r

        self.radar_n_failures = 0
        self.human_present = False
        self.human_present_reliable = False
        self.radar_distance = None
        self.radar_distance_reliable = self.RADAR_DISTANCE_MAX
        self.radar_angle = None

        print("Radar initialized")

    def process_radar(self):
        data = self.radar.get_data()
        if data is None:
            self.radar_n_failures += 1
            if self.radar_n_failures < 5:
                return False

            text = f"{self.dt}: exiting due to {self.radar_n_failures} consequent radar failures"
            print(text)
            self.log(text)
            sys.exit(1)

        self.radar_n_failures = 0

        distance_angle_list = list(
            map(lambda t: (self.radar.distance(t), self.radar.angle(t)), data))

        if distance_angle_list:
            self.radar_distance, self.radar_angle = \
                min(distance_angle_list, key=lambda t: t[0])
        else:
            self.radar_distance = None
            self.radar_angle = None

        if (self.radar_distance is not None) and \
           (self.radar_distance < self.RADAR_DISTANCE_MAX):
            self.human_present = True
        else:
            self.human_present = False

        if self.human_present:
            radar_distance_reliable_new = utils.clamp(
                self.radar_distance,
                self.RADAR_DISTANCE_MIN,
                self.RADAR_DISTANCE_MAX)
        else:
            radar_distance_reliable_new = self.RADAR_DISTANCE_MAX

        radar_distance_reliable_diff = utils.clamp(
            radar_distance_reliable_new - self.radar_distance_reliable,
            -self.RADAR_DISTANCE_DELTA, self.RADAR_DISTANCE_DELTA)
        self.radar_distance_reliable += radar_distance_reliable_diff

        if self.radar_distance_reliable < self.RADAR_DISTANCE_MAX:
            self.human_present_reliable = True
        else:
            self.human_present_reliable = False

        return True

    def init_video(self):
        self.mpv = MPVClient()

        if self.flag_video_brightness:
            self.init_brightness()

        if self.flag_video_overlay:
            self.init_overlay()

    def process_video(self):
        if self.flag_video_brightness:
            self.process_brightness()

        if self.flag_video_overlay:
            self.process_overlay()

    def init_brightness(self):
        cfg = self.cfg['video']['brightness']
        self.BRIGHTNESS_MIN = cfg['min']
        self.BRIGHTNESS_MAX = cfg['max']
        self.BRIGHTNESS_DELTA = cfg['delta']
        self.BRIGHTNESS_DRM = cfg['drm']
        self.BRIGHTNESS_OSD = cfg['osd']

        self.brightness = self.BRIGHTNESS_MIN
        self.brightness_do_not_change_until_dt = datetime.now()
        self.brightness_next_time_check_dt = datetime.now()

        if self.BRIGHTNESS_DRM:
            self.mpv.set_drm_brightness(self.brightness, osd=self.BRIGHTNESS_OSD)
        else:
            self.mpv.set_brightness(self.brightness, osd=self.BRIGHTNESS_OSD)

        print("Video brightness initialized")

    def process_brightness(self):
        if self.dt < self.brightness_do_not_change_until_dt:
            return

        if self.dt > self.brightness_next_time_check_dt:
            remaining_time = self.mpv.get_property("time-remaining")
            if remaining_time is not None:
                self.brightness_next_time_check_dt = self.dt + timedelta(seconds=1)
                if remaining_time < 2:
                    self.brightness_do_not_change_until_dt = self.dt + timedelta(seconds=3)
                    return
            else:
                self.log(f"{self.df}: failed to get property 'time-remaining' from MPV")

        #if self.human_present:
        #    br_new = utils.linear_map(
        #        self.radar_distance,
        #        self.RADAR_DISTANCE_MIN, self.RADAR_DISTANCE_MAX,
        #        self.BRIGHTNESS_MAX, self.BRIGHTNESS_MIN)
        #    br_new = int(br_new)
        #else:
        #    br_new = self.BRIGHTNESS_MIN

        br_new = utils.linear_map(
            self.radar_distance_reliable,
            self.RADAR_DISTANCE_MIN, self.RADAR_DISTANCE_MAX,
            self.BRIGHTNESS_MAX, self.BRIGHTNESS_MIN)
        br_new = int(br_new)

        #br_diff = utils.clamp(
        #    br_new - self.brightness,
        #    -self.BRIGHTNESS_DELTA,
        #    self.BRIGHTNESS_DELTA)

        br_diff = br_new - self.brightness

        self.brightness += br_diff

        if br_diff != 0:
            if self.BRIGHTNESS_DRM:
                self.mpv.set_drm_brightness(self.brightness, osd=self.BRIGHTNESS_OSD)
            else:
                self.mpv.set_brightness(self.brightness, osd=self.BRIGHTNESS_OSD)

    def init_overlay(self):
        cfg = self.cfg['video']['overlay']
        self.OVERLAY_X_MIN = cfg['x_min']
        self.OVERLAY_X_MAX = cfg['x_max']
        self.OVERLAY_BLINK_X_THRESHOLD = cfg['blink_x_threshold']
        self.OVERLAY_BLINK_PAUSE_MIN = cfg['blink_pause_min']
        self.OVERLAY_BLINK_PAUSE_MAX = cfg['blink_pause_max']
        self.OVERLAY_OSD = cfg['osd']

        self.overlay_x = (self.OVERLAY_X_MIN + self.OVERLAY_X_MAX) // 2
        self.overlay_blink = False
        self.overlay_blink_speed = None
        self.overlay_next_blink_dt = datetime.now()

        print("Video overlay initialized")

    def process_overlay(self):
        if self.human_present:
            x_new = utils.linear_map(
                self.angle,
                self.radar.ANGLE_MIN, self.radar.ANGLE_MAX,
                self.OVERLAY_X_MIN, self.OVERLAY_X_MAX)
            x_new = int(x_new)

            if abs(x_new - self.overlay_x) > self.OVERLAY_BLINK_X_THRESHOLD:
                self.overlay_blink = True

            self.overlay_x = x_new

        if self.dt > self.overlay_next_blink_dt:
            self.overlay_blink = True
            self.overlay_blink_speed = utils.linear_map(
                random.random(), 0, 1, 0.05, 0.2)

        if self.overlay_blink:
            self.mpv.set_x_overlay('halfhalflids', 400)
            time.sleep(self.overlay_blink_speed)
            self.mpv.set_x_overlay('halflids', 400)
            time.sleep(self.overlay_blink_speed)
            self.mpv.set_x_overlay('fulllids', 400)
            time.sleep(self.overlay_blink_speed)

        if self.human_present:
            self.mpv.set_x_overlay('eye', self.overlay_x, osd=self.OVERLAY_OSD)

        if self.overlay_blink:
            self.mpv.set_x_overlay('fulllids', -2000)
            time.sleep(self.overlay_blink_speed)
            self.mpv.set_x_overlay('halflids', -2000)
            time.sleep(self.overlay_blink_speed)
            self.mpv.set_x_overlay('halfhalflids', -2000)

            blink_delta = timedelta(seconds=random.randint(
                self.OVERLAY_BLINK_PAUSE_MIN,
                self.OVERLAY_BLINK_PAUSE_MAX))
            self.overlay_next_blink_dt = self.dt + blink_delta

    def init_audio(self):
        cfg = self.cfg['audio']
        self.AUDIO_DEVICE = cfg['device']
        #if self.flag_video_brightness:
        #    self.AUDIO_BRIGHTNESS_THRESHOLD = cfg['brightness_threshold']
        self.AUDIO_PAUSE_MIN = cfg['pause_min']
        self.AUDIO_PAUSE_MAX = cfg['pause_max']

        audio.killall()
        self.audio_state = 0
        self.audio_state_prev = 0
        self.audio_files = None
        self.audio_file = None
        self.audio_proc = None
        self.audio_start_dt = None
        self.audio_pause_until_dt = None

        print("Audio initialized")

    def process_audio(self):
        self.audio_state_prev = self.audio_state

        if self.audio_state == 0: # not playing
            self.audio_files = None

            #if self.human_present:
            if self.human_present_reliable:
                #if self.flag_video_brightness and \
                #   (self.brightness < self.AUDIO_BRIGHTNESS_THRESHOLD):
                #    return

                self.audio_files = audio.get_files(self.base_dpath / "media" / "audio")
                if len(self.audio_files) == 0:
                    return

                random.shuffle(self.audio_files)

                self.audio_file = self.audio_files.pop(0)
                self.audio_proc = audio.play(self.AUDIO_DEVICE, self.audio_file)
                self.audio_start_dt = self.dt
                self.audio_state = 1

        elif self.audio_state == 1: # playing audio file
            if self.audio_proc.poll() is not None:
                if self.audio_proc.returncode != 0:
                    text = f"{self.dt}: audio failed " \
                           f"(return code {self.audio_proc.returncode})"
                    print(text)
                    self.log(text)
                    
                    self.audio_state = 0
                #elif self.human_present:
                elif self.human_present_reliable:
                    if len(self.audio_files) != 0:
                        audio_delta = timedelta(
                            seconds=random.randint(self.AUDIO_PAUSE_MIN,
                                                   self.AUDIO_PAUSE_MAX))
                        self.audio_pause_until_dt = self.dt + audio_delta
                        self.audio_state = 2
                    else:
                        self.audio_state = 3
                else:
                    self.audio_state = 0

        elif self.audio_state == 2: # paused (there is at least 1 audio file left)
            #if self.human_present:
            if self.human_present_reliable:
                if self.dt > self.audio_pause_until_dt:
                    self.audio_file = self.audio_files.pop(0)
                    self.audio_proc = audio.play(self.AUDIO_DEVICE, self.audio_file)
                    self.audio_start_dt = self.dt
                    self.audio_state = 1
            else:
                self.audio_state = 0

        elif self.audio_state == 3: # played all audio files
            #if not self.human_present:
            if not self.human_present_reliable:
                self.audio_state = 0

    def init_flower(self):
        cfg = self.cfg['flower']
        self.FLOWER_DC_MIN = cfg['dc_min']
        self.FLOWER_DC_MAX = cfg['dc_max']
        self.FLOWER_DC_DELTA = cfg['dc_delta']

        self.flower = HardwarePWM(channel=0, hz=50, chip=0)
        self.flower_dc = self.FLOWER_DC_MIN
        self.flower.start(self.flower_dc)
        self.flower_stopped = False

        print("Flower initialized")

    def process_flower(self):
        if self.human_present:
            dc_new = utils.linear_map(
                self.radar_distance,
                self.RADAR_DISTANCE_MIN,
                self.RADAR_DISTANCE_MAX,
                self.FLOWER_DC_MAX,
                self.FLOWER_DC_MIN)
        else:
            dc_new = self.FLOWER_DC_MIN

        dc_diff = utils.clamp(dc_new - self.flower_dc,
                              -self.FLOWER_DC_DELTA,
                              self.FLOWER_DC_DELTA)

        self.flower_dc += dc_diff

        if self.flower_stopped:
            if dc_diff != 0:
                self.flower.start(self.flower_dc)
        else:
            if dc_diff != 0:
                self.flower.change_duty_cycle(self.flower_dc)
            else:
                if not self.human_present:
                    self.flower.stop()
                    self.flower_stopped = True

    def init_baby(self):
        cfg = self.cfg['baby']
        self.BABY_UARTDEV = cfg['uartdev']
        self.BABY_BLINK_PAUSE_MIN = cfg['blink_pause_min']
        self.BABY_BLINK_PAUSE_MAX = cfg['blink_pause_max']
        self.BABY_X_DELTA = cfg['x_delta']

        self.baby = serial.Serial(self.BABY_UARTDEV, 9600, timeout=1)
        self.baby_x = 120
        self.baby_blink = False
        self.baby_next_blink_dt = datetime.now()

        print("Baby initialized")

    def process_baby(self):
        if self.human_present:
            x_new = utils.linear_map(
                self.angle,
                self.radar.ANGLE_MIN,
                self.radar.ANGLE_MAX,
                80, 150)
            x_new = int(x_new)

            x_diff = utils.clamp(x_new - self.baby_x,
                                 -self.BABY_X_DELTA,
                                 self.BABY_X_DELTA)

            if math.fabs(x_diff) > 1:
                self.baby_x += x_diff

                cmd = f"{self.baby_x}\n".encode()
                self.baby.write(cmd)

            if self.dt > self.baby_next_blink_dt:
                self.baby_blink = True
            else:
                self.baby_blink = False

            if self.baby_blink:
                self.baby.write(b"blink\n")

                blink_delta = timedelta(seconds=random.randint(self.BABY_BLINK_PAUSE_MIN,
                                                               self.BABY_BLINK_PAUSE_MAX))
                self.baby_next_blink_dt = self.dt + blink_delta

    def init_horse(self):
        cfg = self.cfg['horse']
        self.HORSE_UARTDEV = cfg['uartdev']

        self.horse = serial.Serial(self.HORSE_UARTDEV, 9600, timeout=1)
        self.horse_next_time_check_dt = datetime.now()

        print("Horse initialized")

    def process_horse(self):
        if self.dt < self.horse_next_time_check_dt:
            return

        self.horse_next_time_check_dt = self.dt + timedelta(seconds=1)

        if self.human_present:
            self.horse.write(b"move\n")

    def init_hand(self):
        cfg = self.cfg['hand']
        self.HAND_INVERTED = cfg['inverted']

        self.hand = Hand(inverted=self.HAND_INVERTED)
        self.hand_stop_dt = self.dt + timedelta(seconds=1)

        self.hand_audio_marks = None
        self.hand_audio_current_mark_dt = None
        self.hand_audio_current_mark_position = None
        self.hand_audio_next_mark_dt = None
        self.hand_audio_next_mark_position = None

        print("Hand initialized")

    def process_hand(self):
        if (self.hand_stop_dt is not None) and (self.dt > self.hand_stop_dt):
            self.hand.stop()
            self.hand_stop_dt = None

        if (self.audio_state in [0,2,3]) and \
           (self.audio_state_prev == 1):
            self.hand.set_position_by_name("close")
            self.hand_stop_dt = self.dt + timedelta(seconds=1)

            self.hand_audio_marks = None
            self.hand_audio_current_mark_dt = None
            self.hand_audio_current_mark_position = None
            self.hand_audio_next_mark_dt = None
            self.hand_audio_next_mark_position = None

        elif self.audio_state == 1: # playing
            if self.hand_audio_marks is None:
                try:
                    self.hand_audio_marks = audio.load_marks(self.audio_file)
                except:
                    return

                if len(self.hand_audio_marks) > 0:
                    mark = self.hand_audio_marks.pop(0)
                    self.hand_audio_next_mark_dt = \
                        self.audio_start_dt + timedelta(seconds=mark[0])
                    self.hand_audio_next_mark_position = mark[1]

            if self.hand_audio_next_mark_dt is None:
                return

            if self.dt > self.hand_audio_next_mark_dt:
                self.hand_audio_current_mark_dt = self.hand_audio_next_mark_dt
                self.hand_audio_current_mark_position = self.hand_audio_next_mark_position

                self.hand.set_position_by_name(self.hand_audio_current_mark_position)
                self.hand_stop_dt = self.dt + timedelta(seconds=1)

                if len(self.hand_audio_marks) == 0:
                    self.hand_audio_next_mark_dt = None
                    self.hand_audio_next_mark_position = None
                else:
                    mark = self.hand_audio_marks.pop(0)
                    self.hand_audio_next_mark_dt = \
                        self.audio_start_dt + timedelta(seconds=mark[0])
                    self.hand_audio_next_mark_position = mark[1]

    def process(self):
        text = f"{self.dt}"

        if self.flag_radar:
            f = self.process_radar()
            if not f:
                return

            text =  f" | IN: {self.radar.in_waiting:5}"
            if self.human_present:
                text += f" | Human: yes"
                text += f" | Distance: {self.radar_distance:7.2f}"
                text += f" | Distance reliable: {self.radar_distance_reliable:7.2f}"
                text += f" | Angle: {self.radar_angle:7.2f}"
            else:
                text += f" | Human: no "
                text +=  " | Distance:   ---  "
                text +=  " | Distance reliable:   ---  "
                text +=  " | Angle:   ---  "

        if self.flag_video_brightness:
            self.process_brightness()

            text += f" | Brightness: {self.brightness:7}"

        if self.flag_video_overlay:
            self.process_overlay()

            text += f" | Overlay X: {self.overlay_x:5}"
            if self.overlay_blink:
                text += f" | Overlay blink: yes"
            else:
                text += f" | Overlay blink: no "

        if self.flag_audio:
            self.process_audio()

            text += f" | Audio state: {self.audio_state:3}"

        if self.flag_flower:
            self.process_flower()

            text += f" | Flower: {self.flower_dc:7.2f}"

        if self.flag_baby:
            self.process_baby()

            text += f" | Baby X: {self.baby_x:7}"
            if self.baby_blink:
                text += f" | Baby blink: yes"
            else:
                text += f" | Baby blink: no "

        if self.flag_horse:
            self.process_horse()

            if self.human_present:
                text += f" | Horse moving: yes"
            else:
                text += f" | Horse moving: no "

        if self.flag_hand:
            self.process_hand()

            if self.hand_audio_current_mark_position is None:
                text += f" | Hand position:     ---    "
            else:
                text += f" | Hand position: {self.hand_audio_current_mark_position:<10} "

        print(text)

    def start(self):
        while True:
            self.dt = datetime.now()
            self.process()


if __name__ == "__main__":
    import sys

    try:
        base_dpath = sys.argv[1]
    except:
        print("No argument for base directory path provided")
        sys.exit(1)

    ctl = Controller(base_dpath)
    ctl.start()
