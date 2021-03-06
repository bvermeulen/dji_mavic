''' application to show dji mavic drone flights from UAV Drone csv files
'''
import sys
from pathlib import Path
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
samplerate = 3
display_frequency = 10  # display is every 10 * 3 samples

class DashboardShow(QWidget):

    def __init__(self):
        super().__init__()
        self.md, self.gd, self.rcd = None, None, None
        self.samples = None
        self.cntr_enabled = False
        self.avg_height, self.avg_speed, self.avg_distance = 0, 0, 0
        self.display_counter = 0
        self.loop_running = False

        self.md_stack = QStackedWidget(self)
        self.md_stack.addWidget(FigureCanvas(Figure()))
        self.gd_stack = QStackedWidget(self)
        self.gd_stack.addWidget(FigureCanvas(Figure()))
        self.rc_stack = QStackedWidget(self)
        self.rc_stack.addWidget(FigureCanvas(Figure()))
        self.stack_depth = 0

        self.initUI()

        self.move(200, 100)
        self.setWindowTitle('DJI Mavic Pro ... ')
        self.show()

    def initUI(self):
        # main box
        mainbox = QVBoxLayout()

        # setup displays
        hbox_displays = QHBoxLayout()

        vbox_left = QVBoxLayout()
        vbox_left.addWidget(self.gd_stack)
        vbox_left.addWidget(self.rc_stack)

        hbox_displays.addLayout(vbox_left)
        hbox_displays.addWidget(self.md_stack)

        # setup status line
        hbox_statusline = QHBoxLayout()
        hbox_statusline.setAlignment(QtCore.Qt.AlignLeft)
        self.status_label = QLabel()
        self.status_label.setText(' status window ...')
        hbox_statusline.addWidget(self.status_label)

        # setup buttons
        hbox_buttons = QHBoxLayout()
        hbox_buttons.setAlignment(QtCore.Qt.AlignLeft)

        selectfile_button = QPushButton('file')
        selectfile_button.setFocusPolicy(QtCore.Qt.NoFocus)
        selectfile_button.clicked.connect(self.cntr_open)
        hbox_buttons.addWidget(selectfile_button)

        start_button = QPushButton('run')
        start_button.setFocusPolicy(QtCore.Qt.NoFocus)
        start_button.clicked.connect(self.cntr_run)
        hbox_buttons.addWidget(start_button)

        pause_button = QPushButton('pause')
        pause_button.clicked.connect(self.cntr_pause)
        pause_button.setFocusPolicy(QtCore.Qt.NoFocus)
        hbox_buttons.addWidget(pause_button)

        stop_button = QPushButton('stop')
        stop_button.clicked.connect(self.cntr_stop)
        stop_button.setFocusPolicy(QtCore.Qt.NoFocus)
        hbox_buttons.addWidget(stop_button)

        quit_button = QPushButton('quit')
        quit_button.clicked.connect(self.cntr_quit)
        quit_button.setFocusPolicy(QtCore.Qt.NoFocus)
        hbox_buttons.addWidget(quit_button)

        self.filename_label = QLabel()
        self.filename_label.setText('file: ')
        hbox_buttons.addWidget(self.filename_label)

        mainbox.addLayout(hbox_displays)
        mainbox.addLayout(hbox_statusline)
        mainbox.addLayout(hbox_buttons)

        self.setLayout(mainbox)

    def display_status(self, time_ms, height, speed, distance):
        if self.display_counter == display_frequency:
            t = (
                f'{time_ms:5.0f}: '
                f'{self.avg_height/ self.display_counter:4.0f} ft, '
                f'{self.avg_speed / self.display_counter:4.0f} km/h, '
                f'{self.avg_distance / self.display_counter:4.0f} meter'
            )
            self.status_label.setText(t)
            self.avg_height = 0
            self.avg_speed = 0
            self.avg_distance = 0
            self.display_counter = 0

        else:
            if self.display_counter == 1:
                self.avg_height = height
                self.avg_speed = speed
                self.avg_distance = distance

            else:
                self.avg_height += height
                self.avg_speed += speed
                self.avg_distance += distance

        self.display_counter += 1

    def cntr_open(self):
        if self.loop_running:
            return

        filename, _ = QFileDialog.getOpenFileName(self, 'OpenFile')
        filename = Path(filename)
        flightdata_df = read_flightdata_csv(filename)

        if flightdata_df.empty:
            return

        self.filename_label.setText(f'file: {filename.name}')
        self.mplfigs_to_canvas(flightdata_df)
        self.cntr_enabled = True
        self.pause = False

    def cntr_run(self):
        if not self.cntr_enabled:
            return

        # display initial statys
        self.display_counter = display_frequency
        vals = self.gd.update(0)
        self.display_status(*vals)

        self.loop_running = True
        for index in range(0, self.samples, samplerate):
            if not self.loop_running:
                break

            self.rcd.update(index)
            self.rcd.blit()

            vals = self.gd.update(index)
            self.display_status(*vals)

            self.gd.blit()

            self.md.update_location(index)
            self.md.blit()

            while self.pause:
                self.md.blit()
                if not self.loop_running:
                    break

        self.loop_running = False

    def cntr_pause(self):
        if not self.cntr_enabled:
            return

        self.pause = not self.pause

    def cntr_stop(self):
        if not self.cntr_enabled:
            return

        self.loop_running = False
        self.cntr_enabled = False

    def cntr_quit(self):
        self.close()
        sys.exit()

    def keyPressEvent(self, event):
        # if spacebar pressed pause
        if event.key() == 32:
            self.pause = not self.pause

    def mplfigs_to_canvas(self, flightdata_df):
        if self.md:
            self.rcd.remove_fig()
            self.gd.remove_fig()
            self.md.remove_fig()

        self.samples = len(flightdata_df)
        self.rcd = RemoteControlDisplay(flightdata_df)
        self.gd = GraphDisplay(flightdata_df)
        self.md = MapDisplay(flightdata_df)

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


def main():
    app = QApplication([])
    _ = DashboardShow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
