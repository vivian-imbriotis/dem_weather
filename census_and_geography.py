# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 10:38:46 2022

@author: vivia
"""

import pickle as pkl
import colorsys

#Data handling
import numpy as np
import pandas as pd
import shapefile
from shapely.geometry import shape

#Data viz
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.animation import FuncAnimation, PillowWriter
import seaborn as sns
from descartes import PolygonPatch

#Stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

ELLESLIE_RD = 94029
CENTRAL_LATTITUDE = -42
CENTRAL_LONGITUDE = 146.5
MAX_DISTANCE = 2

CENSUSFILE = shapefile.Reader("../data/census/tas_2016/Geography/SA1_2016_AUST.shp")

def color_from_loc(longitude, lattitude, clong=CENTRAL_LONGITUDE, 
                   clat=CENTRAL_LATTITUDE, dmax = 1.5):
    
    #Saturation and brightness based on distance from centre of tasmania
    longitude = (longitude - clong) / dmax
    lattitude = (lattitude - clat)  / dmax

    
    distance = np.sqrt((longitude)**2  + (lattitude)**2)
    s = v = min(1,distance / dmax)

    #Hue based on angle of vector from centre of tasmania
    h = (np.arctan2(lattitude, longitude) + np.pi) / 2 / np.pi
    return colorsys.hsv_to_rgb(h,s,v)

def make_gradient_image(res=500):
    X = np.linspace(CENTRAL_LONGITUDE - 2, CENTRAL_LONGITUDE + 2,res)
    Y = np.linspace(CENTRAL_LATTITUDE - 2, CENTRAL_LATTITUDE + 2,res)
    X,Y = np.meshgrid(X,Y)

    color = np.empty((res,res,3), dtype = float)
    #Super ugly way to step through this 2d array...
    for row in range(color.shape[0]):
        for col in range(color.shape[1]):
            color[row,col] = color_from_loc(X[row,col], Y[row,col],dmax=1.5)
    
    alpha = (np.sqrt((X - CENTRAL_LONGITUDE)**2 + (Y-CENTRAL_LATTITUDE)**2) < 2).astype(float)
    return X, Y, color, alpha


sns.set_style("darkgrid")
sns.set_context("paper")
plt.close('all')

class RegionDeletedException(Exception):
    '''
    This exception is raised when a census region is instantiated, but
    that census region no longer exists.
    '''
    pass

class Region:
    def __init__(self, shape_record):
        '''
        This object represents a single Statistical Area Level 1, the smallest
        geographic-level census region.
        These regions are used in the census in place of person-level
        data to preseve annonymity. 

        Parameters
        ----------
        shape_record : shapefile.ShapeRecord
            A single ShapeRecord object. Many of these are stored in a Shape
            (.shp) file. They can be recovered with the shapefile.iterShapeRecords
            method.


        Attributes
        ------
        state: str
            The Australian state within which the region is located
            
        id_7digit
            The 7-digit SA1 Census identifier
        
        id: str
            The main SA1 Census identifier (referred to as a 'maincode' in 
            some census documentation)
        
        area_sqkm: float
            The area of the region, in square kilometers
            
        shape: dict
            A geom_interface polygon. This can be passed to the descartes
            library for plotting. Internally it is a dict like so:
                {'type':'Polygon',
                 'coordinates':data}
            where data is a list of list of 2-tuples, representing a list
            of lines (i.e. a list of lists of points in R2).
            
        record: shapefile.ShapeRecord
            The raw record describing the region
        
        Raises
        ------
        RegionDeletedException
            Raised if the region no longer exists.
        '''
        if shape_record.shape.shapeTypeName=='NULL':
            raise RegionDeletedException("Region no longer exists")
            
        self.state = shape_record.record[3]
        self.id_7digit = int(shape_record.record[0])
        self.id = shape_record.record[1]
        self.area_sqkm = shape_record.record[4]
        self.shape = shape_record.shape.__geo_interface__
        try:
            self.centroid = shape(self.shape).centroid
        except ValueError:
            print(self.shape)
            raise
        self.record = shape_record.record
    
    def make_patch(self,color, fill=True):
        try:
            patch = PolygonPatch(self.shape,fc=(color if fill else "none"),
                                 ec = color, linewidth = 0.5)
        except:
            print(f"{self.record} set with color {color}")
            raise
        return patch

class State:
    def __init__(self,statename, sourcefile):
        self.name = statename
        self.regions = []
        for element in sourcefile.iterShapeRecords():
            try:
                if element.record[3]==self.name:
                    self.regions.append(Region(element))
            except RegionDeletedException:
                pass
        self.fig=None

    def plot_all_regions(self, cmap_callable = None, title = None, axes=False):
        sns.set_style("white")
        sns.set_context("paper")
        fig = plt.figure(tight_layout=True) 
        ax = fig.gca() 
        
        if axes:
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Lattitude")
            sns.despine(ax=ax, offset = 5, trim = False)
        else:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.axis('off')

        if cmap_callable==None:
            patches = [a.make_patch('k',fill=False) for i,a in enumerate(self.regions)]
        else:
            patches = [a.make_patch(cmap_callable(a)) for a in self.regions]
        for patch in patches:
            ax.add_patch(patch)
        ax.axis('scaled')
        self.fig = fig
        self.ax = ax
        if title is not None:
            ax.set_title(title)
        return fig

    
    def add_colorbar(self, cmap, norm, name = None):
        divider = make_axes_locatable(self.ax)
        cax = divider.append_axes("left", size="2%", pad=0.05)
        
        
        self.fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                         cax = cax,
                         orientation='vertical', label=name)
        cax.yaxis.set_ticks_position('left')
        cax.yaxis.set_label_position('left')
        
    def add_centroids(self):
        X = [r.centroid.x for r in self.regions]
        Y = [r.centroid.y for r in self.regions]
        self.ax.plot(X,Y,'o', label = "SA1 Centroids")
        self.ax.legend()
    
    def show(self):
        if self.fig is None:
            self.plot_all_regions()
        return self.fig.show()



tas_geom = State("Tasmania", CENSUSFILE)
if __name__=="__main__":
    fig = tas_geom.plot_all_regions(title="Tasmanian Statistical Areas (Level 1)",
                                    axes=True) 
    tas_geom.add_centroids()
    fig.show()

# plt.plot([s.long for s in all_tasmanian_stations],[s.lat for s in all_tasmanian_stations],
#          'o', color = "red", ms = 5, alpha = 0.7)


# start_time = all_tasmanian_stations[0].data.index[0]




# ax = fig.gca()

# xmin,xmax = ax.get_xlim()
# ymin,ymax = ax.get_ylim()

# RES = 500
# X = np.linspace(xmin,xmax,RES)
# Y = np.linspace(ymin,ymax,RES)
# X,Y = np.meshgrid(X,Y)

# grid = pd.DataFrame({'x':X.flatten(), 'y':Y.flatten()})

# def interpolate(time):
#     try:
#         precip = [station.data.air_temp[time] for station in all_tasmanian_stations]
#     except:
#         return
#     x = [float(station.long) for station in all_tasmanian_stations]
#     y = [float(station.lat) for station in all_tasmanian_stations]
#     training_set = pd.DataFrame({'x':x, 'y':y, 'precip': precip})
#     m = smf.ols("precip ~ 1 + te(cr(x, df=6), cr(y, df=6), constraints = 'center')",
#                 data = training_set)
#     result = m.fit()
#     image = result.predict(grid)
#     Z = image.to_numpy().reshape(RES,RES)
#     return Z

# with open("2016_2017_all_tas_stations.pkl", 'rb') as f:
#     all_tasmanian_stations = pkl.load(f)

# Z = interpolate(all_tasmanian_stations[0].data.index[0])
# artist = plt.imshow(Z, extent = (xmin, xmax, ymin, ymax), interpolation = "nearest",
#                     vmin = 0, vmax = 10)
# fig.colorbar(artist)

# Zs = [interpolate(all_tasmanian_stations[0].data.index[i]) for i in range(100)]
# Zs = [Z for Z in Zs if Z is not None]

# def update(frame):
#     artist.set_data(Zs[frame%len(Zs)])

# animation = FuncAnimation(fig,func = update, interval = 1000)

# plt.show()


