import time

from radar_data_collector import RadarDataCollector
from sliding_average import SlidingAverage


class Controller():
    @staticmethod
    def _dist(x, y):
        return round((x**2 + y**2)**0.5, 2)

    def __init__(self, uartdev, ws, dmin, dmax, verbose=True):
        if dmin > dmax:
            raise Exception("Argument 'dmin' must be no greater than 'dmax'")

        self.rdc = RadarDataCollector(uartdev)

        self._ndec = 2

        self._x1avg = SlidingAverage(ws, self._ndec)
        self._y1avg = SlidingAverage(ws, self._ndec)

        self._x2avg = SlidingAverage(ws, self._ndec)
        self._y2avg = SlidingAverage(ws, self._ndec)

        self._x3avg = SlidingAverage(ws, self._ndec)
        self._y3avg = SlidingAverage(ws, self._ndec)

        self._dmin = dmin
        self._dmax = dmax
        self._drange = self._dmax - self._dmin
        self._dout = self._dmax * 1.2

        self.verbose = verbose

        self.set_no_targets()

    def set_no_targets(self):
        self.x1 = 0.
        self.y1 = 0.
        self.d1 = self._dout

        self.x2 = 0.
        self.y2 = 0.
        self.d2 = self._dout

        self.x3 = 0.
        self.y3 = 0.
        self.d3 = self._dout

    def update_targets(self):
        x1,y1,x2,y2,x3,y3 = self.rdc.get()

        if (x1 == 0) and (y1 == 0):
            self.x1 = 0.
            self.y1 = 0.
            self.d1 = self._dout
        else:
            self.x1 = self._x1avg.add(x1)
            self.y1 = self._y1avg.add(y1)
            self.d1 = self._dist(self.x1, self.y1)
 
        if (x2 == 0) and (y2 == 0):
            self.x2 = 0.
            self.y2 = 0.
            self.d2 = self._dout
        else:
            self.x2 = self._x2avg.add(x2)
            self.y2 = self._y2avg.add(y2)
            self.d2 = self._dist(self.x2, self.y2)

        if (x3 == 0) and (y3 == 0):
            self.x3 = 0.
            self.y3 = 0.
            self.d3 = self._dout
        else:
            self.x3 = self._x3avg.add(x3)
            self.y3 = self._y3avg.add(y3)
            self.d3 = self._dist(self.x3, self.y3)

    def update_brightness(self):
        self.d = min([self.d1, self.d2, self.d3])
        
        if self.d >= self._dmax:
            self.b = 0.
        elif self.d <= self._dmin:
            self.b = 1.
        else:
            self.b = round(1 - ((self.d-self._dmin) / self._drange), self._ndec)
 
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

            if self.verbose:
                print(f"Q: {self.rdc.qsize(): 5} | IN: {in_waiting} | B: {self.b:7.2f} | D: {self.d:7.2f} | "
                      f"{self.x1:7.1f} {self.y1:7.1f} | "
                      f"{self.x2:7.1f} {self.y2:7.1f} | "
                      f"{self.x3:7.1f} {self.y3:7.1f}")

if __name__ == "__main__":
    import sys

    try:
        uartdev = sys.argv[1]
    except:
        raise Exception("No argument for UART device provided")

    try:
        ws = sys.argv[2]
    except:
        raise Exception("No argument for window size provided")

    try:
        dmin = sys.argv[3]
    except:
        raise Exception("No argument for minimum distance provided")

    try:
        dmax = sys.argv[4]
    except:
        raise Exception("No argument for maximum distance provided")

    ctl = Controller(uartdev, ws, dmin, dmax)
    ctl.start()
