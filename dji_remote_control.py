''' module remote control for DJI Mavic Pro
'''
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patches as mpl_patches
from matplotlib import lines as mpl_lines
from dji_mavic_io import read_flightdata_csv

rc_filename = 'dji_mavic_test_data_2.csv'
rc_max = 1684
rc_min = 364
rc_zero = 1024

fig_size = (16.8/2.54, 8.4/2.54)
rect_carth_offs = 0.09
rect_polar_offs = 0.120
tick_intval = 50

stick_end_color = 'red'
stick_end_size = 6
stick_color = 'blue'
stick_width = 3
bar_color = 'orange'
bar_width = 5


def conv_xy_to_polar(x, y):
    return np.degrees(np.arctan2(y, x)), np.sqrt(x*x + y*y)


class RemoteControlDisplay:

    @classmethod
    def setup(cls, rmax):
        cls.rmax = rmax
        mpl.rcParams['toolbar'] = 'None'
        cls.fig = plt.figure('Remote Control', figsize=fig_size)
        cls.fig.suptitle(None)
        cls.background = None

    @classmethod
    def draw(cls):
        cls.fig.canvas.draw()
        cls.fig.canvas.flush_events()


class RcStick(RemoteControlDisplay):

    def __init__(self, stick_name, left=True):

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
        self.ax_carth = self.fig.add_axes(rect_carth)

        # adjust x, y limits to match the one on the polar plot
        self.bv = (
            self.rmax * (1-2*rect_carth_offs) / (1-2*rect_carth_offs-2*rect_polar_offs)
        )
        self.ax_carth.set(
            xlim=(-self.bv, self.bv), ylim=(-self.bv, self.bv), aspect='equal'
        )

        # axis ticks
        ticks = np.arange(0, self.bv, tick_intval)
        ticks = sorted(np.append(-ticks[1:], ticks))
        if left:
            self.ax_carth.set_yticks(ticks)

        else:
            self.ax_carth.set_yticks([])
        self.ax_carth.set_xticks(ticks)

        # place polar grid in carthesian grid
        self.ax_polar = self.fig.add_axes(rect_polar, polar=True, frameon=False)
        self.ax_polar.set_rmax(self.rmax)

        # display of stick
        self.stick_end = mpl_patches.Circle(
            (0, 0), radius=stick_end_size, fc=stick_end_color,
            transform=self.ax_polar.transData._b, zorder=10, animated=True,
        )
        self.stick = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=stick_width, color=stick_color, animated=True,
        )
        self.ax_polar.add_patch(self.stick_end)
        self.ax_polar.add_line(self.stick)
        self.stick_val(0, 0)

        # display of x, y bars
        self.bar_x = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=bar_width, color=bar_color, solid_capstyle='butt',
            animated=True,
        )
        self.bar_y = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=bar_width, color=bar_color, solid_capstyle='butt',
            animated=True,
        )
        self.ax_carth.add_line(self.bar_x)
        self.ax_carth.add_line(self.bar_y)
        self.bar_val(0, 0)

        self.ax_carth.set_title(stick_name)
        self.ax_polar.set_yticklabels([])

        self.background = None

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

    def blit_rc(self):
        if self.background is None:
            self.background = (
                self.fig.canvas.copy_from_bbox(self.fig.bbox)
            )
            self.draw()

        else:
            self.fig.canvas.restore_region(self.background)
            self.fig.draw_artist(self.stick)
            self.fig.draw_artist(self.stick_end)
            self.fig.draw_artist(self.bar_x)
            self.fig.draw_artist(self.bar_y)
            self.fig.canvas.blit()
            self.fig.canvas.flush_events()


if __name__ == '__main__':
    flightdata_df = read_flightdata_csv(rc_filename)
    rc_climb = np.array(flightdata_df['rc_throttle'].to_list(), dtype=np.float64)
    rc_yaw = np.array(flightdata_df['rc_rudder'].to_list(), dtype=np.float64)
    # normalize axises * 100
    rc_climb -= rc_zero
    rc_climb /= 0.01 * (rc_max - rc_zero)
    rc_yaw -= rc_zero
    rc_yaw /= 0.01 * (rc_max - rc_zero)

    rc_pitch = np.array(flightdata_df['rc_elevator'].to_list(), dtype=np.float64)
    rc_roll = np.array(flightdata_df['rc_aileron'].to_list(), dtype=np.float64)
    # normalize axises * 100
    rc_pitch -= rc_zero
    rc_pitch /= 0.01 * (rc_max - rc_zero)
    rc_roll -= rc_zero
    rc_roll /= 0.01 * (rc_max - rc_zero)


    rcd = RemoteControlDisplay()
    rcd.setup(120)
    rc_right = RcStick('pitch/ roll', left=False)
    rc_left = RcStick('climb/ yaw', left=True)
    plt.show(block=False)
    input('continue to start ...')

    # combine blit for left and right
    def blit():
        if rcd.background is None:
            rcd.background = (
                rcd.fig.canvas.copy_from_bbox(rcd.fig.bbox)
            )
            rcd.draw()

        else:
            rcd.fig.canvas.restore_region(rcd.background)
            rcd.fig.draw_artist(rc_left.stick)
            rcd.fig.draw_artist(rc_left.stick_end)
            rcd.fig.draw_artist(rc_left.bar_x)
            rcd.fig.draw_artist(rc_left.bar_y)
            rcd.fig.draw_artist(rc_right.stick)
            rcd.fig.draw_artist(rc_right.stick_end)
            rcd.fig.draw_artist(rc_right.bar_x)
            rcd.fig.draw_artist(rc_right.bar_y)
            rcd.fig.canvas.blit()
            rcd.fig.canvas.flush_events()

    for i in range(len(rc_pitch[::1])):
        rc_left.rc_vals(rc_roll[i], rc_pitch[i])
        rc_right.rc_vals(rc_yaw[i], rc_climb[i])
        blit()

    input('enter to finish ...')