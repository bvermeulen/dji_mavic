''' module remote control for DJI Mavic Pro
'''
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patches as mpl_patches
from matplotlib import lines as mpl_lines

fig_size = (13, 6)
stick_end_color = 'red'
stick_end_size = 5
stick_color = 'blue'
stick_width = 5
bar_color = 'orange'
bar_width = 10
plt.ion()

def conv_xy_to_polar(x, y):
    return np.degrees(np.arctan2(y, x)), np.sqrt(x*x + y*y)


class RemoteControlDisplay:

    @classmethod
    def setup(cls, rmax):
        cls.rmax = rmax
        mpl.rcParams['toolbar'] = 'None'
        cls.fig = plt.figure('Remote Control', figsize=fig_size)
        cls.fig.suptitle(None)
        connect = cls.fig.canvas.mpl_connect
        connect('key_press_event', cls.on_key)
        cls.pause = False

    @classmethod
    def on_key(cls, event):
        if event.key == ' ':
            cls.pause = not cls.pause
            if cls.pause:
                print('pause ...')

    @classmethod
    def blit(cls):
        cls.fig.canvas.draw()
        cls.fig.canvas.flush_events()


class RcStick(RemoteControlDisplay):

    def __init__(self, stick_name, left=True):
        rect_carth_offs = 0.050
        rect_polar_offs = 0.075
        tick_intval = 20

        if left:
            rect_carth = [
                rect_carth_offs, rect_carth_offs,
                0.5-rect_carth_offs, 1 - 2*rect_carth_offs
            ]
            rect_polar = [
                rect_carth[0] + 0.5*rect_polar_offs, rect_carth[1] + rect_polar_offs,
                rect_carth[2] - 1*rect_polar_offs, rect_carth[3] - 2*rect_polar_offs
            ]

        else:
            rect_carth = [
                0.25+2*rect_carth_offs, rect_carth_offs,
                1-4*rect_carth_offs, 1 - 2*rect_carth_offs
            ]
            rect_polar = [
                rect_carth[0] + rect_polar_offs, rect_carth[1] + rect_polar_offs,
                rect_carth[2] - 2*rect_polar_offs, rect_carth[3] - 2*rect_polar_offs
            ]

        # place carthesian grid in fig
        ax_carth = self.fig.add_axes(rect_carth)

        # adjust x, y limits to match the one on the polar plot
        self.bv = (
            self.rmax * (1-2*rect_carth_offs) / (1-2*rect_carth_offs-2*rect_polar_offs)
        )
        ax_carth.set(xlim=(-self.bv, self.bv), ylim=(-self.bv, self.bv), aspect='equal')

        # axis ticks
        ticks = np.arange(0, self.bv, tick_intval)
        ticks = sorted(np.append(-ticks[1:], ticks))
        if left or True:
            ax_carth.set_yticks(ticks)

        else:
            ax_carth.set_yticks([])
        ax_carth.set_xticks(ticks)

        # place polar grid in carthesian grid
        ax_polar = self.fig.add_axes(rect_polar, polar=True, frameon=False)
        ax_polar.set_rmax(self.rmax)

        # display of stick
        self.stick_end = mpl_patches.Circle(
            (0, 0), radius=stick_end_size, fc=stick_end_color,
            transform=ax_polar.transData._b
        )
        self.stick = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=stick_width, color=stick_color
        )
        ax_polar.add_patch(self.stick_end)
        ax_polar.add_line(self.stick)
        self.stick_val(0, 0)

        # display of x, y bars
        self.bar_x = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=bar_width, color=bar_color, solid_capstyle='butt',
        )
        self.bar_y = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=bar_width, color=bar_color, solid_capstyle='butt',
        )
        ax_carth.add_line(self.bar_x)
        ax_carth.add_line(self.bar_y)
        self.bar_val(0, 0)

        ax_carth.set_title(stick_name)
        ax_polar.set_yticklabels([])

    def stick_val(self, x, y):
        theta, r = conv_xy_to_polar(x, y)
        self.stick_end.center = (x, y)
        self.stick.set_data([0, np.radians(theta)], [0, r])

    def bar_val(self, x, y):
        # from (0, -bv) to (x, -bv)
        self.bar_x.set_data([0, x], [-self.bv, -self.bv])
        # from (bv, 0) to (bv, y)
        self.bar_y.set_data([-self.bv, -self.bv], [0, y])

    def rc_vals(self, val1, val2):
        self.stick_val(val1, val2)
        self.bar_val(val1, val2)
