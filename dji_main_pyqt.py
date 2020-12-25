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
from dji_remote_control import RemoteControlDisplay
from dji_flight_graphs import GraphDisplay
from dji_map import MapDisplay, DroneFlight


anticlockwise_symbol = '\u21b6'
clockwise_symbol = '\u21b7'
right_arrow_symbol = '\u25B6'
left_arrow_symbol = '\u25C0'
samplerate = 2


class DashboardShow(QWidget):

    def __init__(self, filename):
        super().__init__()
        flightdata_df = read_flightdata_csv(filename)

        self.gd = GraphDisplay(flightdata_df)
        self.rcd = RemoteControlDisplay(flightdata_df)

        longitudes = np.array(flightdata_df['longitude'].to_list(), dtype=np.float64)
        latitudes = np.array(flightdata_df['latitude'].to_list(), dtype=np.float64)
        md = MapDisplay()
        md.setup(longitudes, latitudes)
        self.md_canvas = FigureCanvas(md.fig)
        self.dd = DroneFlight()
        self.gd_canvas = FigureCanvas(self.gd.fig)
        self.rc_canvas = FigureCanvas(self.rcd.fig)

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

        for index in range(0, len(self.dd.flightpoints), samplerate):
            self.rcd.rc_vals(index)
            self.rcd.blit()

            self.gd.update(index)
            self.gd.blit()

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
    main(filename='./dji_mavic_test_data.csv')
