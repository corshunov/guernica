import threading
import time
import queue

from radar import LD2450


class RadarDataCollector(threading.Thread):
    def __init__(self, uartdev, default_bluetooth=True, default_multi_tracking=True):
        super().__init__()
        self.daemon = True

        self.uartdev = uartdev
        self.default_bluetooth = default_bluetooth
        self.default_multi_tracking = default_multi_tracking

        self.queue = queue.Queue()

        self.radar = None

    def _init_radar(self):
        r = LD2450(self.uartdev)

        if default_bluetooth:
            r.set_bluetooth_on(restart=True)
        else:
            r.set_bluetooth_off(restart=True)

        if default_multi_tracking:
            r.set_multi_tracking()
        else:
            r.set_single_tracking()
        
        r.set_zone_filtering(mode=0)

        self.radar = r
        print("Radar UP.")

    @property
    def active(self):
        return self.radar is not None

    def qsize(self):
        return self.queue.qsize()

    def empty(self):
        return self.queue.empty()

    def get(self):
        return self.queue.get(timeout=0.01)

    def run(self):
        while True:
            try:
                self._init_radar()

                i = 0
                while True:
                    data = self.radar.get_frame()
                    if data is None:
                        continue

                    if i < 50:
                        i += 1
                        continue 

                    self.queue.put(data)
            except:
                if self.active:
                   self.radar = None
                   print("Radar DOWN.")

                time.sleep(1)

if __name__ == "__main__":
    import sys

    try:
        uartdev = sys.argv[1]
    except:
        raise Exception("No argument for UART device provided")

    rdc = RadarDataCollector(uartdev)
    rdc.start()

    while not rdc.active:
        print('Waiting for radar to init...')
        time.sleep(1)

    while True:
        if not rdc.empty():
            s = rdc.get()
            print(f"Queue: {rdc.qsize():5}, IN waiting: {rdc.radar.in_waiting:5}: {s}")
