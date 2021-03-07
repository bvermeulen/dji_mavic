''' module for remote control for dji mavic pro
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
rmax = 120
# adjust x, y limits to match the one on the polar plot
xymax = rmax * (1 - 2*rect_carth_offs) / (1 - 2*rect_carth_offs - 2*rect_polar_offs)

stick_end_color = 'red'
stick_end_size = 6
stick_color = 'blue'
stick_width = 3
bar_color = 'orange'
bar_width = 5
title_left = 'climb/ yaw'
title_right = 'pitch/ roll'


def conv_xy_to_polar(x, y):
    return np.degrees(np.arctan2(y, x)), np.sqrt(x*x + y*y)


class RemoteControlDisplay:
    ''' display of remote control with left and right sticks
        methods:
            __init__: requires as arg a flightdata dataframe from UAV Drone
            setup_rc: setup left and right remote controls on console
            draw: initial draw of console
            update_stick: update remote control sticks display
            update_bar: update x, y bars of remote controls display
            update: update values for climb, yaw, pitch and roll from fligtdata
            blit: blit the remote control sticks and bars
            on_resize: redraw console on resize
    '''

    def __init__(self, flightdata_df):
        # get axes from fligh data dataframe
        self.rc_climb = np.array(flightdata_df['rc_throttle'].to_list(), dtype=np.float64)
        self.rc_yaw = np.array(flightdata_df['rc_rudder'].to_list(), dtype=np.float64)
        # normalize axises * 100
        self.rc_climb -= rc_zero
        self.rc_climb /= 0.01 * (rc_max - rc_zero)
        self.rc_yaw -= rc_zero
        self.rc_yaw /= 0.01 * (rc_max - rc_zero)

        self.rc_pitch = np.array(flightdata_df['rc_elevator'].to_list(), dtype=np.float64)
        self.rc_roll = np.array(flightdata_df['rc_aileron'].to_list(), dtype=np.float64)
        # normalize axises * 100
        self.rc_pitch -= rc_zero
        self.rc_pitch /= 0.01 * (rc_max - rc_zero)
        self.rc_roll -= rc_zero
        self.rc_roll /= 0.01 * (rc_max - rc_zero)

        mpl.rcParams['toolbar'] = 'None'
        self.fig = plt.figure('Remote Control', figsize=fig_size)
        self.fig.suptitle(None)
        self.background = None

        self.ax_carth = {}
        self.ax_polar = {}
        self.stick = {}
        self.stick_end = {}
        self.bar_x = {}
        self.bar_y = {}
        self.setup_rc(title_left, 'left')
        self.setup_rc(title_right, 'right')

        connect = self.fig.canvas.mpl_connect
        connect('resize_event', self.on_resize)

    def setup_rc(self, stick_name: str, rc_key: str):
        if rc_key == 'left':
            rect_carth = [
                rect_carth_offs, rect_carth_offs,
                0.5-rect_carth_offs, 1 - 2*rect_carth_offs
            ]
            rect_polar = [
                rect_carth[0] + 0.5*rect_polar_offs, rect_carth[1] + rect_polar_offs,
                rect_carth[2] - 1*rect_polar_offs, rect_carth[3] - 2*rect_polar_offs
            ]

        elif rc_key == 'right':
            rect_carth = [
                0.25+2*rect_carth_offs, rect_carth_offs,
                1-4*rect_carth_offs, 1 - 2*rect_carth_offs
            ]
            rect_polar = [
                rect_carth[0] + rect_polar_offs, rect_carth[1] + rect_polar_offs,
                rect_carth[2] - 2*rect_polar_offs, rect_carth[3] - 2*rect_polar_offs
            ]

        # place carthesian grid in fig
        self.ax_carth[rc_key] = self.fig.add_axes(rect_carth)

        self.ax_carth[rc_key].set(
            xlim=(-xymax, xymax), ylim=(-xymax, xymax), aspect='equal'
        )

        # axis ticks
        ticks = np.arange(0, xymax, tick_intval)
        ticks = sorted(np.append(-ticks[1:], ticks))
        if rc_key == 'left':
            self.ax_carth[rc_key].set_yticks(ticks)

        elif rc_key == 'right':
            self.ax_carth[rc_key].set_yticks([])

        self.ax_carth[rc_key].set_xticks(ticks)

        # place polar grid in carthesian grid
        self.ax_polar[rc_key] = self.fig.add_axes(
            rect_polar, polar=True, frameon=False)
        self.ax_polar[rc_key].set_rmax(rmax)

        # display of stick
        self.stick_end[rc_key] = mpl_patches.Circle(
            (0, 0), radius=stick_end_size, fc=stick_end_color,
            transform=self.ax_polar[rc_key].transData._b, zorder=10, animated=True,  #pylint: disable=protected-access
        )
        self.stick[rc_key] = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=stick_width, color=stick_color, animated=True,
        )
        self.ax_polar[rc_key].add_patch(self.stick_end[rc_key])
        self.ax_polar[rc_key].add_line(self.stick[rc_key])
        self.update_stick(0, 0, rc_key)

        # display of x, y bars
        self.bar_x[rc_key] = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=bar_width, color=bar_color, solid_capstyle='butt',
            animated=True,
        )
        self.bar_y[rc_key] = mpl_lines.Line2D(
            [0, 0], [0, 0], linewidth=bar_width, color=bar_color, solid_capstyle='butt',
            animated=True,
        )
        self.ax_carth[rc_key].add_line(self.bar_x[rc_key])
        self.ax_carth[rc_key].add_line(self.bar_y[rc_key])
        self.update_bar(0, 0, rc_key)

        self.ax_carth[rc_key].set_title(stick_name)
        self.ax_polar[rc_key].set_yticklabels([])

    def draw(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def update_stick(self, x, y, rc_key):
        theta, r = conv_xy_to_polar(x, y)
        self.stick_end[rc_key].center = (x, y)
        self.stick[rc_key].set_data([0, np.radians(theta)], [0, r])

    def update_bar(self, x, y, rc_key):
        # from (0, -xymax) to (x, -xymax)
        self.bar_x[rc_key].set_data([0, x], [-xymax, -xymax])
        # from (xymax, 0) to (xymax, y)
        self.bar_y[rc_key].set_data([-xymax, -xymax], [0, y])

    def update(self, index):
        val1 = self.rc_yaw[index]
        val2 = self.rc_climb[index]
        self.update_stick(val1, val2, 'left')
        self.update_bar(val1, val2, 'left')

        val1 = self.rc_roll[index]
        val2 = self.rc_pitch[index]
        self.update_stick(val1, val2, 'right')
        self.update_bar(val1, val2, 'right')

    def blit(self):
        if self.background is None:
            self.background = (
                self.fig.canvas.copy_from_bbox(self.fig.bbox)
            )
            self.draw()

        else:
            self.fig.canvas.restore_region(self.background)
            self.fig.draw_artist(self.stick['left'])
            self.fig.draw_artist(self.stick_end['left'])
            self.fig.draw_artist(self.bar_x['left'])
            self.fig.draw_artist(self.bar_y['left'])
            self.fig.draw_artist(self.stick['right'])
            self.fig.draw_artist(self.stick_end['right'])
            self.fig.draw_artist(self.bar_x['right'])
            self.fig.draw_artist(self.bar_y['right'])
            self.fig.canvas.blit()
            self.fig.canvas.flush_events()

    def on_resize(self, event):
        self.background = None

    def remove_fig(self):
        plt.close(self.fig)

    def __repr__(self):
        return f'Remote Control: left: {title_left}, right: {title_right}'

if __name__ == '__main__':
    samplerate = 1
    flightdata_df = read_flightdata_csv('dji_mavic_test_data.csv')
    rcd = RemoteControlDisplay(flightdata_df)
    plt.show(block=False)
    plt.pause(0.1)
    print(rcd)
    input('continue to start ...')

    for i in range(0, len(flightdata_df), samplerate):
        rcd.update(i)
        rcd.blit()

    input('enter to finish ...')
