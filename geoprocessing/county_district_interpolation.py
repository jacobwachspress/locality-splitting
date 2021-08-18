"""Interpolate District Boundaries onto County Boundaries.

Creating a dataframe that matches county fips to districts only if
the county is fully contained by the district.

This will assist in the block level interpolation because we can assign
any blocks within the county to the district minimizing the amount of
geographic matching required.
"""
import pandas as pd
import geopandas as gpd
import os
from download_census_data import state_fips


def main():
    """Interpolate district boundaries on census block data."""
    fips = state_fips()

    # Iterate over each state
    for state, fips_code in fips.items():
        # Get the base bath to the state folder
        base_path = 'clean_data/' + state + '/'

        # Get county and redistricting plan shapefiles
        files = os.listdir(base_path)
        files = [x for x in files if x[-4:] == '.shp']
        files = [x for x in files if 'blocks' not in x]
        counties = [x for x in files if 'county' in x]
        districts = [x for x in files if 'county' not in x]

        # Load most recent county file
        counties.sort()
        df = gpd.read_file(base_path + counties[-1])

        # Add systematic countyfp
        if 'COUNTYFP00' in df.columns:
            df['COUNTYFP'] = df['COUNTYFP00']
        if 'COUNTYFP10' in df.columns:
            df['COUNTYFP'] = df['COUNTYFP10']

        # Iterate through each files
        keep_cols = ['COUNTYFP']
        for file in districts:
            print('INTERPOLATING', file, '\n')
            # Load the district file
            district_path = base_path + file
            df_dist = gpd.read_file(district_path)

            # Define relevant column names and add to keep columns
            district_year = get_district_year(file)
            dist_col = district_attribute(district_year)
            keep_cols.append(district_year)

            # Distribute label
            df = distribute_label(df_dist, [dist_col], df, [district_year])

            # Check if county is full contained, otherwise set to None
            for ix, row in df.iterrows():
                # Get district and county geometry
                district = df_dist.loc[df_dist[dist_col] == row[district_year],
                                       'geometry'].iloc[0]
                county = row['geometry']

                # If district does not fully contain a county then set it
                # equal to null
                intersection_area = district.intersection(county).area
                area_ratio = intersection_area / county.area
                if area_ratio < 0.999:
                    df.at[ix, district_year] = None

        # Save dataframe
        df = df[keep_cols]
        df.to_csv(base_path + state + '_district_contains_county.csv',
                  index=False)

    return


def get_district_year(file):
    """Reduce filename to string with district level underscore year.

    Used for column naming conventions
    """
    district_year = file.split('.')[0]
    district_year = district_year.split('_')[1:]
    district_year = '_'.join(district_year)
    return district_year


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


def distribute_label(df_large, large_cols, df_small, small_cols=False,
                     small_path=False, progress=False, debug_col=False):
    '''Take labels from a shapefile that has larger boundaries and interpolate
    said labels to shapefile with smaller boundaries. By smaller boundaries we
    just mean more fine geographic boundaries. (i.e. census blocks are smaller
    than counties)

    We use the greatest area method. However, when no intersection occurs, we
    simply use the nearest centroid.

    NOTE: By default interpolates a string type because it is a label

    Arguments:

        df_large:
            larger shapefile giving the labels

        large_cols:
            LIST of attributes from larger shp to interpolate to
            smaller shp

        df_small:
            smaller shapefile receiving the labels

        small_cols:
            LIST of names for attributes given by larger columns.
            Default will be False, which means to use the same attribute names

        small_path:
            path to save the new dataframe to

        progress:
            how often to print

        debug_col:
            column in df_small to print out when error occurs.
            usually block_id or geoid

    Output:
        edited df_small dataframe
    '''

    # handle default for small_cols
    if small_cols is False:
        small_cols = large_cols

    # Check that large and small cols have same number of attributes
    if len(small_cols) != len(large_cols):
        return False

    if not set(large_cols).issubset(set(df_large.columns)):
        return False

    # Let the index by an integer for spatial indexing purposes
    df_large.index = df_large.index.astype(int)

    # Drop small_cols in small shp if they already exists
    drop_cols = set(small_cols).intersection(set(df_small.columns))
    df_small = df_small.drop(columns=drop_cols)

    # Initialize new series in small shp
    for col in small_cols:
        df_small[col] = pd.Series(dtype=object)

    # construct r-tree spatial index
    si = df_large.sindex

    # Get centroid for each geometry in the large shapefile
    df_large['centroid'] = df_large['geometry'].centroid

    # Find appropriate matching large geometry for each small geometry
    df_small = df_small.reset_index(drop=True)
    for ix, row in df_small.iterrows():
        try:
            if progress:
                if (ix + 1) % progress == 0:
                    print('\t' + str(ix + 1) + '/' + str(len(df_small)))
            # Get potential matches
            small_poly = row['geometry']
            potential_matches = [df_large.index[i] for i in
                                 list(si.intersection(small_poly.bounds))]

            # Only keep matches that have intersections
            matches = [m for m in potential_matches
                       if df_large.at[m, 'geometry'].intersection(
                       small_poly).area > 0]

            # No intersections. Find nearest centroid
            if len(matches) == 0:
                small_centroid = small_poly.centroid
                dist_series = df_large['centroid'].apply(lambda x:
                                small_centroid.distance(x))
                large_ix = dist_series.idxmin()

            # One intersection. Only one match
            elif len(matches) == 1:
                large_ix = matches[0]

            # Multiple intersections. compare fractional area
            # of intersection
            else:
                area_df = df_large.loc[matches, :]
                area_series = area_df['geometry'].apply(lambda x:
                                x.intersection(small_poly).area
                                / small_poly.area)
                large_ix = area_series.idxmax()

            # Update values for the small geometry
            for j, col in enumerate(large_cols):
                df_small.at[ix, small_cols[j]] = df_large.at[large_ix, col]
        except:
            continue

    return df_small


if __name__ == "__main__":
    main()
