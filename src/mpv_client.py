import json
from pathlib import Path
import socket
import time


class MPVClient():
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
        self.socket.settimeout(1)
        self.socket.connect(str(self.socket_path))

        self._request_id = 0

    def __del__(self):
        try:
            self.socket.close()
        except:
            pass

    def _next_request_id(self):
        self._request_id = (self._request_id % 999) + 1
        return self._request_id

    def _send_json(self, cmd):
        request_id = self._next_request_id()

        cmd_j = {"command" : cmd, "request_id": request_id}
        cmd_b = self._j2b(cmd_j)
        #print(cmd_b)

        self.socket.send(cmd_b)

        res_b = self.socket.recv(4096)
        #print(len(res_b))
        #print(res_b)
        for i_res_b in res_b.split(b'\n'):
            if not i_res_b:
                continue

            res_j = self._b2j(i_res_b)
            if "request_id" in res_j and res_j["request_id"] == request_id:
                return res_j

    def get_property(self, name):
        cmd = ["get_property", name]
        return self._send_json(cmd)

    def set_property(self, name, value):
        cmd = ["set_property", name, value]
        return self._send_json(cmd)

    def clear(self):
        cmd = ["stop"]
        return self._send_json(cmd)

    def load_file(self, path, replace=True):
        if replace:
            cmd = ["loadfile", str(path), "replace"]
        else:
            cmd = ["loadfile", str(path)]
        return self._send_json(cmd)

    def seek(self, pos, pause=True):
        cmd = ["seek", pos, "absolute"]
        return self._send_json(cmd)

    def show_text(self, text):
        cmd = ["show-text", text]
        return self._send_json(cmd)

    def play(self):
        return self.set_property("pause", False)

    def pause(self):
        return self.set_property("pause", True)

    def set_brightness(self, value, osd=False):
        v = max(-100, min(100, value))
        if osd:
            self.show_text(f"brightness: {v}")

        return self.set_property("brightness", v)

    def set_drm_brightness(self, value, osd=False):
        v = max(0, min(65535, value))
        if osd:
            self.show_text(f"drm-brightness: {v}")

        return self.set_property("drm-brightness", v)

    def set_x_overlay(self, overlay_name, x, osd=False):
        if osd:
            self.show_text(f"{overlay_name} X: {x: 4}")

        cmd = ["vf-command", "all", f"x@overlay@{overlay_name}", str(x)]
        return self._send_json(cmd)
