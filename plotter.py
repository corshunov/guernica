import threading

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation

from controller import Controller

class ControllerThread(threading.Thread):
    def __init__(self, uartdev, ws, dmin, dmax, log):
        super().__init__()
        self.daemon = True

        self.ctl = Controller(uartdev, ws, dmin, dmax, log)

    def run(self):
        self.ctl.start()

class Plotter():
    def __init__(self, uartdev, ws, dmin, dmax, log,
                 xmin, xmax, ymin, ymax=0,
                 point_size=1000, fontsize=20):

        self.ctl_thr = ControllerThread(uartdev, ws, dmin, dmax, log)
        self.ctl = self.ctl_thr.ctl

        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.point_size = point_size
        self.fontsize = fontsize

    def start(self):
        self.ctl_thr.start()
        self.show_plot()

    def show_plot(self):
        fig, ax = plt.subplots(figsize=(15,8))
        ax.grid(True)
        ax.set_xlim(self.xmin, self.xmax)
        ax.set_ylim(self.ymin, self.ymax)
        ax.set_xlabel('x, mm')
        ax.set_ylabel('y, mm')
        
        self.screen = patches.Rectangle(
            (self.xmin, self.ymin), self.xmax-self.xmin,
            self.ymax-self.ymin, linewidth=0)
        ax.add_patch(self.screen)
        
        self.sc = ax.scatter([], [], s=self.point_size)
        
        self.d1t = ax.text(self.xmax-1000, self.ymin+750, '', fontsize=self.fontsize)
        self.d2t = ax.text(self.xmax-1000, self.ymin+500, '', fontsize=self.fontsize)
        self.d3t = ax.text(self.xmax-1000, self.ymin+250, '', fontsize=self.fontsize)
        self.brt = ax.text(self.xmin+250, self.ymin+500, '', fontsize=self.fontsize*2)
        
        animation = FuncAnimation(fig=fig, func=self.update_plot, cache_frame_data=False, blit=True)

        mng = plt.get_current_fig_manager()
        mng.full_screen_toggle()

        plt.show()

    def update_plot(self, frame):
        ctl = self.ctl

        #print(ctl.rdc.active)

        if self.ctl.rdc.active:
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
        self.screen.set_facecolor(c)

        self.sc.set_offsets([
            [ctl.x1,-ctl.y1],
            [ctl.x2,-ctl.y2],
            [ctl.x3,-ctl.y3]])
        
        self.d1t.set_text(d1_text)
        self.d2t.set_text(d2_text)
        self.d3t.set_text(d3_text)
        self.brt.set_text(br_text)

        return (self.screen, self.sc, self.d1t, self.d2t, self.d3t, self.brt)

if __name__ == "__main__":
    uartdev = "/dev/tty.usbserial-14410"
    ws = 10
    dmin = 1000
    dmax = 4000
    log = True
    #log = False

    xmin = -3000
    xmax = 3000
    ymin = -4000

    p = Plotter(uartdev, ws, dmin, dmax, log, xmin, xmax, ymin)
    p.start()
