''' dji main module
'''
import numpy as np
import matplotlib.pyplot as plt
from dji_remote_control import RemoteControlDisplay, RcStick
from dji_flight_graphs import GraphDisplay, Graph
from dji_map import MapDisplay, DroneFlight
from dji_mavic_io import read_flightdata_csv
from utils.plogger import Logger, timed

#pylint: disable=no-value-for-parameter

# for faster plotting check:
# https://stackoverflow.com/questions/40126176/fast-live-plotting-in-matplotlib-pyplot
# https://matplotlib.org/3.3.1/tutorials/advanced/blitting.html

rc_filename = 'dji_mavic_test_data_2.csv'
rc_max = 1684
rc_min = 364
rc_zero = 1024
miles_km_conv = 1.60934
feet_meter_conv = 0.3048
samplerate = 3

# Logging setup
Logger.set_logger('dji_main.log', '%(asctime)s:%(levelname)s:%(message)s', 'INFO')
logger = Logger.getlogger()


def dji_main():
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

    rcd = RemoteControlDisplay()
    rcd.setup(120)
    rc_left = RcStick('climb/ yaw', left=True)
    rc_right = RcStick('pitch/ roll', left=False)

    fl_time = np.array(
        flightdata_df['time(millisecond)'].to_list(), dtype=np.float64
    ) / 1000
    gd = GraphDisplay()
    gd.setup(max(fl_time))
    ax_height = gd.get_ax_graph_1()
    ax_speed = gd.get_ax_graph_2()
    ax_dist = gd.get_ax_graph_3()

    fl_height = np.array(
        flightdata_df['height_above_takeoff(feet)'].to_list(), dtype=np.float64
    )
    graph_height = Graph(
        ax_height, 'height', 'feet', min(fl_height), max(fl_height), fl_time, fl_height,
    )
    fl_speed = np.array(
        flightdata_df['speed(mph)'].to_list(), dtype=np.float64
    ) * miles_km_conv
    graph_speed = Graph(
        ax_speed, 'speed', 'kph', min(fl_speed), max(fl_speed), fl_time, fl_speed,
    )
    fl_dist = np.array(
        flightdata_df['distance(feet)'].to_list(), dtype=np.float64
    ) * feet_meter_conv
    graph_dist = Graph(
        ax_dist, 'distance', 'meter', min(fl_dist), max(fl_dist), fl_time, fl_dist,
    )

    longitudes = np.array(flightdata_df['longitude'].to_list(), dtype=np.float64)
    latitudes = np.array(flightdata_df['latitude'].to_list(), dtype=np.float64)
    md = MapDisplay()
    md.setup(longitudes, latitudes)
    dd = DroneFlight()
    plt.show(block=False)

    input('enter to start ...')

    # combined blit for remote control
    @timed(logger)
    def rc_blit():
        if rcd.background is None:
            rcd.background = (
                rcd.fig.canvas.copy_from_bbox(rcd.fig.bbox)
            )
            rcd.draw()

        else:
            rcd.fig.canvas.restore_region(rcd.background)
            rcd.fig.draw_artist(rc_left.stick)
            rcd.fig.draw_artist(rc_left.stick_end)
            rcd.fig.draw_artist(rc_left.bar_x)
            rcd.fig.draw_artist(rc_left.bar_y)
            rcd.fig.draw_artist(rc_right.stick)
            rcd.fig.draw_artist(rc_right.stick_end)
            rcd.fig.draw_artist(rc_right.bar_x)
            rcd.fig.draw_artist(rc_right.bar_y)
            rcd.fig.canvas.blit()
            rcd.fig.canvas.flush_events()

    @timed(logger)
    def gr_blit():
        if gd.background is None:
            gd.background = (
                gd.fig.canvas.copy_from_bbox(gd.fig.bbox)
            )
            gd.draw()

        else:
            gd.fig.canvas.restore_region(gd.background)
            gd.fig.draw_artist(graph_height.graph)
            gd.fig.draw_artist(graph_speed.graph)
            gd.fig.draw_artist(graph_dist.graph)
            gd.fig.canvas.blit()
            rcd.fig.canvas.flush_events()

    for index in range(0, len(fl_time), samplerate):
        rc_left.rc_vals(rc_yaw[index], rc_climb[index])
        rc_right.rc_vals(rc_roll[index], rc_pitch[index])
        rc_blit()

        graph_height.update(fl_time[:index], fl_height[:index])
        graph_speed.update(fl_time[:index], fl_speed[:index])
        graph_dist.update(fl_time[:index], fl_dist[:index])
        gr_blit()

        while dd.pause:
            dd.blit_drone()

        dd.update_location(dd.flightpoints[index])
        dd.blit_drone()

    input('enter to finish ...')

if __name__ == '__main__':
    dji_main()
