''' module for flight graphs dji mavic pro
'''
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry.polygon import Polygon
from geopandas import GeoSeries, GeoDataFrame
from dji_mavic_io import read_flightdata_csv

rc_filename = 'dji_mavic_test_data.csv'
fig_size = (8, 8)
EPSG_WGS84 = 4326
EPSG_OSM = 3857
edgecolor = 'black'
plt.ion()


class MapDisplay:

    @classmethod
    def setup(cls, lons, lats):
        # points = list(zip(longitude, latitude))
        flight_gpd = GeoDataFrame(geometry=GeoSeries(Polygon(zip(lons, lats))))
        flight_gpd.crs = EPSG_WGS84

        cls.fig, cls.ax_map = plt.subplots(figsize=fig_size)
        flight_gpd.plot(ax=cls.ax_map, facecolor='None', edgecolor=edgecolor)


if __name__ == '__main__':
    flightdata_df = read_flightdata_csv(rc_filename)
    longitude = np.array(flightdata_df['longitude'].to_list(), dtype=np.float64)
    latitude = np.array(flightdata_df['latitude'].to_list(), dtype=np.float64)
    MapDisplay.setup(longitude, latitude)
    input('Enter')