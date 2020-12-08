''' dashboard for DJI Mavic Pro
'''
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches as mpl_patches
from matplotlib import lines as mpl_lines

fig_size = (5, 8)
stick_end_color = 'red'
stick_end_size = 5
stick_color = 'blue'
stick_width = 5
bar_color = 'orange'
bar_width = 20
initial_theta = 0
initial_r = 0

def conv_polar_to_xy(theta, r):
    return r*np.cos(theta), r*np.sin(theta)


def conv_xy_to_polar(x, y):
    return np.arctan2(y, x), np.sqrt(x*x + y*y)


class RcStick:

    def __init__(self, stick_name, rmax):
        self.stick_name = stick_name
        self.rmax = rmax
        rect_carth_offs = 0.15
        rect_polar_offs = 0.075
        tick_intval = 20

        self.fig = plt.figure(figsize=fig_size)
        connect = self.fig.canvas.mpl_connect
        connect('key_press_event', self.on_key)

        # place carthesian grid in fig
        rect = [
            rect_carth_offs, rect_carth_offs,
            1-2*rect_carth_offs, 1 - 2*rect_carth_offs
        ]
        self.ax_carth = self.fig.add_axes(rect)

        # adjust x, y limits to match the one on the polar plot
        self.cf = (1-2*rect_carth_offs) / (1-2*rect_carth_offs-2*rect_polar_offs)
        self.ax_carth.set(
            xlim=(-self.cf*self.rmax, self.cf*self.rmax),
            ylim=(-self.cf*self.rmax, self.cf*self.rmax),
            aspect='equal'
        )
        # axis ticks
        ticks = np.arange(0, self.cf*rmax, tick_intval)
        ticks = sorted(np.append(-ticks[1:], ticks))
        self.ax_carth.set_xticks(ticks)
        self.ax_carth.set_yticks(ticks)

        # place polar grid in carthesian grid
        rect = [
            rect[0] + rect_polar_offs, rect[1] + rect_polar_offs,
            rect[2] - 2*rect_polar_offs, rect[3] - 2*rect_polar_offs
        ]
        self.ax_polar = self.fig.add_axes(rect, polar=True, frameon=False)
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

    def blit(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def stick_val(self, theta, r):
        self.stick_end.center = conv_polar_to_xy(np.radians(theta), r)
        self.stick.set_data([0, np.radians(theta)], [0, r])

    def bar_val(self, theta, r):
        x, y = conv_polar_to_xy(np.radians(theta), r)
        print(f'x={x}, y={y}')
        # plot the x and y values on the border of the graph
        bv = self.rmax * self.cf
        # from (0, -bv) to (x, -bv)
        self.bar_x.set_data([0, x], [-bv, -bv])
        # from (bv, 0) to (bv, y)
        self.bar_y.set_data([bv, bv], [0, y])

    def on_key(self, event):
        if event.key == ' ':
            self.input_vals()
            self.blit()

    def input_vals(self):
        answer = input('Give theta (degrees), radius: ')
        theta, r = (float(a) for a in re.split(r'\s|, ', answer))
        self.stick_val(theta, r)
        self.bar_val(theta, r)

if __name__ == '__main__':
    plt.ion()
    rc_left = RcStick('throttle', 80)
    while True:
        rc_left.input_vals()
        rc_left.blit()
