"""Calculate various county splits metrics."""
import geopandas as gpd
import pandas as pd
import numpy as np
from download_census_data import state_fips


def main():
    """Calculate the seven different metrics

    Below are the names of the seven metrics. See docstrings below for more
    in-depth descriptions

        splits_all: counties_split using all blocks
        splits_pop: counties_split using blocks with non-zero population
        intersections_all: county_intersections using all blocks
        intersections_pop: county_intersections using blocks with non-zero pop
        preserved_pairs: see function
        largest_intersection: see function
        min_entropy: see function

    Return dataframe for each metric."""
    fips = state_fips()

    # Initialize splits dataframe
    df_splits = pd.DataFrame()

    # Iterate over each state
    for state, fips_code in fips.items():
        # Show progress by state
        print(state)

        # Get relevant paths
        direc = 'clean_data/' + state + '/'
        class_path = direc + state + '_classifications.csv'
        geo_path = direc + state + '_blocks.shp'

        # Load classifications and block geographies
        df = gpd.read_file(geo_path)
        df_class = pd.read_csv(class_path)
        df_class['GEOID10'] = df_class['GEOID10'].astype(str).str.zfill(15)
        df_class = df_class.drop('pop', axis=1)
        df = df.merge(df_class, on='GEOID10')

        # Iterate through redistricting plans. Redistricting plans have
        # underscore in name due to our naming convention
        plans = [x for x in df.columns if '_' in x]
        for plan in plans:
            metrics = calculate_all_metrics(df, state, plan)
            df_splits = df_splits.append(metrics, ignore_index=True)

    # Sort
    df_splits = df_splits.sort_values(by=['state', 'plan'])

    # Save splits
    df_splits.to_csv('splits_metrics.csv', index=False)

    return


def calculate_all_metrics(df, state, plan, cnty_str='COUNTYFP10'):
    """Calculate all seven metrics and return in a dictionary."""
    # Initialize dictionary with state and plan names
    d = {}
    d['state'] = state
    d['plan'] = plan

    # Calculate total number of counties split
    d['splits_all'] = counties_split(df, plan, cnty_str, populated=False)
    d['splits_pop'] = counties_split(df, plan, cnty_str)

    # Calcualte total number of county district intersections
    d['intersections_all'] = county_intersections(df, plan, cnty_str,
                                                  populated=False)
    d['intersections_pop'] = county_intersections(df, plan, cnty_str)

    # Calculate three new metrics
    d['preserved_pairs'] = preserved_pairs(df, plan, cnty_str)
    d['largest_intersection'] = largest_intersection(df, plan, cnty_str)
    d['min_entropy'] = minimum_entropy(df, plan, cnty_str)

    return d


def counties_split(df, plan, cnty_str='COUNTYFP10', populated=True):
    """Calculate how many counties are split in a redistricting plan.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and county for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        populated: whether to remove census blocks with zero population

        cnty_str: name of county attribute in the dataframe

    Output:
        numeric of how many counties are split
    """
    # Remove blocks without population
    if populated:
        df = df[df['pop'] > 0]

    # Drop duplicates between county and plan
    df = df[[cnty_str, plan]].drop_duplicates()

    # Aggregate number of county intersections
    df = df.groupby(cnty_str).count()

    # Get the number of counties that belong to more than one district
    return len(df[df[plan] > 1])


def county_intersections(df, plan, cnty_str, populated=True):
    """Calculate the total number of county district splits.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and county for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        populated: whether to remove census blocks with zero population

        cnty_str: name of county attribute in the dataframe

    Output:
        numeric of how many county district splits exist
    """
    df = df.copy()

    # Remove blocks without population
    if populated:
        df = df[df['pop'] > 0]

    # Drop duplicates between county and plan
    df = df[[cnty_str, plan]].drop_duplicates()

    # Aggregate number of county intersections
    df = df.groupby(cnty_str).count()

    # Return how many intersections
    return df[plan].sum() - len(df)


def preserved_pairs(df, plan, cnty_str):
    """Calculate new preserved pairs metric.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and county for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        cnty_str: name of county attribute in the dataframe

    Output:
        (number between 0 and 1): the probability that
        two randomly chosen people from the same county are also
        in the same district.
    """
    # Get amount of population by county district intersection
    df_inter = df.groupby([cnty_str, plan])[['pop']].sum()
    df_inter = df_inter.reset_index()

    # Get the population per county
    df_county = df.groupby([cnty_str])[['pop']].sum()
    df_county = df_county.reset_index()

    # Get number of connections between people with the same county & district
    df_inter['connections'] = df_inter['pop'] * (df_inter['pop'] - 1) / 2
    inter_connections = df_inter['connections'].sum()

    # Get the number of connections between people with the same county
    df_county['connections'] = df_county['pop'] * (df_county['pop'] - 1) / 2
    county_connections = df_county['connections'].sum()

    # Get the preserved pairs metric
    return inter_connections / county_connections


def largest_intersection(df, plan, cnty_str):
    """Calculate new largest intersection metric.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and county for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        cnty_str: name of county attribute in the dataframe

    Output:
        (number between 0 and 1): the fraction of voters
        who are in the congressional district that has the largest number of
        their county's voters.  Alternatively, if everyone assumed that
        their congressional district was the one with the largest number
        of their county's residents, the proportion who would be correct.
    """
    # Get the population by county district intersection
    df_inter = df.groupby([cnty_str, plan])[['pop']].sum()
    df_inter = df_inter.reset_index()

    # Get the intersection with the maximum population
    df_max = df_inter.groupby(cnty_str)[['pop']].max()

    # max population intersection total population
    total_max_population = df_max['pop'].sum()

    # population of entire state
    total_population = df['pop'].sum()

    # return largest intersection metric
    return total_max_population / total_population


def minimum_entropy(df, plan, cnty_str):
    """Calculate new minimum entropy metric.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and county for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        cnty_str: name of county attribute in the dataframe

    Output:
        (number between 0 and 1): entropy such that similar partitions yield
        a higher number.
    """
    # Get the population by county district intersection
    df_inter = df.groupby([cnty_str, plan])[['pop']].sum()
    df_inter = df_inter.reset_index()
    df_inter = df_inter[df_inter['pop'] > 0]

    # Get the population per county
    df_county = df.groupby([cnty_str])[['pop']].sum()
    df_county = df_county.reset_index()

    # rename county population and merge
    df_county.columns = [cnty_str, 'county_pop']
    df = df_inter.merge(df_county)

    # Calculate the district entropy
    df['district_entropy'] = df['pop'] * np.log2(df['pop'] / df['county_pop'])

    # calculate entropy
    entropy = -1 * df['district_entropy'].sum() / df['pop'].sum()
    entropy = 1 / (1 + entropy)
    return entropy


if __name__ == "__main__":
    main()
