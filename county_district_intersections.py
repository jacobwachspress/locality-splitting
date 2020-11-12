"""Intersections between districts and counties.

Get which districts intersect with which counties.

This will speed up the block level interpolation because we can reduce
to counties that intersect with each district rather than interpolating on
the entire state.
"""
import geopandas as gpd
import os
from pull_census_data import state_fips
from county_district_interpolation import district_attribute
from county_district_interpolation import get_district_year


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
            print('INTERSECTIONS', file, '\n')
            # Load the district file
            district_path = base_path + file
            df_dist = gpd.read_file(district_path)

            # Define relevant column names and add to keep columns
            district_year = get_district_year(file)
            dist_col = district_attribute(district_year)
            keep_cols.append(district_year)

            # Detect intersections
            df = county_district_intersections(df, district_year, df_dist,
                                               dist_col)

        # Save dataframe
        df = df[keep_cols]
        df.to_csv(base_path + state + '_district_county_intersection.csv',
                  index=False)

    return


def county_district_intersections(df_county, county_col, df_district,
                                  district_col):
    """Determine which districts intersect with each county.

    Arguments:
        df_county: county shapefile

        county_col: name to save district information
            we'll be saving a comma delimited string

        df_district: district shapefile

        district_col: name of fips columnin district shapefile
    """
    # Let the index by an integer for spatial indexing purposes
    df_district.index = df_district.index.astype(int)

    # construct r-tree spatial index
    si = df_district.sindex

    # Get centroid for each geometry in the large shapefile
    df_district['centroid'] = df_district['geometry'].centroid

    # Find appropriate matching large geometry for each small geometry
    df_county = df_county.reset_index(drop=True)
    for ix, row in df_county.iterrows():
        try:
            # Get potential matches
            county_poly = row['geometry']
            potential_matches = [df_district.index[i] for i in
                                 list(si.intersection(county_poly.bounds))]

            # Only keep matches that have intersections
            matches = [m for m in potential_matches
                       if df_district.at[m, 'geometry'].intersection(
                       county_poly).area > 0]

            # Get matches values
            matches_values = df_district.loc[matches, district_col]
            matches_str = ','.join(list(matches_values))

            # Save matches
            df_county.at[ix, county_col] = matches_str

        except:
            continue

    return df_county


if __name__ == "__main__":
    main()
