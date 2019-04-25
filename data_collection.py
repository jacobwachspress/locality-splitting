# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 22:05:47 2019

@author: Jacob
"""
import urllib.request
import zipfile
import os
from os.path import basename
import shutil
import geopandas as gpd
from geoprocessing import counties_from_blocks
import tempfile

def read_in_shapefiles_state_by_state(output_path, urls, name):
    ''' Downloads state shapefiles to desired location
    
    Arguments: 
        output_path: folder to write shapefiles. By convention, ENDS IN '/'.
            (example: 'C:/Users/Jacob/Desktop/JP/2010/')
        urls: dictionarys where keys are two-digit abbreviations for states 
            and values are urls of zipped shapefiles
        name: for saving the file
        
    Note: we are hard-coding in the URLs from the census
        
    Output:
        GeoDataFrame corresponding to the shapefile in the zip folder 
    '''
    failed = []
    for state in urls:
        try:
            # read in file
            file = urls[state]	
            
            # get GeoDataFrame from file
            geo_df = zipped_shapefile_to_geo_df(file)
            
            # write census block shapefile
            if not os.path.isdir(output_path + state):
                os.mkdir(output_path + state)
            geo_df.to_file(output_path + state + '/' + name + '.shp')
        except Exception as e:
            print(e)
            failed.append(state)
    print (name)
    print (failed)

    
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
        try:
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
        except:
            print ('Failed: ' + str(state))

#%% 
def zip_shapefile(filepath):
    ''' Replaces shapefile (and all components) with .zip file
    
    Arguments:
        filepath: everything before .shp, such as:
            'C:/Users/Jacob/Documents/GitHub/county-splits/Data/AL/2010_blocks'
        '''
            
    extensions = ['.cpg', '.dbf', '.prj', '.shp', '.shx']         
    files_to_zip = [filepath + ext for ext in extensions]
    with zipfile.ZipFile(filepath + '.zip','w') as zip: 
        # writing each file one by one 
        for file in files_to_zip: 
            zip.write(file, basename(file))
        for file in files_to_zip: 
            os.remove(file)

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
    urllib.request.urlcleanup()

    # unzip
    zip_ref = zipfile.ZipFile(file_loc, 'r')
    zip_ref.extractall(output_path)
    zip_ref.close()
    
    for file in os.listdir(output_path):
        if file[-4:] == '.cpg':
            os.remove(output_path + '\\' + file)
    
    # get geo_df from shapefile
    shapefiles = [file for file in os.listdir(output_path) if \
                  file[-4:] == '.shp']
    print (shapefiles)
    if (len(shapefiles) != 1):
        shutil.rmtree(output_path)
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
#%%
