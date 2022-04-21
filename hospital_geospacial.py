# -*- coding: utf-8 -*-
"""
Created on Thu Apr 21 12:52:39 2022

@author: vivia

We need to make assumptions about which hospital people will attend, based
on their geographic location. The easiest assumption is that people will
go to the geographically nearest hospital. A better one is that they will
go to the hospital that minimizes travel TIME, which depends on road 
geography and quality. The OpenStreetMap Open Source Routing Machine service 
and nominatim reverse-geocoding service allow us to quantify the travel times. 

They also allow us to pull data for the locations of all four major hospitals
in the state
"""

import requests
import time
from diskcache import Cache

from seaborn import color_palette

nom_cache = Cache("nominatim_results")
osrm_cache= Cache("osrm_results")

class Hospital:
    def __init__(self, name, state = "Tasmania", color = None, address=None, long=None, lat=None):
        self.name = name
        self.state = state
        if any((address is None, long is None, lat is None)):
            address, long, lat = get_hospital_geodata_from_free_text(f"{self.name}, {self.state}")
        self.address = address
        self.long = float(long)
        self.lat  = float(lat)
        self.color = color
    def __repr__(self):
        return f"{self.name}||Longitude={self.long}, Lattitude = {self.lat}"

@osrm_cache.memoize()
def get_route(long_1, lat_1, long_2, lat_2):
    global NO_LOOKUPS
    if NO_LOOKUPS:
        NO_LOOKUPS = False
        print("Performing a non-cached API call. This probably means you are running this code for the first time. Unfortunately this will take some minutes...")
    r = requests.get(f"http://router.project-osrm.org/route/v1/car/{long_1},{lat_1};{long_2},{lat_2}?overview=false")
    try:
        route = r.json()["routes"][0] #routes is a single-element list
    except KeyError:
        return []
    return route


def get_travel_duration(long_1,lat_1,long_2,lat_2):
    try:
        return get_route(long_1, lat_1, long_2, lat_2)["duration"]
    except (TypeError):
        raise ValueError("No route found.")

@nom_cache.memoize()
def search_using_nominatim_for(search_text):
    print("Warning: performing a realtime search using Nominatim")
    print("Only one request per second can be sent, to comply with terms of use")
    print(f"Searching for: {search_text}...")
    time.sleep(2)
    r = requests.get(f"https://nominatim.openstreetmap.org/search?q={search_text}&format=json")
    results = r.json()
    return results

def get_hospital_geodata_from_free_text(address):
    results = search_using_nominatim_for(address)
    for result in results:
        if result["type"] == "hospital":
          return result["display_name"], result["lon"], result['lat']
    raise ValueError("No search results were tagged as hospital")


palette = color_palette()

rhh  = Hospital("Royal Hobart Hospital",       "Tasmania", color = palette[0])
lgh  = Hospital("Launceston General Hospital", "Tasmania", color = palette[1])
nwrh = Hospital("North West Regional Hospital","Tasmania", color = palette[2])
mch  = Hospital("Mersey Community Hospital",   "Tasmania", color = palette[3])


HOSPITALS = (rhh,lgh,nwrh, mch)

def get_nearest_hospital(long,lat, expensive = False):
    '''
    Returns the nearest of the 4 public tasmanian hospitals to a given
    (longitude, lattitude) location. If expensive is set to True,
    will use the Open Source Routing Machine to check which 
    of the hospitals would take the least time to drive to
    in a car. Otherwise, will just return the hospital
    that is physically closest (i.e. minimizes the L2 norm).

    Parameters
    ----------
    long : float
        Longitude.
    lat : float
        Lattitude.
    expensive : bool, optional
        Whether to query the OSRM API. The default is False.

    Returns
    -------
    Hospital
        The nearest public Tasmanian hospital.

    '''
    if expensive:
        try:
            return min(HOSPITALS, key = lambda h: get_travel_duration(long,lat,h.long,h.lat))
        except ValueError:
            return None
    else:
        return min(HOSPITALS, key=lambda h:(h.long - long)**2 + (h.lat - lat)**2)