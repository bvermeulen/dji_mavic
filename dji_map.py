''' module for flightpath map for dji mavic pro
'''
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches as mpl_patches
from shapely.geometry import Point, LineString
import pyproj
from geopandas import GeoDataFrame
import contextily as ctx
from dji_mavic_io import read_flightdata_csv
from utils.plogger import Logger, timed

#pylint: disable=no-value-for-parameter

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

# Logging setup
Logger.set_logger('dji_map.log', '%(asctime)s:%(levelname)s:%(message)s', 'INFO')
logger = Logger.getlogger()


class MapDisplay:

    @classmethod
    def setup(cls, lons, lats):

        cls.fig, cls.ax_map = plt.subplots(figsize=fig_size)
        cls.fig.canvas.set_window_title('Drone flightpath')
        cls.fig.suptitle(None)

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
        cls.background = None


    @classmethod
    @timed(logger)
    def add_basemap_osm(cls, source=ctx.providers.OpenStreetMap.Mapnik):
        ctx.add_basemap(cls.ax_map, source=source)

    @classmethod
    @timed(logger)
    def draw(cls):
        cls.fig.canvas.draw()
        cls.fig.canvas.flush_events()


class DroneFlight(MapDisplay):

    def __init__(self):
        self.drone = mpl_patches.Circle(
            (self.flightpoints[0].x, self.flightpoints[0].y),
            fc=drone_color, radius=drone_size, animated=True
        )
        self.ax_map.add_patch(self.drone)
        # self.fig.canvas.draw()

        connect = self.fig.canvas.mpl_connect
        connect('key_press_event', self.on_key)
        connect('resize_event', self.on_resize)
        self.pause = True

    def update_location(self, _point):
        self.drone.center = (_point.x, _point.y)

    @timed(logger)
    def blit_drone(self):
        if self.background is None:
            self.background = (
                self.fig.canvas.copy_from_bbox(self.fig.bbox)
            )
            self.draw()

        else:
            self.fig.canvas.restore_region(self.background)
            self.fig.draw_artist(self.drone)
            self.fig.canvas.blit(self.fig.bbox)
            self.fig.canvas.flush_events()

    def on_key(self, event):
        if event.key == ' ':
            self.pause = not self.pause
            if self.pause:
                print('pause ...')

        if event.key == 's':
            self.fly_drone()

    def on_resize(self, event):
        print('resizing ...')
        # self.pause = True
        self.background = None

if __name__ == '__main__':

    flightdata_df = read_flightdata_csv(rc_filename)
    longitudes = np.array(flightdata_df['longitude'].to_list(), dtype=np.float64)
    latitudes = np.array(flightdata_df['latitude'].to_list(), dtype=np.float64)
    md = MapDisplay()
    md.setup(longitudes, latitudes)
    drone = DroneFlight()
    plt.show(block=False)
    plt.pause(0.1)
    input('continue ...')

    for point in drone.flightpoints[::2]:
        while drone.pause:
            drone.blit_drone()

        drone.update_location(point)
        drone.blit_drone()
