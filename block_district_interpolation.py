"""Assisgning redistricting plan districts to each census block."""
import pandas as pd
import geopandas as gpd
import os
import numpy as np
from pull_census_data import state_fips
from county_district_interpolation import district_attribute
from county_district_interpolation import distribute_label
from county_district_interpolation import get_district_year


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

        # Load district contains district an rename columns to note imputation
        district_path = base_path + state + '_district_contains_district.csv'
        df_district = pd.read_csv(district_path)
        district_cols = list(df_district.columns)
        district_cols_base = district_cols[:3]
        district_cols_other = district_cols[3:]
        district_cols_other = [x + '_imputed' for x in district_cols_other]
        df_district.columns = district_cols_base + district_cols_other

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
            df_class['GEOID10'] = df_class['GEOID10'].astype(str).str.zfill(15)
            df_class = df_class.drop('pop', axis=1)
            df = df.merge(df_class, on='GEOID10')

        # Iterate through each redistricting plan
        for file_ix, file in enumerate(files):
            # Get the district level and year
            district_year = get_district_year(file)

            # If redistricting plan has already been classified in the block
            # file we can continue
            if district_year in df.columns:
                if len(df[df[district_year].isna()]) == 0:
                    continue

            # Reduce county contains dataframe and join
            df_county_plan = reduce_county_contains(df_county, district_year)
            df = add_district_contains_counties(df, df_county_plan,
                                                district_year)

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
            if len(df_unclassified) > 0:
                dist_col = district_attribute(district_year)
                df_labeled = distribute_labels_by_subset(df_plan, dist_col,
                                                         df_unclassified,
                                                         district_year,
                                                         df_inter_plan)

                # Combine classified and unclassified
                df_labeled = df_labeled.drop('check_districts', axis=1)
                df = df_classified.append(df_labeled)
            df = df.reset_index(drop=True)

            # Add district contains district
            print('\tDistrict Contains Districts')
            df = add_district_contains_district(df, df_district, district_year)

            # Remove imputed columns
            imputed_cols = list(df.columns)
            imputed_cols = [x for x in imputed_cols if 'imputed' in x]
            df = df.drop(columns=imputed_cols)

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

    return


def standardize_value(x):
    """zfill a value to have three digits and handle type."""
    # If NaN then return none
    if isinstance(x, str):
        return x.zfill(3)
    elif np.isnan(x):
        return None
    elif x is None:
        return x
    elif isinstance(x, float):
        return str(int(x)).zfill(3)
    else:
        return str(x).zfill(3)


def add_district_contains_counties(df, df_county, district_year):
    # Check if district_year is already in dataframe
    if district_year in df.columns:
        # Make df_county column imputed
        imp_col = district_year + '_imputed'
        df_county.columns = ['COUNTYFP10', imp_col]
        df = df.merge(df_county, on='COUNTYFP10', how='left')
        df[district_year] = df[district_year].fillna(df[imp_col])

        # Drop imputed column after imputation
        df = df.drop(imp_col, axis=1)

    else:
        df = df.merge(df_county, how='left')
    return df


def add_district_contains_district(df, df_district, district_year):
    """Add classifications for larger district plans."""
    # Reduce district
    df_plan = df_district[df_district['base'] == district_year]
    df_plan[district_year] = df_plan['base_value']

    # Get list of imputed columns
    imp_cols = [x for x in list(df_plan.columns) if 'imputed' in x]

    # Drop base information
    df_plan = df_plan.drop(columns=['base', 'base_col', 'base_value'])

    # Standardize district names
    df[district_year] = df[district_year].apply(lambda x: standardize_value(x))
    df_plan[district_year] = df_plan[district_year].apply(lambda x:
                                                          standardize_value(x))

    # left join districts to blocks
    df = df.merge(df_plan, how='left', on=district_year)

    # Iterate through each imputed column
    for col in imp_cols:
        # Get name of nonimputed column
        non_imp_col = '_'.join(col.split('_')[:-1])

        # Impute or set equal if column exists
        if non_imp_col in df.columns:
            df[non_imp_col] = df[non_imp_col].fillna(df[col])
        else:
            df[non_imp_col] = df[col]
    return df


def distribute_labels_by_subset(df_plan, plan_col, df_blocks, block_col,
                                df_inter):
    """Distribute label into census blocks."""
    # Join intersecting districts
    df_blocks = df_blocks.merge(df_inter, how='left', on='COUNTYFP10')

    # Fill na with all districts
    all_districts = ','.join(df_plan[plan_col].to_list())
    cd = 'check_districts'
    df_blocks[cd] = df_blocks[cd].fillna(all_districts)

    # Initialize new blocks dataframe
    df_blocks_new = pd.DataFrame()

    # Iterate through each subset of plans
    subsets = set(df_blocks[cd])
    for ix, subset in enumerate(subsets):
        print('\n\tsubset', ix + 1, '/', len(subsets), '- districts', subset)
        # Get subset as a list
        subset_list = subset.split(',')

        # Get subset of redistricting plan an subset of blocks
        df_plan_subset = df_plan[df_plan[plan_col].isin(subset_list)]
        df_blocks_subset = df_blocks[df_blocks[cd] == subset]

        # Distribute label on the subset
        df_subset = distribute_label(df_plan_subset, [plan_col],
                                     df_blocks_subset, [block_col],
                                     progress=1000)

        # Append classified subset
        df_blocks_new = df_blocks_new.append(df_subset)

    return df_blocks_new


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
    # Define check districts
    cd = 'check_districts'

    # Reduce
    df['COUNTYFP10'] = df['COUNTYFP']
    df['COUNTYFP10'] = df['COUNTYFP10'].astype(str).str.zfill(3)
    df[cd] = df[district_year]
    df = df[['COUNTYFP10', cd]]

    # Sort check districts
    df[cd] = df[cd].apply(lambda x: str(x).split(','))
    df[cd].apply(lambda x: x.sort())
    df[cd] = df[cd].apply(lambda x: ','.join(x))

    return df


if __name__ == "__main__":
    main()
