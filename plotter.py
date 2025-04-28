import threading

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation

from controller import Controller


class ControllerThread(threading.Thread):
    def __init__(self, uartdev, ws, dmin, dmax, verbose):
        super().__init__()
        self.daemon = True

        self._ctl = Controller(uartdev, ws, dmin, dmax, verbose)

    def run(self):
        self._ctl.start()

class Plotter():
    def __init__(self, uartdev, ws, dmin, dmax, verbose,
                 xmin, xmax, ymin, ymax=0,
                 point_size=1000, fontsize=20):

        self._ctl_thr = ControllerThread(uartdev, ws, dmin, dmax, verbose)
        self._ctl = self._ctl_thr._ctl

        self._xmin = xmin
        self._xmax = xmax
        self._ymin = ymin
        self._ymax = ymax
        self._point_size = point_size
        self._fontsize = fontsize

    def start(self):
        self._ctl_thr.start()
        self._show_plot()

    def _show_plot(self):
        fig, ax = plt.subplots(figsize=(15,8))
        ax.grid(True)
        ax.set_xlim(self._xmin, self._xmax)
        ax.set_ylim(self._ymin, self._ymax)
        ax.set_xlabel('x, mm')
        ax.set_ylabel('y, mm')
        
        self._screen = patches.Rectangle(
            (self._xmin, self._ymin), self._xmax-self._xmin,
            self._ymax-self._ymin, linewidth=0)
        ax.add_patch(self._screen)
        
        self._sc = ax.scatter([], [], s=self._point_size)
        
        self._d1t = ax.text(self._xmax-1000, self._ymin+750, '', fontsize=self._fontsize)
        self._d2t = ax.text(self._xmax-1000, self._ymin+500, '', fontsize=self._fontsize)
        self._d3t = ax.text(self._xmax-1000, self._ymin+250, '', fontsize=self._fontsize)
        self._brt = ax.text(self._xmin+250,  self._ymin+500, '', fontsize=self._fontsize*2)
        
        animation = FuncAnimation(fig=fig, func=self._update_plot, cache_frame_data=False, blit=True)

        mng = plt.get_current_fig_manager()
        mng.full_screen_toggle()

        plt.show()

    def _update_plot(self, frame):
        ctl = self._ctl

        if ctl.rdc.active:
            d1_text = f'1: {ctl.d1} mm'
            d2_text = f'2: {ctl.d2} mm'
            d3_text = f'3: {ctl.d3} mm'
            br_text = f'{int(ctl.b*100)}%'
        else:
            d1_text = '1: -- mm'
            d2_text = '2: -- mm'
            d3_text = '3: -- mm'
            br_text = 'No radar'

        c = (1, 0, 0, ctl.b)
        self._screen.set_facecolor(c)

        self._sc.set_offsets([
            [ctl.x1,-ctl.y1],
            [ctl.x2,-ctl.y2],
            [ctl.x3,-ctl.y3]])
        
        self._d1t.set_text(d1_text)
        self._d2t.set_text(d2_text)
        self._d3t.set_text(d3_text)
        self._brt.set_text(br_text)

        return (self._screen, self._sc, self._d1t, self._d2t, self._d3t, self._brt)

if __name__ == "__main__":
    import sys

    try:
        uartdev = sys.argv[1]
    except:
        print("No argument for UART device provided")
        sys.exit(1)

    try:
        ws = sys.argv[2]
    except:
        print("No argument for window size provided")
        sys.exit(1)

    try:
        ws = int(ws)
        if ws <= 0:
            raise Exception
    except:
        print("Window size must be integer greater than 0")
        sys.exit(1)

    try:
        dmin = sys.argv[3]
    except:
        print("No argument for minimum distance provided")
        sys.exit(1)

    try:
        dmin = int(dmin)
        if dmin <= 0:
            raise Exception
    except:
        print("Minimum distance must be integer greater than 0")
        sys.exit(1)

    try:
        dmax = sys.argv[4]
    except:
        print("No argument for maximum distance provided")
        sys.exit(1)

    try:
        dmax = int(dmax)
        if dmax <= dmin:
            raise Exception
    except:
        print("Maximum distance must be integer greater than minimum distance")
        sys.exit(1)

    try:
        xmin = sys.argv[5]
    except:
        xmin = -3000

    try:
        xmin = int(xmin)
    except:
        print("Minimum X must be integer")
        sys.exit(1)

    try:
        xmax = sys.argv[6]
    except:
        xmax = 3000

    try:
        xmax = int(xmax)
        if xmax <= xmin:
            raise Exception
    except:
        print("Maximum X must be integer greater than minimum X")
        sys.exit(1)

    try:
        ymin = sys.argv[7]
    except:
        ymin = -4000

    try:
        ymin = int(ymin)
        if ymin >= 0:
            raise Exception
    except:
        print("Minimum Y must be integer less than 0")
        sys.exit(1)

    p = Plotter(uartdev, ws, dmin, dmax, verbose=True, xmin=xmin, xmax=xmax, ymin=ymin)
    p.start()
