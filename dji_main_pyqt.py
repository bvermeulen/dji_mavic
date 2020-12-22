''' application to show dji mavic drone flights from UAV Drone csv files
'''
#TODO refactor remote control, graph and map modules to reduce code size of main program
#TODO load csv files with qt dialogue
#TODO port to QGIS

import sys
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication, QPushButton,
    QShortcut
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from dji_mavic_io import read_flightdata_csv
from dji_remote_control import RemoteControlDisplay, RcStick
from dji_flight_graphs import GraphDisplay, Graph
from dji_map import MapDisplay, DroneFlight


anticlockwise_symbol = '\u21b6'
clockwise_symbol = '\u21b7'
right_arrow_symbol = '\u25B6'
left_arrow_symbol = '\u25C0'

rc_max = 1684
rc_min = 364
rc_zero = 1024
miles_km_conv = 1.60934
feet_meter_conv = 0.3048
samplerate = 7


class DashboardShow(QWidget):

    def __init__(self, filename):
        super().__init__()
        flightdata_df = read_flightdata_csv(filename)

        self.fl_time = np.array(
            flightdata_df['time(millisecond)'].to_list(), dtype=np.float64
        ) / 1000
        self.gd = GraphDisplay()
        self.gd.setup(max(self.fl_time))
        ax_height = self.gd.get_ax_graph_1()
        ax_speed = self.gd.get_ax_graph_2()
        ax_dist = self.gd.get_ax_graph_3()

        self.fl_height = np.array(
            flightdata_df['height_above_takeoff(feet)'].to_list(), dtype=np.float64
        )
        self.graph_height = Graph(
            ax_height, 'height', 'feet', min(self.fl_height), max(self.fl_height),
            self.fl_time, self.fl_height,
        )
        self.fl_speed = np.array(
            flightdata_df['speed(mph)'].to_list(), dtype=np.float64
        ) * miles_km_conv
        self.graph_speed = Graph(
            ax_speed, 'speed', 'kph', min(self.fl_speed), max(self.fl_speed),
            self.fl_time, self.fl_speed,
        )
        self.fl_dist = np.array(
            flightdata_df['distance(feet)'].to_list(), dtype=np.float64
        ) * feet_meter_conv
        self.graph_dist = Graph(
            ax_dist, 'distance', 'meter', min(self.fl_dist), max(self.fl_dist),
            self.fl_time, self.fl_dist,
        )

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

        self.rc = RemoteControlDisplay()
        self.rc.setup(120)
        self.rc_left = RcStick('climb/ yaw', left=True)
        self.rc_right = RcStick('pitch/ roll', left=False)

        longitudes = np.array(flightdata_df['longitude'].to_list(), dtype=np.float64)
        latitudes = np.array(flightdata_df['latitude'].to_list(), dtype=np.float64)
        md = MapDisplay()
        md.setup(longitudes, latitudes)
        self.md_canvas = FigureCanvas(md.fig)
        self.dd = DroneFlight()
        self.gd_canvas = FigureCanvas(self.gd.fig)
        self.rc_canvas = FigureCanvas(self.rc.fig)

        self.initUI()

    def initUI(self):
        # main box
        vbox = QVBoxLayout()

        # setup displays
        hbox_displays = QHBoxLayout()

        vbox_left = QVBoxLayout()
        vbox_left.addWidget(self.gd_canvas)
        vbox_left.addWidget(self.rc_canvas)

        hbox_displays.addLayout(vbox_left)
        hbox_displays.addWidget(self.md_canvas)

        # setup status line
        hbox_statusline = QHBoxLayout()
        hbox_statusline.setAlignment(Qt.AlignLeft)
        status_label = QLabel()
        status_label.setText('Here come the text widgets for status ...')
        hbox_statusline.addWidget(status_label)

        # setup buttons
        hbox_buttons = QHBoxLayout()
        hbox_buttons.setAlignment(Qt.AlignLeft)

        start_button = QPushButton('run')
        start_button.clicked.connect(self.cntr_run)
        hbox_buttons.addWidget(start_button)

        pause_button = QPushButton('pause')
        pause_button.clicked.connect(self.cntr_pause)
        hbox_buttons.addWidget(pause_button)

        quit_button = QPushButton('quit')
        quit_button.clicked.connect(self.cntr_quit)
        hbox_buttons.addWidget(quit_button)

        vbox.addLayout(hbox_displays)
        vbox.addLayout(hbox_statusline)
        vbox.addLayout(hbox_buttons)

        self.setLayout(vbox)

        self.move(400, 300)
        self.setWindowTitle('DJI Mavi Pro ... ')
        self.show()

    def cntr_run(self):
        def rc_blit():
            if self.rc.background is None:
                self.rc.background = (
                    self.rc.fig.canvas.copy_from_bbox(self.rc.fig.bbox)
                )
                self.rc.draw()

            else:
                self.rc.fig.canvas.restore_region(self.rc.background)
                self.rc.fig.draw_artist(self.rc_left.stick)
                self.rc.fig.draw_artist(self.rc_left.stick_end)
                self.rc.fig.draw_artist(self.rc_left.bar_x)
                self.rc.fig.draw_artist(self.rc_left.bar_y)
                self.rc.fig.draw_artist(self.rc_right.stick)
                self.rc.fig.draw_artist(self.rc_right.stick_end)
                self.rc.fig.draw_artist(self.rc_right.bar_x)
                self.rc.fig.draw_artist(self.rc_right.bar_y)
                self.rc.fig.canvas.blit()
                self.rc.fig.canvas.flush_events()

        def gd_blit():
            if self.gd.background is None:
                self.gd.background = (
                    self.gd.fig.canvas.copy_from_bbox(self.gd.fig.bbox)
                )
                self.gd.draw()

            else:
                self.gd.fig.canvas.restore_region(self.gd.background)
                self.gd.fig.draw_artist(self.graph_height.graph)
                self.gd.fig.draw_artist(self.graph_speed.graph)
                self.gd.fig.draw_artist(self.graph_dist.graph)
                self.gd.fig.canvas.blit()
                self.gd.fig.canvas.flush_events()

        for index in range(0, len(self.dd.flightpoints), samplerate):
            self.rc_left.rc_vals(self.rc_yaw[index], self.rc_climb[index])
            self.rc_right.rc_vals(self.rc_roll[index], self.rc_pitch[index])
            rc_blit()

            self.graph_height.update(self.fl_time[:index], self.fl_height[:index])
            self.graph_speed.update(self.fl_time[:index], self.fl_speed[:index])
            self.graph_dist.update(self.fl_time[:index], self.fl_dist[:index])
            gd_blit()

            while self.dd.pause:
                self.dd.blit_drone()

            self.dd.update_location(self.dd.flightpoints[index])
            self.dd.blit_drone()

    def cntr_pause(self):
        self.dd.pause = not self.dd.pause

    def cntr_quit(self):
        self.close()


def main(filename=None):
    app = QApplication([])

    pic_show = DashboardShow(filename)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main(filename='./dji_mavic_test_data_2.csv')
