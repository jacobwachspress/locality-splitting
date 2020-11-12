import pandas as pd
import geopandas as gpd
import os
from pull_census_data import state_fips
from county_district_interpolation import district_attribute
from county_district_interpolation import distribute_label
from county_district_interpolation import get_district_year

base_path = 'clean_data/' + 'WY' + '/'

# Get the relevant redistricting plans
files = os.listdir(base_path)
files = [x for x in files if x[-4:] == '.shp']
sldl = [x for x in files if 'sldl' in x]
sldu = [x for x in files if 'sldu' in x]
cd = [x for x in files if 'cd' in x]

# Sort and recombine so we interpolate in proper order
sldl.sort()
sldu.sort()
cd.sort()
files = sldl + sldu + cd
district_years = [get_district_year(x) for x in files]


df = gpd.read_file('wy_test_county.shp')
print(df.head())
