''' module for flightpath map for dji mavic pro
'''
import numpy as np
from matplotlib import patches as mpl_patches
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
import pyproj
from geopandas import GeoDataFrame
import contextily as ctx
from dji_mavic_io import read_flightdata_csv

rc_filename = 'dji_mavic_test_data_2.csv'
fig_size = (6, 6)
EPSG_WGS84 = 4326
EPSG_OSM = 3857
flightpath_color = 'grey'
homepoint_color = 'red'
homepoint_size = 500
drone_color = 'blue'
drone_size = 15
tr_wgs_osm = pyproj.Transformer.from_crs(EPSG_WGS84, EPSG_OSM)
plt.ion()


class MapDisplay:

    @classmethod
    def setup(cls, lons, lats):

        cls.fig, cls.ax_map = plt.subplots(figsize=fig_size)
        cls.fig.canvas.set_window_title('Drone flightpath')
        cls.fig.suptitle(None)
        # cls.background = cls.fig.canvas.copy_from_bbox(cls.fig.bbox)

        # create flightpoints and flightpath in osm projection
        cls.flightpoints = [
            Point(xy) for xy in tr_wgs_osm.itransform([xy for xy in zip(lats, lons)])
        ]

        cls.flightpath = [
            LineString([point1, point2]) for point1, point2
            in zip(cls.flightpoints, cls.flightpoints[1:])
        ]
        flightpath_gpd = GeoDataFrame(geometry=cls.flightpath)
        flightpath_gpd.crs = EPSG_OSM
        print(flightpath_gpd.head(-100))

        # set the homepoint and convert to map projection
        homepoint_gpd = GeoDataFrame(geometry=[cls.flightpoints[0]])
        homepoint_gpd.crs = EPSG_OSM

        # plot the flightpath in grey and convert to map projection
        flightpath_gpd.plot(ax=cls.ax_map, color=flightpath_color)
        homepoint_gpd.plot(
            ax=cls.ax_map, marker='*', color=homepoint_color, markersize=homepoint_size
        )
        cls.add_basemap_osm(source=ctx.providers.Esri.WorldStreetMap)

    @classmethod
    def add_basemap_osm(cls, source=ctx.providers.OpenStreetMap.Mapnik):
        ctx.add_basemap(cls.ax_map, source=source)

    @classmethod
    def blit(cls):
        # cls.fig.canvas.restore_region(cls.background)
        # cls.fig.canvas.draw()
        cls.fig.canvas.blit(cls.fig.bbox)
        cls.fig.canvas.flush_events()


class DroneFlight(MapDisplay):

    def __init__(self):
        self.drone = mpl_patches.Circle(
            (self.flightpoints[0].x, self.flightpoints[0].y),
            fc=drone_color, radius=drone_size)
        self.ax_map.add_patch(self.drone)

    def update_location(self, point):
        self.drone.center = (point.x, point.y)

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
