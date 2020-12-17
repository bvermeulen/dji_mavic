''' module for flight graphs dji mavic pro
'''
# import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
# from matplotlib import patches as mpl_patches
# from matplotlib import lines as mpl_lines


fig_size = (6, 3)
graph_light_color = 'lightgrey'
graph_dark_color = 'black'
graph_lw = 0.5
graph_xlabel = 'time (s)'


class GraphDisplay:

    @classmethod
    def setup(cls, duration):
        mpl.rcParams['toolbar'] = 'None'
        cls.fig, (cls.ax_graph_1, cls.ax_graph_2, cls.ax_graph_3) = plt.subplots(
            nrows=3, ncols=1, figsize=fig_size, sharex='all')
        cls.fig.canvas.set_window_title('Flight graphs')
        cls.fig.suptitle(None)
        cls.fig.tight_layout()
        cls.ax_graph_3.set_xlabel(graph_xlabel)
        cls.ax_graph_3.set_xlim(0, duration)

    @classmethod
    def get_ax_graph_1(cls):
        return cls.ax_graph_1

    @classmethod
    def get_ax_graph_2(cls):
        return cls.ax_graph_2

    @classmethod
    def get_ax_graph_3(cls):
        return cls.ax_graph_3

    @classmethod
    def blit(cls):
        cls.fig.canvas.blit()
        cls.fig.canvas.flush_events()


class Graph(GraphDisplay):

    def __init__(self, ax, title, ylabel, min_y, max_y, x, y):
        self.graph_bg, = ax.plot(
            x, y, color=graph_light_color, linewidth=graph_lw,
        )
        self.graph, = ax.plot(
            [0], [0], color=graph_dark_color, linewidth=graph_lw,
        )
        ax.set_ylim(min_y*1.1, max_y*1.1)
        ax.set_title(title)
        ax.set_ylabel(ylabel)

    def update(self, x_values, y_values):
        self.graph.set_data(x_values, y_values,)
