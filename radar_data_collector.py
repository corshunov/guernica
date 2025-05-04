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

        self.queue = queue.Queue(maxsize=1000)

        self.radar = self._get_radar()

        self._active = True

    def _get_radar(self):
        r = LD2450(self.uartdev)

        if self.default_bluetooth:
            r.set_bluetooth_on(restart=True)
        else:
            r.set_bluetooth_off(restart=True)

        if self.default_multi_tracking:
            r.set_multi_tracking()
        else:
            r.set_single_tracking()
        
        r.set_zone_filtering(mode=0)

        return r

    def _collect_data(self):
        self.radar.clean()

        #i = 0
        first_time = True
        while True:
            if not self._active:
                print("Radar DOWN.")
                break

            data = self.radar.get_frame()
            if first_time:
                print("Radar UP.")
                first_time = False
            
            if data is None:
                continue

            #if i < 50:
                #i += 1
                #continue 

            try:
                #self.queue.put_nowait(data)
                self.queue.put(data, timeout=0.01)
            except:
                print("Queue is full, skipping frame")

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, f):
        if isinstance(f, bool):
            self._active = f
        else:
            raise Exception("Invalid argument")

    @property
    def qsize(self):
        return self.queue.qsize()

    @property
    def empty(self):
        return self.queue.empty()

    def get(self):
        try:
            #return self.queue.get_nowait()
            return self.queue.get(timeout=0.01)
        except:
            return None

    def run(self):
        while True:
            if not self._active:
                time.sleep(1)
                continue

            try:
                self._collect_data()
            except:
                print("Problem with radar")

                try:
                    self.radar = self._get_radar()
                except:
                    time.sleep(1)

if __name__ == "__main__":
    import sys

    try:
        uartdev = sys.argv[1]
    except:
        print("No argument for UART device provided")
        sys.exit(1)

    rdc = RadarDataCollector(uartdev)
    rdc.start()

    try:
        while True:
            if not rdc.empty:
                s = rdc.get()
                print(f"Queue: {rdc.qsize:5}, IN waiting: {rdc.radar.in_waiting:5}: {s}")
    except KeyboardInterrupt:
        print("\nExiting...\n")
