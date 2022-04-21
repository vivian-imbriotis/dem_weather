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
"""

import requests
import time
from diskcache import Cache

cache = Cache("nominatim_results")


def get_route(long_1, lat_1, long_2, lat_2):
    r = requests.get(f"http://router.project-osrm.org/route/v1/car/{long_1},{lat_1};{long_2},{lat_2}?overview=false")
    route = r.get("routes")[0] #routes is a single-element list
    return route


def get_travel_duration(long_1,lat_1,long_2,lat_2):
    return get_route(long_1, lat_1, long_2, lat_2)["duration"]

@cache.memoize()
def search_using_nominatim_for(search_text):
    print("Warning: performing a realtime search using Nominatim")
    print("Only one request per second can be sent, to comply with terms of use")
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


rhh  = get_hospital_geodata_from_free_text("Royal Hobart Hospital, Tasmania")
lgh  = get_hospital_geodata_from_free_text("Launceston General Hospital, Tasmania")
nwrh = get_hospital_geodata_from_free_text("North West Regional Hospital, Tasmania")
mch  = get_hospital_geodata_from_free_text("Mersey Community Hospital, Tasmania")
