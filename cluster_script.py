# -*- coding: utf-8 -*-
"""
Created on Thu May  2 10:00:54 2019

@author: Jacob
"""
import geopandas as gpd
import sys
import os
from geoprocessing import county_district_intersection_pops, same_plan, \
                          dict_to_json


state = sys.argv[1]
series = sys.argv[2]

input_path = '/scratch/network/jacobmw/Data'
output_path = '/home/jacobmw/Output'


congresses = ['2018_congress.shp', '2016_congress.shp', '2014_congress.shp', \
              '2012_congress.shp', '2010_congress.shp', '2008_congress.shp', \
              '2006_congress.shp', '2004_congress.shp', '2002_congress.shp', \
              '2000_congress.shp', '1998_congress.shp']

uppers = ['2017_upper_leg.shp', '2016_upper_leg.shp', '2015_upper_leg.shp', \
          '2014_upper_leg.shp', '2013_upper_leg.shp', '2010_upper_leg.shp', \
          '2006_upper_leg.shp']

lowers = ['2017_lower_leg.shp', '2016_lower_leg.shp', '2015_lower_leg.shp', \
          '2014_lower_leg.shp', '2013_lower_leg.shp', '2010_lower_leg.shp', \
          '2006_lower_leg.shp']

plans = []
if series == 'c':
    plans = congresses
elif series == 'u':
    plans = uppers
else:
    plans = lowers


# catch errors
failed = []

try:
    # get the shapefiles to check
    shapefiles = [file for file in os.listdir(input_path) if \
                  file[-4:] == '.shp']
    shapefiles = [file for file in plans if file in shapefiles]
    
    # figure out which files we need to check
    dfs = []
    dfs_to_test = []
    for i in plans:
        dfs.append((i, gpd.read_file(f'{input_path}/{state}/{i}')))
    for i in range(len(dfs)):
        if i == 0:
            dfs_to_test.append(dfs[i])
        else:
            df = dfs[i][1]
            df_last = dfs[i-1][1]
            if not same_plan(df, df_last):
                dfs_to_test.append(dfs[i])

    # run tests
    # c_df = gpd.read_file(f'{input_path}/{state}/2010_counties.shp')
    # b_df = gpd.read_file(f'{input_path}/{state}/2010_blocks.shp')
    for plan_name, d_df in dfs_to_test:
      #  _, pops = county_district_intersection_pops(c_df, d_df, b_df)
        
        # write to file
        if not os.path.isdir(output_path):
            os.mkdir(output_path)
        if not os.path.isdir(f'{output_path}/{state}'):
            os.mkdir(f'{output_path}/{state}')
            
        pops = {}
        pops[1] = 2
        pops[3] = 4
        pops_file = f'{output_path}/{state}/{plan_name[:-4]}.json'
        dict_to_json(pops, pops_file)
except:
    failed.append(f'{state} {plan_name}')
    
# write failed file if needed
if len(failed) > 0:
    with open(f'{output_path}/{state}/failed.txt', 'w') as f:
        for item in failed:
            f.write('%s\n' % item)

    

    
