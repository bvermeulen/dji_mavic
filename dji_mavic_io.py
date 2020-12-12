''' module input/ output for dji mavic pro
'''
import os
import psutil
import pandas as pd


filename = 'dji_mavic_test_data.csv'

def read_flightdata_csv(file_name: str):
    ''' read Airdata UAV - csv flightdata
        https://app.airdata.com/
        argument:
            filename: csv filename
        returns:
            pandas df
    '''
    flightdata_df = pd.read_csv(file_name)
    process = psutil.Process(os.getpid())
    print(process, f': {process.memory_info().rss:,}')
    return flightdata_df

def main():
    fd_df = read_flightdata_csv(filename)
    print(fd_df.head())
    process = psutil.Process(os.getpid())
    print(process, f': {process.memory_info().rss:,}')

if __name__ == '__main__':
    main()