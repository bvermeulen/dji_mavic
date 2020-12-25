''' module for flight graphs dji mavic pro
'''
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
# from matplotlib import patches as mpl_patches
# from matplotlib import lines as mpl_lines


FEET_METER_CONV = 0.3048
MILES_KM_CONV = 1.60934
fig_size = (8, 4)
graph_light_color = 'lightgrey'
graph_dark_color = 'black'
graph_lw = 0.5
graph_xlabel = 'time (s)'

class GraphDisplay:

    def __init__(self, flightdata_df):
        mpl.rcParams['toolbar'] = 'None'
        self.fig, (self.ax_speed, self.ax_height, self.ax_dist) = plt.subplots(
            nrows=3, ncols=1, figsize=fig_size, sharex='all')
        self.fig.canvas.set_window_title('Flight graphs')
        self.fig.suptitle(None)
        self.background = None
        # self.fig.tight_layout()

        self.setup_graphs(flightdata_df)

    def setup_graphs(self, flightdata_df):
        self.fl_time = np.array(
            flightdata_df['time(millisecond)'].to_list(), dtype=np.float64) / 1000
        self.fl_height = np.array(
            flightdata_df['height_above_takeoff(feet)'].to_list(), dtype=np.float64)
        self.fl_speed = np.array(
            flightdata_df['speed(mph)'].to_list(), dtype=np.float64) * MILES_KM_CONV
        self.fl_dist = np.array(
            flightdata_df['distance(feet)'].to_list(), dtype=np.float64) * FEET_METER_CONV

        # height graph
        self.ax_height.plot(
            self.fl_time, self.fl_height, color=graph_light_color, linewidth=graph_lw,)
        self.graph_height, = self.ax_height.plot(
            [0], [0], color=graph_dark_color, linewidth=graph_lw, animated=True,)
        self.ax_height.set_ylim(min(self.fl_height)*1.1, max(self.fl_height)*1.1)
        self.ax_height.set_ylabel('Height\n(feet)')

        # speed graph
        self.ax_speed.plot(
            self.fl_time, self.fl_speed, color=graph_light_color, linewidth=graph_lw,)
        self.graph_speed, = self.ax_speed.plot(
            [0], [0], color=graph_dark_color, linewidth=graph_lw, animated=True,)
        self.ax_speed.set_ylim(min(self.fl_speed)*1.1, max(self.fl_speed)*1.1)
        self.ax_speed.set_ylabel('Velocity\n(km/ hour)')

        # distance graph
        _ = self.ax_dist.plot(
            self.fl_time, self.fl_dist, color=graph_light_color, linewidth=graph_lw,)
        self.graph_dist, = self.ax_dist.plot(
            [0], [0], color=graph_dark_color, linewidth=graph_lw, animated=True,)
        self.ax_dist.set_ylim(min(self.fl_dist)*1.1, max(self.fl_dist)*1.1)
        self.ax_dist.set_ylabel('Distance\n(meter)')

        # add the time axis
        self.ax_dist.set_xlabel(graph_xlabel)
        self.ax_dist.set_xlim(0, max(self.fl_time))

    def draw(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def update(self, index):
        self.graph_height.set_data(self.fl_time[:index], self.fl_height[:index],)
        self.graph_speed.set_data(self.fl_time[:index], self.fl_speed[:index],)
        self.graph_dist.set_data(self.fl_time[:index], self.fl_dist[:index],)

    def blit(self):
        if self.background is None:
            self.background = (
                self.fig.canvas.copy_from_bbox(self.fig.bbox)
            )
            self.draw()

        else:
            self.fig.canvas.restore_region(self.background)
            self.fig.draw_artist(self.graph_height)
            self.fig.draw_artist(self.graph_speed)
            self.fig.draw_artist(self.graph_dist)
            self.fig.canvas.blit()
            self.fig.canvas.flush_events()
