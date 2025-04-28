import json
from pathlib import Path
import socket
import time


class MPVController():
    DEFAULT_SOCKET_PATH = "/tmp/mpvsocket"

    @staticmethod
    def _j2b(j):
        t = json.dumps(j) + "\n"
        b = t.encode("utf-8")
        return b

    @staticmethod
    def _b2j(b):
        t = b.decode("utf-8")
        j = json.loads(t)
        return j

    def __init__(self, socket_path=None):
        if socket_path is None:
            self.socket_path = Path(self.DEFAULT_SOCKET_PATH)
        else:
            self.socket_path = Path(socket_path)

        if not self.socket_path.is_socket():
            raise Exception(f"Socket '{self.socket_path}' not found")

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(str(self.socket_path))

        self.set_brightness(0)
        self.pause()

    def _send(self, cmd_j):
        try:
            cmd_b = self._j2b(cmd_j)
            print(cmd_b)
            self.socket.send(cmd_b)

            res_b = self.socket.recv(4096)
            res_j = self._b2j(res_b)

            return res_j
        except Exception as e:
            print(f"Failed to send CMD: {e}")

    #def load_file(self, path, pause=True, start=0):
    #    #self._send({"command": ["loadfile", path, "replace",
    #                           #{"pause": pause, "start": str(start)}]})
    #    self._send({"command": ["loadfile", path, "replace"]})
    #    time.sleep(1)

    def play(self):
        self._send({"command": ["set_property", "pause", False]})
        self.playing = True

    def pause(self):
        self._send({"command": ["set_property", "pause", True]})
        self.playing = False

    #def seek(self, v, pause=True):
    #    self._send({"command": ["seek", v, "absolute"]})
    #    self.pause()
    #    print("Seek to {v}")

    def set_brightness(self, v):
        v = max(-100, min(100, v))
        self.brightness = v
        self._send(["vf", "set", f"eq=brightness={self.brightness}"])
        print(f"Brightness: {self.brightness:.2f}")

    #def change_brightness(self, to_v, steps=10, delay=0.5):
    #    step = (to_v - self.brightness) / steps
    #    for i in range(steps + 1):
    #        v = self.brightness + (i * step)
    #        self.set_brightness(v)
    #        time.sleep(delay)

    #def get_property(self, prop):
    #    res = self._send({"command": ["get_property", prop]})
    #    return res.get("data") if res else None

if __name__ == "__main__":
    d = 0.05

    ctl = MPVController()

    time.sleep(3)
    ctl.play()

    time.sleep(3)
    ctl.pause()

    time.sleep(3)
    ctl.play()

    for i in range(0, 100):
        ctl.set_brightness(i)
        time.sleep(d)

    for i in range(100, -100, -1):
        ctl.set_brightness(i)
        time.sleep(d)

    for i in range(-100, 0):
        ctl.set_brightness(i)
        time.sleep(d)

    ctl.pause()
