''' dji main module
'''
import numpy as np
import mapplotlib.pyplot as plt
from dji_remote_control import RemoteControlDisplay, RcStick
from dji_flight_graphs import GraphDisplay, Graph
from dji_map import MapDisplay, DroneFlight
from dji_mavic_io import read_flightdata_csv
from utils.plogger import Logger, timed

#pylint: disable=no-value-for-parameter
# for faster plotting check:
# https://stackoverflow.com/questions/40126176/fast-live-plotting-in-matplotlib-pyplot

rc_filename = 'dji_mavic_test_data_2.csv'
rc_max = 1684
rc_min = 364
rc_zero = 1024
miles_km_conv = 1.60934
feet_meter_conv = 0.3048
blit_rate = 25
show_rc = False
show_print = False

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

    if show_rc:
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

    @timed(logger)
    def remote_control_display(index):
        rc_left.rc_vals(rc_yaw[i], rc_climb[i])
        rc_right.rc_vals(rc_roll[i], rc_pitch[i])
        rcd.blit()

    @timed(logger)
    def graph_display(index):
        graph_height.update(fl_time[:index], fl_height[:index])
        graph_speed.update(fl_time[:index], fl_speed[:index])
        graph_dist.update(fl_time[:index], fl_dist[:index])
        gd.blit()

    @timed(logger)
    def drone_display(index):
        dd.update_location(dd.flightpoints[index])
        dd.blit()

    @timed(logger)
    def printval(index):
        print(
            f'time: {fl_time[index]:6}, '
            f'climb: {rc_climb[index]:10.4f}, yaw: {rc_yaw[index]:10.4f}, '
            f'pitch: {rc_pitch[index]:10.4f}, roll: {rc_roll[index]:10.4f}'
        )

    input('start')
    plt.show(block=False)
    for i in range(len(rc_climb)):

        while dd.pause:
            dd.blit()

        # blot diplay for every second of the flight (10 x 100 ms)
        # nominal there may be gaps if reception is poor
        if i % blit_rate == 0:
            if show_rc:
                remote_control_display(i)
            graph_display(i)
            drone_display(i)
            if show_print:
                printval(i)

    input('finish')


if __name__ == '__main__':
    dji_main()
