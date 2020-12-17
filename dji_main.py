''' dji main module
'''
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
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
samplerate = 5

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

    rc_roll = rc_roll[::samplerate]
    rc_pitch = rc_pitch[::samplerate]
    rc_yaw = rc_yaw[::samplerate]
    rc_climb = rc_climb[::samplerate]
    def rc_init():
        return (
            rc_left.stick, rc_left.stick_end, rc_right.stick, rc_right.stick_end,
            rc_left.bar_x, rc_left.bar_y, rc_right.bar_x, rc_right.bar_y,
        )

    def rc_animate(i):
        print(f'frame rc: {i}')
        rc_left.rc_vals(rc_yaw[i], rc_climb[i])
        rc_right.rc_vals(rc_roll[i], rc_pitch[i])
        return (
            rc_left.stick, rc_left.stick_end, rc_right.stick, rc_right.stick_end,
            rc_left.bar_x, rc_left.bar_y, rc_right.bar_x, rc_right.bar_y,
        )

    flightpoints = dd.flightpoints[::samplerate]
    def dd_init():
        return dd.drone,

    def dd_animate(i):
        print(f'frame dd: {i}')
        dd.update_location(flightpoints[i])
        return dd.drone,

    fl_time = fl_time[::samplerate]
    fl_height = fl_height[::samplerate]
    fl_speed = fl_speed[::samplerate]
    fl_dist = fl_dist[::samplerate]
    def gd_init():
        return graph_height.graph, graph_speed.graph, graph_dist.graph

    def gd_animate(i):
        print(f'frame gd: {i}')
        graph_height.update(fl_time[:i], fl_height[:i])
        graph_speed.update(fl_time[:i], fl_speed[:i])
        graph_dist.update(fl_time[:i], fl_dist[:i])
        return graph_height.graph, graph_speed.graph, graph_dist.graph

    dd_anim = animation.FuncAnimation(
        dd.fig, dd_animate, init_func=dd_init, interval=1,
        frames=len(flightpoints), repeat=False, blit=True
    )
    rc_anim = animation.FuncAnimation(
        dd.fig, rc_animate, init_func=rc_init, interval=1,
        frames=len(rc_pitch), repeat=False, blit=True
    )
    gd_anim = animation.FuncAnimation(
        gd.fig, gd_animate, init_func=gd_init, interval=1,
        frames=len(fl_time), repeat=False, blit=True
    )
    plt.show()


if __name__ == '__main__':
    dji_main()
