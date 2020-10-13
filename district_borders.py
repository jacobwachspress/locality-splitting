"""Interpolate District Boundaries onto Block Data."""
import pandas as pd
from shapely.geometry import LineString
import geopandas as gpd
import os
from pull_census_data import state_fips
import time
import numpy as np


def main():
    """Interpolate district boundaries on census block data."""
    fips = state_fips()

    # Iterate over each state
    for state, fips_code in fips.items():
        # Get the base bath to the state folder
        base_path = 'clean_data/' + state + '/'

        # Load state census block shapefile
        blocks_path = base_path + state + '_blocks.shp'
        df = gpd.read_file(blocks_path)

        # Get non-county shapefiles
        files = os.listdir(base_path)
        files = [x for x in files if x[-4:] == '.shp']
        files = [x for x in files if 'county' not in x]
        files = [x for x in files if 'blocks' not in x]

        # Iterate through each files
        for file in files:
            print('CALCULATING BORDER', file, '\n')
            # Load the district file
            district_path = base_path + file
            df_dist = gpd.read_file(district_path)

            # Define relevant column names
            district_year = file.split('.')[0]
            district_year = district_year.split('_')[1:]
            district_year = '_'.join(district_year)
            dist_col = district_attribute(district_year)

            # Distribute label
            border_path = base_path + state + '/'
            border_path += district_year + '_border.shp'
            print(border_path)
            df_border = border_blocks(df_dist, df)
            df_border.to_file(border_path)
            break
        break
    return


def border_blocks(df_dist, df):
    """Get census blocks that are on the border of districts."""
    # Iterate through districts
    district_borders = []
    for ix, row in df_dist.iterrows():
        # Get district borders
        district = row['geometry']

        # Handle if multipolygon
        if district.geom_type == 'MultiPolygon':
            for j, part in enumerate(list(district)):
                district_border = list(part.exterior.coords)
                district_borders.append(district_border)
        elif district.geom_type == 'Polygon':
            district_border = list(district.exterior.coords)
            district_borders.append(district_border)

    # Convert into linestring objects
    district_borders = [LineString(x) for x in district_borders]

    # Create geodataframe
    df_lines = pd.DataFrame()
    df_lines['geometry'] = district_borders
    df_lines = gpd.GeoDataFrame(df_lines, geometry='geometry')
    df_lines.crs = {'init': 'epsg:4269'}
    print(df_lines)

    # Just use a spatial join on districts
    start = time.time()
    df_border = gpd.sjoin(df, df_lines, how='inner', op='intersects')
    print(np.round(time.time() - start, 1))
    return df_border


def district_attribute(district_year):
    """Get the name of the district attribute given the shapefile.

    Arguments:
        district_year: name of district boundary and the given year
    """
    # Define dictionary for each attribute name
    d = {}

    # Define congressional districts
    d['cd_2003'] = 'CD108FP'
    d['cd_2010'] = 'CD111FP'
    d['cd_2011'] = 'CD112FP'
    d['cd_2012'] = 'CD112FP'
    d['cd_2013'] = 'CD113FP'
    d['cd_2014'] = 'CD114FP'
    d['cd_2015'] = 'CD114FP'
    d['cd_2016'] = 'CD115FP'
    d['cd_2017'] = 'CD115FP'
    d['cd_2018'] = 'CD116FP'
    d['cd_2019'] = 'CD116FP'

    # Define state legislative upper
    d['sldl_2000'] = 'SLDLST00'
    d['sldl_2010'] = 'SLDLST10'
    d['sldl_2011'] = 'SLDLST'
    d['sldl_2012'] = 'SLDLST'
    d['sldl_2013'] = 'SLDLST'
    d['sldl_2014'] = 'SLDLST'
    d['sldl_2015'] = 'SLDLST'
    d['sldl_2016'] = 'SLDLST'
    d['sldl_2017'] = 'SLDLST'
    d['sldl_2018'] = 'SLDLST'
    d['sldl_2019'] = 'SLDLST'

    # Define state legislative lower
    d['sldu_2000'] = 'SLDUST00'
    d['sldu_2010'] = 'SLDUST10'
    d['sldu_2011'] = 'SLDUST'
    d['sldu_2012'] = 'SLDUST'
    d['sldu_2013'] = 'SLDUST'
    d['sldu_2014'] = 'SLDUST'
    d['sldu_2015'] = 'SLDUST'
    d['sldu_2016'] = 'SLDUST'
    d['sldu_2017'] = 'SLDUST'
    d['sldu_2018'] = 'SLDUST'
    d['sldu_2019'] = 'SLDUST'
    return d[district_year]


if __name__ == "__main__":
    main()
