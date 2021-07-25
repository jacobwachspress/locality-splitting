"""Calculate various locality splitting metrics."""
import pandas as pd
import numpy as np
from fips_lookup import state_fips
from functools import reduce


def main():
    """Calculate the different metrics for the counties

    Below are the names of the metrics. See docstrings below for more
    in-depth descriptions

        splits_all: localities_split using all blocks
        splits_pop: localities_split using blocks with non-zero population
        intersections_all: locality_intersections using all blocks
        intersections_pop: locality_intersections using blocks with non-zero pop
        split_pairs: see function
        largest_intersection: see function
        min_entropy: see function
        sqrt_entropy: see function
        effective_splits: see function

    Return dataframe for each metric."""
    fips = state_fips()

    # Initialize splits dataframe
    df_splits = pd.DataFrame()

    # Iterate over each state
    for state, fips_code in fips.items():

        # Get relevant path
        direc = 'clean_data/' + state + '/'
        class_path = direc + state + '_classifications.csv'

        # Load classifications and get counties from geoids
        df = pd.read_csv(class_path)
        df['GEOID10'] = df['GEOID10'].astype(str).str.zfill(15)
        df['county'] = df['GEOID10'].apply(lambda x: x[2:5])

        # Iterate through redistricting plans. Redistricting plans have
        # underscore in name due to our naming convention
        plans = [x for x in df.columns if '_' in x]
        for plan in plans:
            metrics = calculate_all_metrics(df, plan, state=state, lclty_str='county')
            df_splits = df_splits.append(metrics, ignore_index=True)

    # Sort
    df_splits = df_splits.sort_values(by=['state', 'plan'])

    # reorder columns and save splits
    cols = ['state', 'plan'] + sorted([i for i in df_splits.columns if i not in ['state', 'plan']])
    df_splits[cols].to_csv('splits_metrics.csv', index=False)

    return

def calculate_all_metrics(df, plan, state=None, lclty_str='COUNTYFP10'):
    """Calculate all metrics and return in a dictionary."""
    # Initialize dictionary with state and plan names
    d = {}

    if state is not None:
        d['state'] = state
    d['plan'] = plan

    # Calculate total number of localities split
    d['splits_all'] = localities_split(df, plan, lclty_str, populated=False)
    d['splits_pop'] = localities_split(df, plan, lclty_str)

    # Calcualte total number of locality district intersections
    d['intersections_all'] = locality_intersections(df, plan, lclty_str,
                                                    populated=False)
    d['intersections_pop'] = locality_intersections(df, plan, lclty_str)

    # calculate population-based metrics
    d['split_pairs'] = split_pairs(df, plan, lclty_str)
    d['conditional_entropy'] = conditional_entropy(df, plan, lclty_str)
    d['sqrt_entropy'] = sqrt_entropy(df, plan, lclty_str)
    d['effective_splits'] = effective_splits(df, plan, lclty_str)

    # calculate population-based metrics, symmetric version
    d['split_pairs_sym'] = split_pairs(df, plan, lclty_str, symmetric=True)
    d['conditional_entropy_sym'] = conditional_entropy(df, plan, lclty_str, symmetric=True)
    d['sqrt_entropy_sym'] = sqrt_entropy(df, plan, lclty_str, symmetric=True)
    d['effective_splits_sym'] = effective_splits(df, plan, lclty_str, symmetric=True)

    return d


def localities_split(df, plan, lclty_str='COUNTYFP10', populated=True):
    """Calculate how many counties are split in a redistricting plan.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and locality for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        populated: whether to remove census blocks with zero population

        lclty_str: name of locality attribute in the dataframe

    Output:
        numeric of how many counties are split
    """
    # Remove blocks without population
    if populated:
        df = df[df['pop'] > 0]

    # Drop duplicates between locality and plan
    df = df[[lclty_str, plan]].drop_duplicates()

    # Aggregate number of locality intersections
    df = df.groupby(lclty_str).count()

    # Get the number of counties that belong to more than one district
    return len(df[df[plan] > 1])


def locality_intersections(df, plan, lclty_str, populated=True):
    """Calculate the total number of locality district splits.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and locality for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        populated: whether to remove census blocks with zero population

        lclty_str: name of locality attribute in the dataframe

    Output:
        numeric of how many locality district splits exist
    """
    df = df.copy()

    # Remove blocks without population
    if populated:
        df = df[df['pop'] > 0]

    # Drop duplicates between locality and plan
    df = df[[lclty_str, plan]].drop_duplicates()

    # Aggregate number of locality intersections
    df = df.groupby(lclty_str).count()

    # Return how many intersections
    return df[plan].sum() - len(df)


