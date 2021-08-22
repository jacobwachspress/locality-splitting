"""Calculate various locality splitting metrics."""

import numpy as np

def calculate_all_metrics(df, plan_col, state=None, lclty_col='COUNTYFP10', pop_col='pop'):
    """Calculate all metrics and return in a dictionary.

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
        """

    # get populations of each (locality, district) pair
    df = df.groupby([lclty_col, plan_col], as_index=False).agg({pop_col: sum})

    # Initialize dictionary with state and plan names
    d = {}

    if state is not None:
        d['state'] = state
    d['plan'] = plan_col

    # Calculate total number of localities split
    d['splits_all'] = calculate_metric(df, lclty_col, pop_col, localities_split, None,
                                       populated=False)
    d['splits_pop'] = calculate_metric(df, lclty_col, pop_col, localities_split, None)

    # Calculate total number of locality district intersections
    d['intersections_all'] = calculate_metric(df, lclty_col, pop_col, locality_intersections,
                                              None, populated=False)
    d['intersections_pop'] = calculate_metric(df, lclty_col, pop_col, locality_intersections,
                                              None)

    # Calculate population-based metrics
    d['split_pairs'] = calculate_metric(df, lclty_col, pop_col, split_pairs, 1)
    d['conditional_entropy'] = calculate_metric(df, lclty_col, pop_col, conditional_entropy, 1)
    d['sqrt_entropy'] = calculate_metric(df, lclty_col, pop_col, sqrt_entropy, 1)
    d['effective_splits'] = calculate_metric(df, lclty_col, pop_col, effective_splits, 1)

    # Calculate population-based metrics, symmetric version
    split_pairs_score = d['split_pairs']
    split_pairs_reversed = calculate_metric(df, plan_col, pop_col, split_pairs, 1)
    d['split_pairs_sym'] = (split_pairs_score + split_pairs_reversed) / 2
    conditional_entropy_score = d['conditional_entropy']
    conditional_entropy_reversed = calculate_metric(df, plan_col, pop_col, conditional_entropy, 1)
    d['conditional_entropy_sym'] = (conditional_entropy_score + conditional_entropy_reversed) / 2
    sqrt_entropy_score = d['sqrt_entropy']
    sqrt_entropy_reversed = calculate_metric(df, plan_col, pop_col, sqrt_entropy, 1)
    d['sqrt_entropy_sym'] = (sqrt_entropy_score + sqrt_entropy_reversed) / 2
    effective_splits_score = d['effective_splits']
    effective_splits_reversed = calculate_metric(df, plan_col, pop_col, effective_splits, 1)
    d['effective_splits_sym'] = (effective_splits_score + effective_splits_reversed) / 2

    return d


def calculate_metric(df, lclty_col, pop_col, metric_function, agg_exponent, populated=True):
    """Calculates a locality splitting score for a redistricting plan.

    Arguments:
        df: DataFrame containing a row for every (locality, district) pair and populations of each
        lclty_col: name of locality attribute in the DataFrame
        plan_col: string that is the name of the redistricting plan (e.g. 'sldl_2010'), must
            be an attribute in the DataFrame
        pop_col: name of population attribute in the DataFrame
        metric_function: function for the metric of interest, pick from those defined below
        agg_exponent: how to aggregate scores across multiple localities for a state (scores get aggregated
            according to weights proportional to (population ^ agg_exponent). Pass None to just add up the
            scores (slightly different from agg_exponent=0, which takes a mean).
        populated: whether to remove census blocks with zero population

    Output:
        numeric of splitting metric score
    """

    # if restricting to populated intersections, get rid of the zero-population pairs
    if populated:
        df = df[df[pop_col] > 0]

    # calculate the population of each locality and the splitting metric for each locality
    lclty_metrics = df.groupby([lclty_col], as_index=False)
    lclty_metrics = lclty_metrics.agg({pop_col: [sum, metric_function]})

    # grab the columns for the metric and the locality population
    metric_col = lclty_metrics.columns[-1]
    lclty_pop_col = lclty_metrics.columns[-2]

    # if we are aggregating the scores in some population-weighted way
    if agg_exponent is not None:

        # prepare the population weights for the scores of each locality
        lclty_metrics[lclty_pop_col] = lclty_metrics[lclty_pop_col] / lclty_metrics[lclty_pop_col].sum()
        lclty_metrics[lclty_pop_col] = lclty_metrics[lclty_pop_col] ** agg_exponent
        lclty_metrics[lclty_pop_col] = lclty_metrics[lclty_pop_col] / lclty_metrics[lclty_pop_col].sum()

        # get a weighted score across all localities
        score = (lclty_metrics[lclty_pop_col] * lclty_metrics[metric_col]).sum()

    # otherwise just add up the scores
    else:
        score = lclty_metrics[metric_col].sum()

    return score


def localities_split(pops):
    """Calculates localities split score for a single locality
    from a pandas Series or numpy array of the populations of
    all (locality, district) intersections."""

    # return 1 if there are at least 2 parts of partition, else 0
    return int(len(pops) > 1)


def locality_intersections(pops):
    """Calculates locality intersections score for a single locality from a pandas Series or numpy array of the
    populations of all (locality, district) intersections."""

    # return number of parts of partition
    return len(pops)


def split_pairs(pops):
    """Calculates split pairs score for a single locality from a pandas Series or numpy array of the
    populations of all (locality, district) intersections."""

    # find total number of pairs of voters
    all_pairs = pops.sum() * (pops.sum() - 1) / 2

    # find number of pairs of voters in same district
    preserved_pairs = (pops * (pops - 1)).sum() / 2

    # if there are no pairs of people, return 1 (rare, un-impactful corner case)
    if all_pairs == 0:
        all_pairs = 1

    # return proportion of split pairs
    return (all_pairs - preserved_pairs) / all_pairs


def conditional_entropy(pops):
    """Calculates conditional entropy score for a single locality from a pandas Series or numpy array of the
    populations of all (locality, district) intersections."""

    # get rid of zero population parts
    pops = pops[pops > 0]

    # find total number of people
    total_population = pops.sum()

    # find total entropy over all people
    total_entropy = (pops * np.log2(total_population / pops)).sum()

    # return entropy per person
    return total_entropy / total_population


def sqrt_entropy(pops):
    """Calculates square root entropy score for a single locality from a pandas Series or numpy array of the
    populations of all (locality, district) intersections."""

    # get rid of zero population parts
    pops = pops[pops > 0]

    # find total number of people
    total_population = pops.sum()

    # find total square root entropy over all people
    total_entropy = (pops * np.sqrt(total_population / pops)).sum()

    # return entropy per person
    return total_entropy / total_population


def effective_splits(pops):
    """Calculates effective splits score for a single locality from a pandas Series or numpy array of the
    populations of all (locality, district) intersections."""

    # turn populations into proportions
    props = pops / pops.sum()

    # return effective splits
    return 1 / (props ** 2).sum() - 1
