''' application to show dji mavic drone flights from UAV Drone csv files
'''
#TODO load csv files with qt dialogue, probably have to use QStackedWidget to be able to load another csv file
#TODO port to QGIS

import sys
import numpy as np
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication, QPushButton, QFileDialog
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from dji_mavic_io import read_flightdata_csv
from dji_remote_control import RemoteControlDisplay
from dji_flight_graphs import GraphDisplay
from dji_map import MapDisplay



anticlockwise_symbol = '\u21b6'
clockwise_symbol = '\u21b7'
right_arrow_symbol = '\u25B6'
left_arrow_symbol = '\u25C0'
samplerate = 5


class DashboardShow(QWidget):

    def __init__(self):
        super().__init__()
        self.flightflightdata_df = None
        self.md_canvas = FigureCanvas(Figure())
        self.gd_canvas = FigureCanvas(Figure())
        self.rc_canvas = FigureCanvas(Figure())
        self.md = None
        self.gd = None
        self.rcd = None

        self.initUI()

        self.move(400, 300)
        self.setWindowTitle('DJI Mavi Pro ... ')
        self.show()


    def initUI(self):
        # main box
        mainbox = QVBoxLayout()

        # setup displays
        self.hbox_displays = QHBoxLayout()

        vbox_left = QVBoxLayout()
        vbox_left.addWidget(self.gd_canvas)
        vbox_left.addWidget(self.rc_canvas)

        self.hbox_displays.addLayout(vbox_left)
        self.hbox_displays.addWidget(self.md_canvas)

        # setup status line
        hbox_statusline = QHBoxLayout()
        hbox_statusline.setAlignment(QtCore.Qt.AlignLeft)
        status_label = QLabel()
        status_label.setText('Here come the text widgets for status ...')
        hbox_statusline.addWidget(status_label)

        # setup buttons
        hbox_buttons = QHBoxLayout()
        hbox_buttons.setAlignment(QtCore.Qt.AlignLeft)

        selectfile_button = QPushButton('file')
        selectfile_button.clicked.connect(self.cntr_open)
        hbox_buttons.addWidget(selectfile_button)

        start_button = QPushButton('run')
        start_button.clicked.connect(self.cntr_run)
        hbox_buttons.addWidget(start_button)

        pause_button = QPushButton('pause')
        pause_button.clicked.connect(self.cntr_pause)
        hbox_buttons.addWidget(pause_button)

        quit_button = QPushButton('quit')
        quit_button.clicked.connect(self.cntr_quit)
        hbox_buttons.addWidget(quit_button)

        mainbox.addLayout(self.hbox_displays)
        mainbox.addLayout(hbox_statusline)
        mainbox.addLayout(hbox_buttons)

        self.setLayout(mainbox)


    def cntr_open(self):
        self.filename, _ = QFileDialog.getOpenFileName(self, 'OpenFile')
        print(self.filename)
        if not self.filename:
            return

        if self.md:
            self.rcd.on_close()
            self.gd.on_close()
            self.md.on_close()

        self.flightdata_df = read_flightdata_csv(self.filename)
        self.samples = len(self.flightdata_df)
        self.rcd = RemoteControlDisplay(self.flightdata_df)
        self.gd = GraphDisplay(self.flightdata_df)
        self.md = MapDisplay(self.flightdata_df)

        md_canvas = FigureCanvas(self.md.fig)
        self.hbox_displays.replaceWidget(self.md_canvas, md_canvas)
        gd_canvas = FigureCanvas(self.gd.fig)
        self.hbox_displays.replaceWidget(self.gd_canvas, gd_canvas)
        rc_canvas = FigureCanvas(self.rcd.fig)
        self.hbox_displays.replaceWidget(self.rc_canvas, rc_canvas)

        md_canvas.mpl_connect('resize_event', self.md.on_resize)
        gd_canvas.mpl_connect('resize_event', self.gd.on_resize)
        rc_canvas.mpl_connect('resize_event', self.rcd.on_resize)

        self.md_cancvas = md_canvas
        self.gd_cancvas = gd_canvas
        self.rc_cancvas = rc_canvas

    def cntr_run(self):
        if self.flightdata_df is None:
            return

        for index in range(0, self.samples, samplerate):
            self.rcd.update(index)
            self.rcd.blit()

            self.gd.update(index)
            self.gd.blit()

            self.md.update_location(index)
            self.md.blit()

            while self.md.pause:
                self.md.blit()

    def cntr_pause(self):
        if self.flightdata_df is None:
            return

        self.md.pause = not self.md.pause

    def cntr_quit(self):
        self.close()


def main(filename=None):
    app = QApplication([])

    pic_show = DashboardShow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main(filename='./dji_mavic_test_data_2.csv')
