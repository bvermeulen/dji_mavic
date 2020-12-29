''' module input/ output for dji mavic pro
'''
import os
import psutil
import pandas as pd

flightdata_keys = [
    'time(millisecond)',
    'datetime(utc)',
    'latitude',
    'longitude',
    'height_above_takeoff(feet)',
    'height_above_ground_at_drone_location(feet)',
    'ground_elevation_at_drone_location(feet)',
    'altitude_above_seaLevel(feet)',
    'height_sonar(feet)',
    'speed(mph)',
    'distance(feet)',
    'satellites',
    'gpslevel',
    'voltage(v)',
    'max_altitude(feet)',
    'max_ascent(feet)',
    'max_speed(mph)',
    'max_distance(feet)',
    ' xSpeed(mph)',
    ' ySpeed(mph)',
    ' zSpeed(mph)',
    ' compass_heading(degrees)',
    ' pitch(degrees)',
    ' roll(degrees)',
    'isPhoto',
    'isVideo',
    'rc_elevator',
    'rc_aileron',
    'rc_throttle',
    'rc_rudder',
    'gimbal_heading(degrees)',
    'gimbal_pitch(degrees)',
    'battery_percent',
    'voltageCell1',
    'voltageCell2',
    'voltageCell3',
    'voltageCell4',
    'voltageCell5',
    'voltageCell6',
    'current(A)',
    'battery_temperature(f)',
    'altitude(feet)',
    'ascent(feet)',
    'flycStateRaw',
    'flycState',
    'message',
]

filename = 'dji_mavic_test_data.csv'

def read_flightdata_csv(file_name: str) -> pd.DataFrame:
    ''' read Airdata UAV - csv flightdata
        https://app.airdata.com/
        argument:
            filename: csv filename
        returns:
            pandas df
    '''
    empty_df = pd.DataFrame()
    try:
        flightdata_df = pd.read_csv(file_name)

    except Exception as e:
        print(f'unable to read {file_name}, error message: {e}')
        return empty_df

    for key in flightdata_df.keys():
        if key not in flightdata_keys:
            print(f'unable to read {file_name}, '
                  f'key "{key}" does not match Airdata UAV header')
            return empty_df

        # stop checking after the last 'official' key
        if key == 'message':
            break

    # returns flightdata dataframe, note it may not contain
    # all the keys
    return flightdata_df

def main():
    fd_df = read_flightdata_csv(filename)
    print(fd_df.head())
    process = psutil.Process(os.getpid())
    print(process, f': {process.memory_info().rss:,}')

if __name__ == '__main__':
    main()
