''' dji main module
'''
import matplotlib.pyplot as plt
from dji_remote_control import RemoteControlDisplay
from dji_flight_graphs import GraphDisplay
from dji_map import MapDisplay
from dji_mavic_io import read_flightdata_csv
from utils.plogger import Logger

#pylint: disable=no-value-for-parameter

# for faster plotting check:
# https://stackoverflow.com/questions/40126176/fast-live-plotting-in-matplotlib-pyplot
# https://matplotlib.org/3.3.1/tutorials/advanced/blitting.html

rc_filename = 'dji_mavic_test_data_2.csv'
samplerate = 5

# Logging setup
Logger.set_logger('dji_main.log', '%(asctime)s:%(levelname)s:%(message)s', 'INFO')
logger = Logger.getlogger()


def dji_main():
    flightdata_df = read_flightdata_csv(rc_filename)
    rd = RemoteControlDisplay(flightdata_df)
    gd = GraphDisplay(flightdata_df)
    md = MapDisplay(flightdata_df)

    plt.show(block=False)
    plt.pause(0.1)


    for index in range(0, len(flightdata_df), samplerate):
        rd.update(index)
        rd.blit()
        gd.update(index)
        gd.blit()
        md.update_location(index)
        md.blit()

        while md.pause:
            md.blit()

    input('enter to finish ...')

if __name__ == '__main__':
    dji_main()
