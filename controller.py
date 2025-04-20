import time

from radar_data_collector import RadarDataCollector
from sliding_average import SlidingAverage


class Controller():
    @staticmethod
    def _dist(x, y):
        return round((x**2 + y**2)**0.5, 2)

    def __init__(self, uartdev, ws, dmin, dmax, log=True):
        self.rdc = RadarDataCollector(uartdev)

        self.x1avg = SlidingAverage(ws)
        self.y1avg = SlidingAverage(ws)

        self.x2avg = SlidingAverage(ws)
        self.y2avg = SlidingAverage(ws)

        self.x3avg = SlidingAverage(ws)
        self.y3avg = SlidingAverage(ws)

        self.dmin = dmin
        self.dmax = dmax

        self.log = log

        self.d_out = self.dmax * 1.2
        self.set_no_targets()

    def set_no_targets(self):
        self.x1 = 0.
        self.y1 = 0.
        self.d1 = self.d_out

        self.x2 = 0.
        self.y2 = 0.
        self.d2 = self.d_out

        self.x3 = 0.
        self.y3 = 0.
        self.d3 = self.d_out

    def update_targets(self):
        x1,y1,x2,y2,x3,y3 = self.rdc.get()

        if (x1 == 0) and (y1 == 0):
            self.x1 = 0.
            self.y1 = 0.
            self.d1 = self.d_out
        else:
            self.x1 = self.x1avg.add(x1)
            self.y1 = self.y1avg.add(y1)
            self.d1 = self._dist(self.x1, self.y1)
 
        if (x2 == 0) and (y2 == 0):
            self.x2 = 0.
            self.y2 = 0.
            self.d2 = self.d_out
        else:
            self.x2 = self.x2avg.add(x2)
            self.y2 = self.y2avg.add(y2)
            self.d2 = self._dist(self.x2, self.y2)

        if (x3 == 0) and (y3 == 0):
            self.x3 = 0.
            self.y3 = 0.
            self.d3 = self.d_out
        else:
            self.x3 = self.x3avg.add(x3)
            self.y3 = self.y3avg.add(y3)
            self.d3 = self._dist(self.x3, self.y3)

    def update_brightness(self):
        self.d = min([self.d1, self.d2, self.d3])
        
        if self.d >= self.dmax:
            self.b = 0.
        elif self.d <= self.dmin:
            self.b = 1.
        else:
            self.b = round(1 - ((self.d-self.dmin) / (self.dmax-self.dmin)), 2)
        
    def start(self):
        self.rdc.start()

        while True:
            in_waiting = "  -  "
            if self.rdc.empty():
                if self.rdc.active:
                   continue
                else:
                   self.set_no_targets()
            else:
                self.update_targets()
                in_waiting = f"{self.rdc.radar.in_waiting:5}"

            self.update_brightness()

            if self.log:
                print(f"Q: {self.rdc.qsize(): 5} | IN: {in_waiting} | B: {self.b:7.2f} | D: {self.d:7.2f} | "
                      f"{self.x1:7.1f} {self.y1:7.1f} | "
                      f"{self.x2:7.1f} {self.y2:7.1f} | "
                      f"{self.x3:7.1f} {self.y3:7.1f}")

if __name__ == "__main__":
    uartdev = "/dev/tty.usbserial-14410"
    ws = 15
    dmin = 1000
    dmax = 3000

    ctl = Controller(uartdev, ws, dmin, dmax)
    ctl.start()