def split_pairs(df, plan, lclty_str, symmetric=False):
    """Calculate split pairs metric.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and locality for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        lclty_str: name of locality attribute in the dataframe

    Output:
        (number between 0 and 1): the probability that
        two randomly chosen people from the same locality are not
        in the same district.
    """

    if symmetric:

        # calculate metric, swap locality and district, calculate again, sum
        return split_pairs(df, plan, lclty_str, symmetric=False) + \
               split_pairs(df, lclty_str, plan, symmetric=False)

    else:
        # Get amount of population by locality district intersection
        df_inter = df.groupby([lclty_str, plan])[['pop']].sum()
        df_inter = df_inter.reset_index()

        # Get the population per locality
        df_locality = df.groupby([lclty_str])[['pop']].sum()
        df_locality = df_locality.reset_index()

        # Get number of connections between people with the same locality & district
        df_inter['connections'] = df_inter['pop'] * (df_inter['pop'] - 1) / 2
        inter_connections = df_inter['connections'].sum()

        # Get the number of connections between people with the same locality
        df_locality['connections'] = df_locality['pop'] * (df_locality['pop'] - 1) / 2
        locality_connections = df_locality['connections'].sum()

        # Get the split pairs metric
        return (locality_connections - inter_connections) / locality_connections


def effective_splits(df, plan, lclty_str, symmetric=False):
    """Calculate effective splits metric used by Wang et. al. in COI paper.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and locality for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        lclty_str: name of locality attribute in the dataframe

    Output:
        positive real number corresponding to effective splits metric
        (higher is more splitting)
    """

    if symmetric:

        # calculate metric, swap locality and district, calculate again, sum
        return effective_splits(df, plan, lclty_str, symmetric=False) + \
               effective_splits(df, lclty_str, plan, symmetric=False)

    else:

        # Get the population by locality district intersection
        df_inter = df.groupby([lclty_str, plan])[['pop']].sum()
        df_inter = df_inter.reset_index()

        # Get the population per locality
        df_locality = df.groupby([lclty_str])[['pop']].sum()
        df_locality = df_locality.reset_index()

        # rename locality population and merge
        df_locality.columns = [lclty_str, 'lclty_pop']
        df_merged = df_inter.merge(df_locality)
        df_merged['prop'] = (df_merged['pop'] / df_merged['lclty_pop'])

        # get effective splits of each locality
        df2 = df_merged.groupby(lclty_str).agg({'prop': locality_effective_splits})
        df2 = df2.reset_index().rename(columns={'prop': 'eff_splits'})
        df_locality = pd.merge(df_locality, df2, on=lclty_str)

        # return total effective splits, not population-weighted
        return df_locality['eff_splits'].sum()

def conditional_entropy(df, plan, lclty_str, symmetric=False):
    """Calculate new minimum entropy metric.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and locality for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        lclty_str: name of locality attribute in the dataframe

    Output:
        (number between 0 and 1): entropy such that similar partitions yield
        a higher number.
    """

    if symmetric:

        # calculate metric, swap locality and district, calculate again, sum
        return conditional_entropy(df, plan, lclty_str, symmetric=False) + \
               conditional_entropy(df, lclty_str, plan, symmetric=False)

    else:

        # Get the population by locality district intersection
        df_inter = df.groupby([lclty_str, plan])[['pop']].sum()
        df_inter = df_inter.reset_index()
        df_inter = df_inter[df_inter['pop'] > 0]

        # Get the population per locality
        df_locality = df.groupby([lclty_str])[['pop']].sum()
        df_locality = df_locality.reset_index()

        # rename locality population and merge
        df_locality.columns = [lclty_str, 'lclty_pop']
        df = df_inter.merge(df_locality)

        # Calculate the district entropy
        df['district_entropy'] = df['pop'] * np.log2(df['pop'] / df['lclty_pop'])

        # calculate entropy
        entropy = -1 * df['district_entropy'].sum() / df['pop'].sum()

        return entropy


def sqrt_entropy(df, plan, lclty_str, symmetric=False):
    """Calculate sqrt(entropy) metric used by Duchin in PA report.

    Arguments:
        df: dataframe containing classifications and populations for the
            redistricting plan and locality for every census block

        plan: string that is the name of the redistricting plan
              e.g. 'sldl_2010'

        lclty_str: name of locality attribute in the dataframe

    Output:
        positive real number corresponding to sqrt(entropy) metric
        (higher is more splitting)
    """

    if symmetric:

        # calculate metric, swap locality and district, calculate again, sum
        return sqrt_entropy(df, plan, lclty_str, symmetric=False) + \
               sqrt_entropy(df, lclty_str, plan, symmetric=False)

    else:

        # Get the population by locality district intersection
        df_inter = df.groupby([lclty_str, plan])[['pop']].sum()
        df_inter = df_inter.reset_index()

        # Get the population per locality
        df_locality = df.groupby([lclty_str])[['pop']].sum()
        df_locality = df_locality.reset_index()

        # Rename population columns and merge
        df_locality.columns = [lclty_str, 'lclty_pop']
        df_merged = df_inter.merge(df_locality)

        # Calculate sqrtEntropy
        square_root_entropy = np.sqrt(df_merged['lclty_pop'] * df_merged['pop']).sum()
        square_root_entropy = square_root_entropy / df_merged['pop'].sum()

        return square_root_entropy


def locality_effective_splits(series):
    """ Helper function for effective_splits"""
    return 1 / reduce(lambda x, y: x ** 2 + y ** 2, series) - 1





if __name__ == "__main__":
    main()
