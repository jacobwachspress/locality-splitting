# -*- coding: utf-8 -*-
"""
Created on Mon May  6 11:47:31 2019

@author: Jacob
"""

import matplotlib.pyplot as plt
import numpy as np
from geoprocessing import json_to_dict
from metrics import threshold, counties_split, county_intersections, preserved_pairs, largest_intersection, min_entropy
import os
import pandas as pd
import geopandas as gpd
import seaborn as sns

#%%
FIPS = {
    'WA': '53', 'DE': '10', 'WI': '55', 'WV': '54', 'HI': '15',
    'FL': '12', 'WY': '56', 'NJ': '34', 'NM': '35', 'TX': '48', 'LA': '22', 
    'NC': '37', 'ND': '38', 'NE': '31', 'TN': '47', 'NY': '36', 'PA': '42', 
    'AK': '02', 'NV': '32', 'NH': '33', 'VA': '51', 'CO': '08', 'CA': '06', 
    'AL': '01', 'AR': '05', 'VT': '50', 'IL': '17', 'GA': '13', 'IN': '18', 
    'IA': '19', 'MA': '25', 'AZ': '04', 'ID': '16', 'CT': '09', 'ME': '23', 
    'MD': '24', 'OK': '40', 'OH': '39', 'UT': '49', 'MO': '29', 'MN': '27', 
    'MI': '26', 'RI': '44', 'KS': '20', 'MT': '30', 'MS': '28', 'SC': '45', 
    'KY': '21', 'OR': '41', 'SD': '46'
}

plans = []
for state in FIPS:
    path = f'C:\\Users\\Jacob\\Documents\\GitHub\\county-splits\\Data\\Output\\{state}\\'
    for file in os.listdir(path):
        year = int(file[0:4])
        body = file[5:-5]
        try:
            pops = json_to_dict(path+file)
            num_districts = len(set([key[1] for key in pops]))
            thresh = 0.005 * sum(pops.values()) / num_districts
            thresh = min(thresh, 500)
            pops = threshold(pops, threshold=thresh)
            
            plans.append([state, body, year, pops,\
                          counties_split(pops),\
                          county_intersections(pops),\
                          preserved_pairs(pops),\
                          largest_intersection(pops),\
                          min_entropy(pops)])
        except:
            print(path+file)
plans = np.asarray(plans)
df = pd.DataFrame(plans, columns = ['state', 'body', 'year', 'pops',\
                                    'counties_split',\
                                    'county_intersections',\
                                    'preserved_pairs',\
                                    'largest_intersection',\
                                    'min_entropy'])
#%%

df.to_csv(f'C:\\Users\\Jacob\\Documents\\GitHub\\county-splits\\Data\\Output\\df.csv')
        
        
    
#%%
PA_county_path = 'C:\\Users\\Jacob\\Documents\\GitHub\\county-splits\\Data\\PA\\'
json_path = 'C:\\Users\\Jacob\\Documents\\GitHub\\county-splits\\Data\\Output\\PA\\'
PA_2018_districts = PA_county_path + '2018_congress.shp'
PA_2016_districts = PA_county_path + '2016_congress.shp'
geo_df = gpd.read_file(PA_county_path + '2010_counties.shp')
districts2018 = gpd.read_file(PA_2018_districts) 
districts2016 = gpd.read_file(PA_2016_districts) 
dict2018 = json_to_dict(json_path + '2018_congress.json')
dict2016 = json_to_dict(json_path + '2016_congress.json')

#%%

# get counties
pops = dict2018
counties = set([key[0] for key in pops])
    
intersect_pops = {county: [pops[key] for key in pops if key[0] == county] \
                   for county in counties}

good_pairs = {county: sum([i*(i-1)/2 for i in intersect_pops[county]]) \
              for county in counties }

county_pops = {county: sum([pops[key] for key in pops if key[0] == county]) \
                   for county in counties}

all_pairs = {county: county_pops[county]*(county_pops[county]-1)/2 \
              for county in counties }

proportions = {county: good_pairs[county]/all_pairs[county] \
              for county in counties}

df_to_merge = pd.DataFrame(list(proportions.items()), columns=['COUNTYFP10', 'PROP'])
geo_df2 = geo_df.merge(df_to_merge, on='COUNTYFP10')



#%%
    
fig, ax = plt.subplots()
ax.set_aspect('equal')

geo_df2.plot(ax=ax, column='PROP', cmap='Greens', edgecolor='white', linewidth=1)
districts2018.plot(ax=ax, color=[1,1,1,0], edgecolor='red', linewidth=1)

plt.show();
