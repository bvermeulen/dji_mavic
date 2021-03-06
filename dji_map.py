''' module for flightpath map for dji mavic pro
'''
import json
from decouple import config
import numpy as np
from matplotlib import ticker
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
flightpath_color = 'yellow'
homepoint_color = 'red'
homepoint_size = 500
drone_color = 'blue'
drone_size = 15
arial_limit = 150  # meter
tick_intval = 500  # meter
tr_wgs_osm = pyproj.Transformer.from_crs(EPSG_WGS84, EPSG_OSM)


@ticker.FuncFormatter
def major_formatter(x, pos):
    ''' formatter to show only the last 4 digipythonts '''
    return f'{x % 10_000:.0f}'


def read_json_maptiler(json_file):
    try:
        with open(json_file) as f:
            maptiler_source = json.load(f)
            maptiler_source['url'] = ''.join([
                maptiler_source['url'], '?key=', config('maptiler_api_key')
            ])
            return maptiler_source

    except (KeyError, FileNotFoundError):
        return None


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

        # set the homepoint and convert to map projection
        homepoint_gpd = GeoDataFrame(geometry=[self.flightpoints[0]])
        homepoint_gpd.crs = EPSG_OSM

        # create the figure and axes
        self.fig, self.ax_map = plt.subplots(figsize=fig_size)
        self.fig.canvas.set_window_title('Drone flightpath')
        self.fig.suptitle(None)

        self.ax_map.xaxis.set_major_formatter(major_formatter)
        self.ax_map.yaxis.set_major_formatter(major_formatter)
        self.ax_map.xaxis.set_major_locator(ticker.MultipleLocator(tick_intval))
        self.ax_map.yaxis.set_major_locator(ticker.MultipleLocator(tick_intval))

        # plot the flightpath, homepoint
        flightpath_gpd.plot(ax=self.ax_map, color=flightpath_color)
        homepoint_gpd.plot(
            ax=self.ax_map, marker='*', color=homepoint_color, markersize=homepoint_size
        )

        # adjust map limits to make x and y dimensions the same
        xlimits = list(self.ax_map.get_xlim())
        ylimits = list(self.ax_map.get_ylim())
        if xlimits[1] - xlimits[0] > ylimits[1] - ylimits[0]:
            xlimits[0] -= arial_limit
            xlimits[1] += arial_limit
            self.ax_map.set_xlim(xlimits[0], xlimits[1])
            dist = 0.5 * (xlimits[1] - xlimits[0])
            yc = 0.5 * (ylimits[1] + ylimits[0])
            self.ax_map.set_ylim(yc - dist, yc + dist)

        else:
            ylimits[0] -= arial_limit
            ylimits[1] += arial_limit
            self.ax_map.set_ylim(ylimits[0], ylimits[1])
            dist = 0.5 * (ylimits[1] - ylimits[0])
            xc = 0.5 * (xlimits[1] + xlimits[0])
            self.ax_map.set_xlim(xc - dist, xc + dist)

        # add the basemap
        # ctx.providers.Esri.WorldStreetMap
        self.add_basemap_osm(source='maptiler_hybrid.json')
        self.background = None

        # add the drone
        self.drone = mpl_patches.Circle(
            (self.flightpoints[0].x, self.flightpoints[0].y),
            fc=drone_color, radius=drone_size, animated=True
        )
        self.ax_map.add_patch(self.drone)

        # make connections for key and figure resize
        connect = self.fig.canvas.mpl_connect
        connect('resize_event', self.on_resize)

    def add_basemap_osm(self, source=None):
        if source is None:
            maptiler_source = ctx.providers.OpenStreetMap.Mapnik

        elif isinstance(source, str):
            maptiler_source = read_json_maptiler(source)
            if not maptiler_source:
                maptiler_source = ctx.providers.OpenStreetMap.Mapnik

        else:
            maptiler_source = source

        ctx.add_basemap(self.ax_map, source=maptiler_source)

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
