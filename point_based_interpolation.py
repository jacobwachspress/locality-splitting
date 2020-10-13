"""Labeling Census Blocks by Districts Using Block Lat/Long."""
import pandas as pd
import geopandas as gpd
import os
from shapely.geometry import Point
from pull_census_data import state_fips
from county_district_interpolation import district_attribute
from county_district_interpolation import distribute_label
from county_district_interpolation import get_district_year


def main():
    """Interpolate district boundaries on census block data."""
    fips = state_fips()

    # Iterate over each state
    for state, fips_code in fips.items():
        if state != 'AK':
            continue
        # Get the base bath to the state folder
        base_path = 'clean_data/' + state + '/'

        # Load state census block shapefile
        blocks_path = base_path + state + '_blocks.shp'
        df = gpd.read_file(blocks_path)

        # Load district and county containment dataframes
        county_path = base_path + state + '_district_contains_county.csv'
        df_county = pd.read_csv(county_path)

        # Load in district county intersections
        inter_path = base_path + state + '_district_county_intersection.csv'
        df_inter = pd.read_csv(inter_path)

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

            # Reduce county district intersection plan
            df_inter_plan = reduce_district_county_intersection(df_inter,
                                                                district_year)

            # Split blocks into classified and unclassified
            df_classified = df[df[district_year].notna()]
            df_unclassified = df[df[district_year].isna()]

            # Show progress and load redistricting plan
            print('INTERPOLATING', file, len(df_classified),
                  len(df_unclassified), '\n')
            df_plan = gpd.read_file(base_path + file)
            print(df_plan.head())
            # Distribute label to unclassified blocks
            dist_col = district_attribute(district_year)
            df_unclassified = distribute_label_points(df_plan, dist_col,
                                                      df_unclassified,
                                                      district_year,
                                                      df_inter_plan)

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


def distribute_label_points(df_plan, plan_col, df_blocks, block_col, df_inter):
    """Distribute label into census blocks."""
    # Join intersecting districts
    df_blocks = df_blocks.merge(df_inter, how='left', on='COUNTYFP10')

    print(df_blocks.head())
    # Fill na with all districts
    all_districts = ','.join(df_plan[plan_col].to_list())
    cd = 'check_districts'
    df_blocks[cd] = df_blocks[cd].fillna(all_districts)
    df_blocks[cd] = df_blocks[cd].apply(lambda x: x.split(','))

    # Iterate over each census block
    for ix, row in df_blocks.iterrows():
        print(ix + 1, '/', len(df_blocks))
        # Create point
        c = row['geometry'].centroid

        # Reduce current plan to districts we should be checking
        df_current = df_plan[df_plan[plan_col].isin(row['check_districts'])]

        # Iterate through districts
        for plan_ix, plan_row in df_current.iterrows():
            if plan_row['geometry'].contains(c):
                df_blocks.at[ix, block_col] = plan_row[plan_col]
                break
    return df_blocks


def reduce_county_contains(df, district_year):
    """Reduce county contains to a single district year.

    Reduce to the district year, zfill the fips code, and rename fips column
    to match 2010 blocks
    """
    df['COUNTYFP10'] = df['COUNTYFP']
    df['COUNTYFP10'] = df['COUNTYFP10'].astype(str).str.zfill(3)
    df = df[['COUNTYFP10', district_year]]
    return df


def reduce_district_county_intersection(df, district_year):
    """Reduce county district intersections contains to a single district year.
    """
    df['COUNTYFP10'] = df['COUNTYFP']
    df['COUNTYFP10'] = df['COUNTYFP10'].astype(str).str.zfill(3)
    df['check_districts'] = df[district_year]
    df = df[['COUNTYFP10', 'check_districts']]
    return df



if __name__ == "__main__":
    main()
