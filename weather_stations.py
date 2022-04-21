# -*- coding: utf-8 -*-
"""
Created on Tue Apr 12 17:22:11 2022

@author: vivia
"""

import os
import pickle as pkl
from datetime import datetime

#Data handling
import pandas as pd
#Plotting
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import seaborn as sns

#Local
import census_and_geography as geom

sns.set_style("darkgrid")
sns.set_context("paper")

dat_2016_2017 = r"data\bom2016_2017\BoM_ETA_20160501-20170430\obs"

STATIONS_METADATA_SOURCE = r"data\bom2016_2017\BoM_ETA_20160501-20170430\spatial\StationData.csv"

STATIONS_METADATA = pd.read_csv(STATIONS_METADATA_SOURCE)


def get_station_data_from_file(file, station_id):
    df = pd.read_csv(file)
    dat = df[df.station_number == station_id]
    temp = dat[dat.parameter == 'AIR_TEMP']
    temp.index = [datetime.fromtimestamp(i) for i in temp["valid_start"]]
    prcp = dat[dat.parameter == 'PRCP']
    prcp.index = [datetime.fromtimestamp(i) for i in prcp["valid_start"]]
    return temp,prcp

class Station:
    def __init__(self,data_source, station_id):
        #Our data source is either a CSV, a directory containing CSVs,
        #or a list of directories that each contain CSVs.
        if data_source[-4:]==".csv":
            all_files = data_source
        elif os.path.isdir(data_source):
            all_files = [file for file in os.listdir(data_source) if file[-4:]==".csv"]
            all_files = [os.path.join(data_source,file) for file in all_files]
        elif type(data_source)==list:
            #Everything in the list must be a directory
            assert(all((os.path.isdir(folder) for folder in data_source)))
            folders = (os.listdir(folder) for folder in data_source)
            all_files = []
            for folder in folders:
                files = [f for f in folder if f[-3:]=="csv"]
                files = [os.path.join(folder,file) for file in files]
                all_files.extend(files)
        else:
            raise ValueError("data_source for Station object must be csv, dir, or lst of dir")
        
        #Get temperature and precipitation data for this station from each file
        tmps, prcps = [], []
        for file in all_files:
            tmp, prcp = get_station_data_from_file(file, station_id)
            tmps.append(tmp); prcps.append(prcp)
        air_temp, precip = pd.concat(tmps), pd.concat(prcps)
        
        #Drop unneeded columns (e.g. units and station identifier)
        air_temp = air_temp[["value"]]
        air_temp.columns = ["air_temp"]
        precip = precip[["value"]]
        precip.columns = ["precipitation"]
        
        #This has 2 columns, air_temp and precipitation, and is indexed by datetimes
        self.data = air_temp.join(precip)
        
        #Access and store the remaining station metadata, e.g. location
        row = STATIONS_METADATA[STATIONS_METADATA.station_number==station_id]
        self.station_id = station_id
        (self.name, self.long, self.lat, self.state, 
         self.height) = (row.station_name.item(), float(row.LONGITUDE), 
                         float(row.LATITUDE), row.REGION.item(), 
                         float(row.STN_HT))
        
        #Assign a color based on longitude + lattitude
        self.color = geom.color_from_loc(self.long, self.lat)
    
    def glance_at(self):
        '''
        Create a figure showing the relative location of the station
        as well as its data (air temp and precipitation) over the
        recorded period.

        Returns
        -------
        fig : matplotlib.pyplot.Figure
            The created figure instance, which is also stored in self.fig.

        '''
        fig = plt.figure(tight_layout = True, figsize = (12,6))
        gridspec = GridSpec(2,4,fig)
        ax1 = fig.add_subplot(gridspec[0,0:-1])
        ax2 = fig.add_subplot(gridspec[1,0:-1])
        

        xmin, xmax = (geom.CENTRAL_LONGITUDE-geom.MAX_DISTANCE, 
                      geom.CENTRAL_LONGITUDE+geom.MAX_DISTANCE)
        
        ymin, ymax = (geom.CENTRAL_LATTITUDE-geom.MAX_DISTANCE, 
                      geom.CENTRAL_LATTITUDE+geom.MAX_DISTANCE)
        
        with sns.axes_style("white"):
            loc_ax = fig.add_subplot(gridspec[1,-1])

            loc_ax.plot([self.long], [self.lat], 'o', color = self.color)
            sns.utils.despine(fig,loc_ax)
        
            hue_ax = fig.add_subplot(gridspec[0,-1])
            
            x,y,color,alpha = geom.make_gradient_image()
            color[~alpha.astype(bool)] = [1,1,1]
            hue_ax.imshow(color, 
                          alpha=alpha, interpolation = "bicubic",
                          origin = 'lower',
                          extent = (xmin, xmax,ymin,ymax))
            sns.utils.despine(fig,hue_ax)
        
        
        loc_ax.set_xlim(xmin,xmax)
        loc_ax.set_ylim(ymin,ymax)
        loc_ax.set_aspect(1)
        
        for a in (loc_ax,hue_ax):
            a.set_ylabel("Lattitude")
            a.set_xlabel("Longitude")
        
        fig.suptitle(f"Weather data from station: {self.name}")
        ax1.set_ylabel("Air temp (C)")
        ax1.set_xlabel("Date")
        ax1.plot(self.data.air_temp, color = self.color)
        
        ax2.set_ylabel("Precipitation (mm)")
        ax1.set_xlabel("Date")
        ax2.plot(self.data.precipitation, color = self.color)
        self.fig = fig
        self.ax1, self.ax2, self.loc_ax = ax1, ax2, loc_ax
        return fig
    
    def add_station_to_figure(self,other_station):
        '''
        Superimpose another station's location and weather data over this
        station's self.glance_at() figure.
        
        >>station1, station2 = Station(*args1), Station(*args2)
        #Look at station1's data
        >>station1.glance_at()
        #Look at station2's data
        >>station2.glance_at()
        #Look at both on the same figure
        >>fig = station1.add_station_to_figure(station2)
        >>fig.show()
        
        
        Parameters
        ----------
        other_station : Station
            The station object to superimpose on this station's figure.

        Returns
        -------
        fig : matplotlib.pyplot.Figure
            The created figure instance, which is also stored in self.fig.
            Note self.fig will be overriden if self.glance_at() is called
            after this method.

        '''
        if not hasattr(self,"fig"):
            self.glance_at()
        self.fig.suptitle("")
        self.ax1.plot(other_station.data.air_temp, color = other_station.color)
        self.ax2.plot(other_station.data.precipitation, color = other_station.color)
        self.loc_ax.plot(other_station.long, other_station.lat, 'o', color=other_station.color)
        return self.fig
    
    def __repr__(self):
        return self.name


def preprocess_and_cache_all_stations(data_source, dst="2016_2017_all_tas_stations.pkl"):
    all_tasmanian_stations = []
    for idx, station in STATIONS_METADATA.iterrows():
        if station.REGION == "TAS/ANT":
            print(f"Reading data for station: {station.station_name}")
            all_tasmanian_stations.append(Station(data_source,station.station_number))

    with open(dst, 'wb') as file:
        pkl.dump(all_tasmanian_stations, file)

def get_all_stations_from_file(cache_file = "2016_2017_all_tas_stations.pkl"):
    with open(cache_file, 'rb') as file:
        all_tasmanian_stations = pkl.load(file)
    return all_tasmanian_stations

def vizualize_many_stations(list_of_stations):
    list_of_stations = list_of_stations.copy()
    first_station = list_of_stations.pop()
    for station in list_of_stations:
        first_station.add_station_to_glance(station)
    first_station.fig.show()

if __name__ == "__main__":
    #Show all data from every station in Tasmania
    all_stations = get_all_stations_from_file()
    vizualize_many_stations(all_stations)
    

    