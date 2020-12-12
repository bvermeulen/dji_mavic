''' dji main module
'''
import numpy as np
from dji_remote_control import RemoteControlDisplay, RcStick
from dji_flight_graphs import GraphDisplay, Graph
from dji_mavic_io import read_flightdata_csv


rc_filename = 'dji_mavic_test_data.csv'
rc_max = 1684
rc_min = 364
rc_zero = 1024
miles_km_conv = 1.60934


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

    gd = GraphDisplay()
    gd.setup()
    ax_height = gd.get_ax_graph_1()
    ax_speed = gd.get_ax_graph_2()

    fl_time = np.array(
        flightdata_df['time(millisecond)'].to_list(), dtype=np.float64
    ) / 1000
    fl_height = np.array(
        flightdata_df['height_above_takeoff(feet)'].to_list(), dtype=np.float64
    )
    graph_height = Graph(
        ax_height, 'height (feet)', max(fl_time), min(fl_height), max(fl_height)
    )
    fl_speed = np.array(
        flightdata_df['speed(mph)'].to_list(), dtype=np.float64
    ) * miles_km_conv
    graph_speed = Graph(
        ax_speed, 'speed (mph)', max(fl_time), 1.1 * min(fl_speed), max(fl_speed)
    )

    input('start')
    for i, (climb, yaw, pitch, roll)  in enumerate(
            zip(rc_climb, rc_yaw, rc_pitch, rc_roll)):

        while rcd.pause:
            rcd.blit()

        # blot diplay for every second of the flight (10 x 100 ms)
        # nominal there may be gaps if reception is poor
        if i % 50 == 0:
            rc_left.rc_vals(yaw, climb)
            rc_right.rc_vals(roll, pitch)
            rcd.blit()

            graph_height.update(fl_time[:i], fl_height[:i])
            graph_speed.update(fl_time[:i], fl_speed[:i])
            gd.blit()

        if i % 10 == 0:
            print(
                f'time: {i:5}, climb: {climb:10.4f}, yaw: {yaw:10.4f}, '
                f'pitch: {pitch:10.4f}, roll: {roll:10.4f}'
            )

    input('finish')


if __name__ == '__main__':
    dji_main()
