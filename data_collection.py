# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 22:05:47 2019

@author: Jacob
"""
import urllib.request
import zipfile
import os
import shutil
import geopandas as gpd
from geoprocessing import counties_from_blocks
#%%
# source: http://code.activestate.com/recipes/577775-state-fips-codes-dict/
FIPS = {
    'WA': '53', 'DE': '10', 'WI': '55', 'WV': '54', 'HI': '15',
    'FL': '12', 'WY': '56', 'NJ': '34', 'NM': '35', 'TX': '48',
    'LA': '22', 'NC': '37', 'ND': '38', 'NE': '31', 'TN': '47', 'NY': '36',
    'PA': '42', 'AK': '02', 'NV': '32', 'NH': '33', 'VA': '51', 'CO': '08',
    'CA': '06', 'AL': '01', 'AR': '05', 'VT': '50', 'IL': '17', 'GA': '13',
    'IN': '18', 'IA': '19', 'MA': '25', 'AZ': '04', 'ID': '16', 'CT': '09',
    'ME': '23', 'MD': '24', 'OK': '40', 'OH': '39', 'UT': '49', 'MO': '29',
    'MN': '27', 'MI': '26', 
    'RI': '44', 'KS': '20', 'MT': '30', 'MS': '28',
    'SC': '45', 'KY': '21', 'OR': '41', 'SD': '46'
}
#%%

def read_congressional_district_shapefiles(maps, output_path, \
                                           state_id='STATEFP'):
    ''' Reads congressional district shapefiles and separates them by
    state.
    
    Arguments: 
        maps: dictionary whose keys are the names of the districting plan
            (e.g. 112_congress) and whose values are the full file paths
            where the corresponding shapefile lies
        output_path: folder where state-by-state shapefiles should go
        state_id: column in attribute table that contains FIPS code
            (operates under assumption that this is the same for all maps)
    '''
    for plan in maps:
        
        # read in file to geodataframe
        geo_df = gpd.read_file(maps[plan])
        
        # trim geo_df to actual districts (removing territories, unassigned
        # "districts," and other weird data artifacts)
        geo_df = geo_df.loc[geo_df['FUNCSTAT'] == 'N']
        geo_df =  geo_df.loc[int(geo_df['GEOID']) % 100 <= 53]
        
        # check that this worked
        if (len(geo_df) != 435):
            raise Exception('CD shapefile at ' + plan + ' has ' + \
                            str(len(geo_df)) + ' elements after cleaning')
        
        # get FIPS of all states included in shapefile
        df_FIPS = list(set(geo_df.loc[:, state_id]))
        df_FIPS = [int(i) for i in df_FIPS]
        
        # separate shapefiles by state
        for state in FIPS:
            fips = int(FIPS[state])
            # check if this state is in the shapefile (maybe needed for DC, PR)
            if fips in df_FIPS:
                
                # trim df for appropriate rows
                state_df = geo_df.loc[int(geo_df[state_id]) == fips]
                
                # save file to appropriate location
                directory = output_path + state
                if not os.path.isdir(directory):
                    os.mkdir(directory)
                state_df.to_file(directory + '/' + plan + '.shp')
                
#%%
def download_census_block_files(output_path, states=FIPS, pop_str='POP10',\
                                name='2010_blocks'):
    ''' Downloads state census block files from census and saves shapefiles
    
    Arguments: 
        output_path: folder to write shapefiles. By convention, ENDS IN '/'.
            (example: 'C:/Users/Jacob/Desktop/JP/2010/')
        states: list of two-digit abbreviations for states we want to download
        pop_str: name of population column in dataframe (assumed to be the same
                                                         across all states)
        name: for saving the file
        
    Note: we are hard-coding in the URLs from the census
        
    Output:
        GeoDataFrame corresponding to the shapefile in the zip folder 
    '''
    for state in states:
        # read in file
        file = 'https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/' + \
               'tabblock2010_' + FIPS[state] + '_pophu.zip'	
        
        # get GeoDataFrame from file
        geo_df = zipped_shapefile_to_geo_df(file)
        
        # delete census blocks with no population
        geo_df = geo_df.loc[geo_df[pop_str] > 0]
        
        # write census block shapefile
        if not os.path.isdir(output_path + state):
            os.mkdir(output_path + state)
        geo_df.to_file(output_path + state + '/' + name + '.shp')

#%%      
def zipped_shapefile_to_geo_df(file_URL):
    ''' Downloads zipped shapefile and turns it into a GeoDataFrame
    
    Arguments: 
        file_URL: url of zipped shapefile
        
    Output:
        GeoDataFrame corresponding to the shapefile in the zip folder 
        (assumption is that there is just one .shp file)
    '''
    # set temporary directory to download zip file
    tempfile.TemporaryDirectory()
    output_path = tempfile.gettempdir() + '\\temp'
    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    # read in file
    file_loc = output_path + '\\temp.zip'
    urllib.request.urlretrieve(file_URL, file_loc)

    # unzip
    zip_ref = zipfile.ZipFile(file_loc, 'r')
    zip_ref.extractall(output_path)
    zip_ref.close()
    
    # get geo_df from shapefile
    shapefiles = [file for file in os.listdir(output_path) if \
                  file[-4:] == '.shp']
    if (len(shapefiles) != 1):
        raise Exception("Not exactly one shapefile in zip folder. See  " + \
                        str(output_path))
    shp = shapefiles[0]
    geo_df = gpd.read_file(output_path + '\\' + shp)
    
    # remove temporary folder
    shutil.rmtree(output_path)
    
    return geo_df
#%%

def separate_national_shp_into_states(geo_df, state_id, output_path, name):
    ''' Separates national shapefile into files by state
    
    Arguments: 
        geo_df: geopandas dataframe from national shapefile
        state_id: column name for states in geo_df
        output_path: path to directory for state output folder
        name: name the output shapefile (example: 2010_counties)
    '''  
    for st in FIPS:
        out_df = geo_df.loc[geo_df[str(state_id)] == FIPS[st]]
        
        if not os.path.isdir(output_path + st):
            os.mkdir(output_path + st)
        out_df.to_file(output_path + st + '/' + name + '.shp')
    