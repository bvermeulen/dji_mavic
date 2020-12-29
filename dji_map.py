''' module for flightpath map for dji mavic pro
'''
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches as mpl_patches
import pyproj
from shapely.geometry import Point, LineString
from geopandas import GeoDataFrame
import contextily as ctx
from dji_mavic_io import read_flightdata_csv

#pylint: disable=no-value-for-parameter

fig_size = (6, 6)
EPSG_WGS84 = 4326
EPSG_OSM = 3857
flightpath_color = 'grey'
homepoint_color = 'red'
homepoint_size = 500
drone_color = 'blue'
drone_size = 15
tr_wgs_osm = pyproj.Transformer.from_crs(EPSG_WGS84, EPSG_OSM)


class MapDisplay:
    ''' display of drone with osm map in background
        methods:
            add_basemap_osm: set background map from ctx.providers.OpenStreetMap.Mapnik
            draw: initial draw
            update_location: update drone location
            blit: blit the drone on the map
            on_key: pause on key
            on_resize: redraws on resize
    '''

    def __init__(self, flightdata_df):

        # create flightpoints and flightpath in osm projection
        lons = np.array(flightdata_df['longitude'].to_list(), dtype=np.float64)
        lats = np.array(flightdata_df['latitude'].to_list(), dtype=np.float64)
        self.flightpoints = [
            Point(xy) for xy in tr_wgs_osm.itransform([xy for xy in zip(lats, lons)])
        ]
        self.flightpath = [
            LineString([point1, point2]) for point1, point2
            in zip(self.flightpoints, self.flightpoints[1:])
        ]
        flightpath_gpd = GeoDataFrame(geometry=self.flightpath)
        flightpath_gpd.crs = EPSG_OSM
        print(flightpath_gpd.head(-100))

        # set the homepoint and convert to map projection
        homepoint_gpd = GeoDataFrame(geometry=[self.flightpoints[0]])
        homepoint_gpd.crs = EPSG_OSM

        # create the figure and axes
        self.fig, self.ax_map = plt.subplots(figsize=fig_size)
        self.fig.canvas.set_window_title('Drone flightpath')
        self.fig.suptitle(None)

        # plot the flightpath in grey and convert to map projection and add basemap
        flightpath_gpd.plot(ax=self.ax_map, color=flightpath_color)
        homepoint_gpd.plot(
            ax=self.ax_map, marker='*', color=homepoint_color, markersize=homepoint_size
        )
        self.add_basemap_osm(source=ctx.providers.Esri.WorldStreetMap)
        self.background = None

        # add the drone
        self.drone = mpl_patches.Circle(
            (self.flightpoints[0].x, self.flightpoints[0].y),
            fc=drone_color, radius=drone_size, animated=True
        )
        self.ax_map.add_patch(self.drone)

        # make connections for key and figure resize
        connect = self.fig.canvas.mpl_connect
        connect('key_press_event', self.on_key)
        connect('resize_event', self.on_resize)
        self.pause = True

    def add_basemap_osm(self, source=ctx.providers.OpenStreetMap.Mapnik):
        ctx.add_basemap(self.ax_map, source=source)

    def draw(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def update_location(self, index):
        point = self.flightpoints[index]
        self.drone.center = (point.x, point.y)

    def blit(self):
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

        if event.key == 's':
            self.fly_drone()

    def on_resize(self, event):
        self.background = None

    def remove_fig(self):
        self.background = None
        plt.close(self.fig)

    def __repr__(self):
        return (f'drone homepoint at: '
                f'{int(self.flightpoints[0].x):,}, {int(self.flightpoints[0].y):,}')


if __name__ == '__main__':
    samplerate = 2
    rc_filename = 'dji_mavic_test_data_2.csv'

    flightdata_df = read_flightdata_csv(rc_filename)
    md = MapDisplay(flightdata_df)
    print(md)
    plt.show(block=False)
    plt.pause(0.1)
    input('continue ...')

    for index in range(0, len(flightdata_df), samplerate):
        while md.pause:
            md.blit()

        md.update_location(index)
        md.blit()
