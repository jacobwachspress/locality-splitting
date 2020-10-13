"""Interpolate District Boundaries onto Block Data."""
import pandas as pd
import geopandas as gpd
import os
from pull_census_data import state_fips
from county_district_interpolation import district_attribute
from county_district_interpolation import distribute_label
from county_district_interpolation import get_district_year


def main():
    """Interpolate district boundaries on census block data."""
    fips = state_fips()

    # Iterate over each state
    for state, fips_code in fips.items():
        if state != 'WY':
            continue
        # Get the base bath to the state folder
        base_path = 'clean_data/' + state + '/'

        # Load state census block shapefile
        blocks_path = base_path + state + '_blocks.shp'
        df = gpd.read_file(blocks_path)

        # Load district and county containment dataframes
        county_path = base_path + state + '_district_contains_county.csv'
        df_county = pd.read_csv(county_path)
        district_path = base_path + state + '_district_contains_district.csv'
        df_district = pd.read_csv(district_path)

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

        # Join most updated classifications
        class_path = base_path + state + '_classifications.csv'
        if os.path.isfile(class_path):
            df_class = pd.read_csv(class_path)
            df_class['GEOID10'] = df_class['GEOID10'].astype(str)
            df = df.merge(df_class, on='GEOID10')

        # Iterate through each redistricting plan
        for file_ix, file in enumerate(files):
            print(file)
            # Get the district level and year
            district_year = get_district_year(file)

            # If redistricting plan has already been classified in the block
            # file we can continue
            if district_year in df.columns:
                continue

            # Reduce county contains dataframe and join
            df_county_plan = reduce_county_contains(df_county, district_year)
            df = df.merge(df_county_plan, on='COUNTYFP10', how='left')

            df.to_file('wy_test_county.shp')
            print('County Finished')
            # # Iterate through files before this file. This will tell us which
            # # districts of already classified plans are subsets of districts
            # # of the current plan
            # for prev_file in files[:file_ix]:
            #     print(prev_file)
            #     # Get the previous file district year
            #     prev_district_year = get_district_year(prev_file)
            #
            #     # Continue if previous district year is not in dataframe
            #     if prev_district_year not in df.columns:
            #         continue
            #
            #     # Get dataframe to join previous district years to
            #     d = df_district[df_district['base'] == prev_district_year]
            #     d = d[['base_value', district_year]]
            #     d[prev_district_year] = d['base_value']
            #     d[district_year + '_contain'] = d[district_year]
            #     d = d.drop(columns=['base_value', district_year])
            #
            #     # Merge, fillna, and drop contain value
            #     df = df.merge(df, on=prev_district_year, how='left')
            #     fill = district_year + '_contain'
            #     df[district_year] = df[district_year].fillna(df[fill])
            #     df = df.drop(fill, axis=1)
            #
            # print('Previous Files')
            #
            # # Split blocks into classified and unclassified
            # df_classified = df[df[district_year].notna()]
            # df_unclassified = df[df[district_year].isna()]
            #
            # # Show progress and load redistricting plan
            # print('INTERPOLATING', file, len(df_classified),
            #       len(df_unclassified), '\n')
            # df_plan = gpd.read_file(base_path + file)
            #
            # # Distribute label to unclassified blocks
            # dist_col = district_attribute(district_year)
            # df_unclassified = distribute_label(df_plan, [dist_col],
            #                                    df_unclassified,
            #                                    [district_year], progress=1000)
            #
            # # Save classifications and district only
            # district_cols = set(district_years).intersection(set(df.columns))
            # district_cols = list(district_cols)
            # df = df[['GEOID10'] + district_cols]
            # df.to_csv(base_path + state + '_classifications.csv', index=False)
            # df.to_csv(base_path + state + '_' + district_year +
            #           '_classifications.csv', index=False)
            # df.to_csv(base_path + state + '_classifications_' + district_year +
            #           '.csv', index=False)

            break

        break
    return


def reduce_county_contains(df, district_year):
    """Reduce county contains to a single district year.

    Reduce to the district year, zfill the fips code, and rename fips column
    to match 2010 blocks
    """
    df['COUNTYFP10'] = df['COUNTYFP']
    df['COUNTYFP10'] = df['COUNTYFP10'].astype(str).str.zfill(3)
    df = df[['COUNTYFP10', district_year]]
    return df



if __name__ == "__main__":
    main()