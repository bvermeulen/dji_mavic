''' application to show dji mavic drone flights from UAV Drone csv files
'''
import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication, QPushButton,
    QFileDialog, QStackedWidget,
)
from dji_mavic_io import read_flightdata_csv
from dji_remote_control import RemoteControlDisplay
from dji_flight_graphs import GraphDisplay
from dji_map import MapDisplay

#TODO port to QGIS

#pylint: disable=c-extension-no-member


anticlockwise_symbol = '\u21b6'
clockwise_symbol = '\u21b7'
right_arrow_symbol = '\u25B6'
left_arrow_symbol = '\u25C0'
samplerate = 5


class DashboardShow(QWidget):

    def __init__(self):
        super().__init__()
        self.flightflightdata_df = None
        self.md, self.gd, self.rcd = None, None, None

        self.md_stack = QStackedWidget(self)
        self.md_stack.addWidget(FigureCanvas(Figure()))
        self.gd_stack = QStackedWidget(self)
        self.gd_stack.addWidget(FigureCanvas(Figure()))
        self.rc_stack = QStackedWidget(self)
        self.rc_stack.addWidget(FigureCanvas(Figure()))
        self.stack_depth = 0

        self.initUI()

        self.move(400, 300)
        self.setWindowTitle('DJI Mavic Pro ... ')
        self.show()


    def initUI(self):
        # main box
        mainbox = QVBoxLayout()

        # setup displays
        self.hbox_displays = QHBoxLayout()

        vbox_left = QVBoxLayout()
        vbox_left.addWidget(self.gd_stack)
        vbox_left.addWidget(self.rc_stack)

        self.hbox_displays.addLayout(vbox_left)
        self.hbox_displays.addWidget(self.md_stack)

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
        #TODO add filename checker and handle case there is no lat-lon
        self.flightdata_df = read_flightdata_csv(self.filename)

        if self.flightdata_df.empty:
            return

        if self.md:
            self.rcd.remove_fig()
            self.gd.remove_fig()
            self.md.remove_fig()

        self.samples = len(self.flightdata_df)
        self.rcd = RemoteControlDisplay(self.flightdata_df)
        self.gd = GraphDisplay(self.flightdata_df)
        self.md = MapDisplay(self.flightdata_df)

        md_canvas = FigureCanvas(self.md.fig)
        gd_canvas = FigureCanvas(self.gd.fig)
        rc_canvas = FigureCanvas(self.rcd.fig)

        md_canvas.mpl_connect('resize_event', self.md.on_resize)
        gd_canvas.mpl_connect('resize_event', self.gd.on_resize)
        rc_canvas.mpl_connect('resize_event', self.rcd.on_resize)

        self.md_stack.addWidget(md_canvas)
        self.gd_stack.addWidget(gd_canvas)
        self.rc_stack.addWidget(rc_canvas)
        self.stack_depth += 1
        print(f'stack depth: {self.stack_depth}')

        self.md_stack.setCurrentIndex(self.stack_depth)
        self.gd_stack.setCurrentIndex(self.stack_depth)
        self.rc_stack.setCurrentIndex(self.stack_depth)

        self.md.on_resize(None)
        self.gd.on_resize(None)
        self.rcd.on_resize(None)

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
        sys.exit()


def main():
    app = QApplication([])
    _ = DashboardShow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
