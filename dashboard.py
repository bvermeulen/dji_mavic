''' module dashboard for DJI Mavic Pro
'''
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patches as mpl_patches
from matplotlib import lines as mpl_lines
from rc_io import read_flightdata_csv

rc_filename = 'Oct-27th-2020-12-05PM-Flight-Airdata.csv'
fig_size = (13, 6)
stick_end_color = 'red'
stick_end_size = 5
stick_color = 'blue'
stick_width = 5
bar_color = 'orange'
bar_width = 10
initial_theta = 0
initial_r = 0
rc_max = 1684
rc_min = 364
rc_zero = 1024

def conv_xy_to_polar(x, y):
    return np.degrees(np.arctan2(y, x)), np.sqrt(x*x + y*y)


class RemoteControlDisplay:
    def __init__(self, rmax):
        self._rmax = rmax
        mpl.rcParams['toolbar'] = 'None'
        self.rc_fig = plt.figure('Remote Control', figsize=fig_size)
        self.rc_fig.suptitle(None)
        connect = self.rc_fig.canvas.mpl_connect
        connect('key_press_event', self.on_key)
        self._pause = False

    def on_key(self, event):
        if event.key == ' ':
            self._pause = not self._pause
            if self._pause:
                print('pause ...')

    def blit(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    @property
    def fig(self):
        return self.rc_fig

    @property
    def rmax(self):
        return  self._rmax

    @property
    def pause(self):
        return self._pause


class RcStick():

    def __init__(self, fig, rmax, stick_name, left=True):
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
        self.ax_carth = fig.add_axes(rect_carth)

        # adjust x, y limits to match the one on the polar plot
        self.cf = (1-2*rect_carth_offs) / (1-2*rect_carth_offs-2*rect_polar_offs)
        self.ax_carth.set(
            xlim=(-self.cf*rmax, self.cf*rmax),
            ylim=(-self.cf*rmax, self.cf*rmax),
            aspect='equal'
        )
        self.bv = rmax * self.cf
        # axis ticks
        ticks = np.arange(0, self.cf*rmax, tick_intval)
        ticks = sorted(np.append(-ticks[1:], ticks))
        if left or True:
            self.ax_carth.set_yticks(ticks)

        else:
            self.ax_carth.set_yticks([])
        self.ax_carth.set_xticks(ticks)

        # place polar grid in carthesian grid
        self.ax_polar = fig.add_axes(rect_polar, polar=True, frameon=False)
        self.ax_polar.set_rmax(rmax)

        # display of stick
        self.stick_end = mpl_patches.Circle(
            (0, 0), radius=stick_end_size, fc=stick_end_color,
            transform=self.ax_polar.transData._b
        )
        self.stick = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=stick_width, color=stick_color
        )
        self.ax_polar.add_patch(self.stick_end)
        self.ax_polar.add_line(self.stick)
        self.stick_val(initial_theta, initial_r)

        # display of x, y bars
        self.bar_x = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=bar_width, color=bar_color
        )
        self.bar_y = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=bar_width, color=bar_color
        )
        self.ax_carth.add_line(self.bar_x)
        self.ax_carth.add_line(self.bar_y)
        self.bar_val(initial_theta, initial_r)

        self.ax_carth.set_title(stick_name)
        self.ax_polar.set_yticklabels([])

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


if __name__ == '__main__':
    plt.ion()
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

    rc = RemoteControlDisplay(120)
    rc_left = RcStick(rc.fig, rc.rmax, 'climb/ yaw', left=True)
    rc_right = RcStick(rc.fig, rc.rmax, 'pitch/ roll', left=False)
    input('start')
    for i, (climb, yaw, pitch, roll)  in enumerate(
            zip(rc_climb, rc_yaw, rc_pitch, rc_roll)):

        while rc.pause:
            rc.blit()

        # blot diplay for every second of the flight (10 x 100 ms)
        # nominal there may be gaps if reception is poor
        if i % 10 == 0:
            rc_left.rc_vals(yaw, climb)
            rc_right.rc_vals(roll, pitch)
            rc.blit()

        if i % 10 == 0:
            print(
                f'time: {i:5}, climb: {climb:10.4f}, yaw: {yaw:10.4f}, '
                f'pitch: {pitch:10.4f}, roll: {roll:10.4f}'
            )

    input('finish')
