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
        # Need to figure out error with connecticut
        if state in ['MD', 'MT']:
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
            try:
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
                print('\nINTERPOLATING', file, len(df_classified),
                      len(df_unclassified))
                df_plan = gpd.read_file(base_path + file)

                # Distribute label to unclassified blocks
                dist_col = district_attribute(district_year)

                #######################################
                # Temporary continue to skip the files that have ZZZ
                if 'ZZZ' in list(df_plan[dist_col].unique()):
                    continue
                if 'ZZ' in list(df_plan[dist_col].unique()):
                    continue

                if 'Z19' in list(df_plan[dist_col].unique()):
                    continue

                #######################################
                df_unclassified = distribute_label_points(df_plan, dist_col,
                                                          df_unclassified,
                                                          district_year,
                                                          df_inter_plan)

                # Combine classified and unclassified
                df_unclassified = df_unclassified.drop('check_districts', axis=1)
                df = df_classified.append(df_unclassified)

                # Split again into classified and unclassified to use distribute
                # label on remaining unclassified
                df_classified = df[df[district_year].notna()]
                df_unclassified = df[df[district_year].isna()]

                if len(df_unclassified) > 0:
                    print('\tRemaining Classifications:', len(df_unclassified))
                    # Distribute label
                    df_unclassified = distribute_label(df_plan, [dist_col],
                                                       df_unclassified,
                                                       [district_year])
                    # Append unclassified
                    df = df_classified.append(df_unclassified)

                # Get equivalency file for this plan
                equiv_path = base_path + state + '_classifications_'
                equiv_path += district_year + '.csv'
                df_equiv = df[['GEOID10', district_year]]
                df_equiv.to_csv(equiv_path, index=False)

                # Save block equivalency file for all plans
                print('\n\nSaving', state)
                state_path = base_path + state + '_classifications.csv'
                district_cols = set(district_years).intersection(set(df.columns))
                df_state = df[['GEOID10', 'pop'] + list(district_cols)]
                df_state.to_csv(state_path, index=False)
            except:
                continue

    return


def distribute_label_points(df_plan, plan_col, df_blocks, block_col, df_inter):
    """Distribute label into census blocks."""
    # Join intersecting districts
    df_blocks = df_blocks.merge(df_inter, how='left', on='COUNTYFP10')

    # Fill na with all districts
    all_districts = ','.join(df_plan[plan_col].to_list())
    cd = 'check_districts'
    df_blocks[cd] = df_blocks[cd].fillna(all_districts)
    df_blocks[cd] = df_blocks[cd].apply(lambda x: x.split(','))

    # Iterate over each census block
    for ix, row in df_blocks.iterrows():
        if (ix + 1) % 1000 == 0:
            print('\t', ix + 1, '/', len(df_blocks))
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
