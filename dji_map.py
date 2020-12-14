''' module for flightpath map for dji mavic pro
'''
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from geopandas import GeoDataFrame
from dji_mavic_io import read_flightdata_csv

rc_filename = 'dji_mavic_test_data.csv'
fig_size = (6, 6)
EPSG_WGS84 = 4326
EPSG_OSM = 3857
flightpath_color = 'grey'
homepoint_color = 'red'
homepoint_size = 500
drone_color = 'blue'
drone_size = 100

plt.ion()


class MapDisplay:

    @classmethod
    def setup(cls, lons, lats):
        cls.flightpoints = [Point(xy) for xy in zip(lons, lats)]
        cls.flightpath = [
            LineString([point1, point2]) for point1, point2
            in zip(cls.flightpoints, cls.flightpoints[1:])
        ]

        flightpath_gpd = GeoDataFrame(geometry=cls.flightpath)
        flightpath_gpd.crs = EPSG_WGS84
        print(flightpath_gpd.head(-100))

        cls.homepoint_gdp = GeoDataFrame(geometry=[cls.flightpoints[0]])
        cls.homepoint_gdp.crs = EPSG_WGS84

        cls.fig, cls.ax_map = plt.subplots(figsize=fig_size)
        flightpath_gpd.plot(ax=cls.ax_map, color=flightpath_color)
        cls.homepoint_gdp.plot(
            ax=cls.ax_map, marker='*', color=homepoint_color, markersize=homepoint_size
        )

    @classmethod
    def blit(cls):
        cls.fig.canvas.draw()
        cls.fig.canvas.flush_events()


class DroneFlight(MapDisplay):

    def __init__(self):
        self.drone_gdp = GeoDataFrame(geometry=self.homepoint_gdp.geometry)
        self.drone_gdp.crs = EPSG_WGS84
        self.drone_gdp.plot(
            ax=self.ax_map, marker='o', color=drone_color,
            markersize=drone_size, gid='drone'
        )

    def update_location(self, point):
        # below assumes ax_map 3rd collection item is the drone plot, this may not always
        # be true. In that case use the commented code below
        # for plot_object in self.ax_map.collections:
        #     if plot_object.get_gid() == 'drone':
        #         plot_object.remove()
        self.ax_map.collections[2].remove()
        self.drone_gdp.set_geometry([point], inplace=True)
        self.drone_gdp.plot(
            ax=self.ax_map, marker='o', color='blue', markersize=100, gid='drone'
        )

    def fly_drone(self):
        for i, point in enumerate(self.flightpoints):
            if i % 20 == 0:
                self.update_location(point)
                self.blit()
                print(f'{i:6}, long: {point.x:10.4f}, lat {point.y:10.4f}, '
                      f'map collections: {len(self.ax_map.collections)}')


if __name__ == '__main__':

    flightdata_df = read_flightdata_csv(rc_filename)
    longitudes = np.array(flightdata_df['longitude'].to_list(), dtype=np.float64)
    latitudes = np.array(flightdata_df['latitude'].to_list(), dtype=np.float64)
    md = MapDisplay()
    md.setup(longitudes, latitudes)
    drone = DroneFlight()

    input('enter to start ...')
    drone.fly_drone()
    input('enter to finish ...')
