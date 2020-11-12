"""Aggregate interpolation and intersection information across states."""
import pandas as pd
from download_census_data import state_fips


def main():
    """Aggregate various interpolation metrics

    nationwide_classifcations: nationwide block equivalency file

    We will also create the following aggregated files
        nationwide_district_contains_county
        nationwide_district_contains_district
        nationwide_district_county_intersection
    """
    fips = state_fips()

    # Perform aggregations. Iterating through clean data and appending
    df = aggregate_nationwide(fips, 'classifications',
                              ['state', 'GEOID10', 'pop'])
    df_dcc = aggregate_nationwide(fips, 'district_contains_county',
                                  ['state', 'COUNTYFP'])
    df_dcd = aggregate_nationwide(fips, 'district_contains_district',
                                  ['state', 'base', 'base_value'])
    df_dci = aggregate_nationwide(fips, 'district_country_intersection',
                                  ['state', 'COUNTYFP'])

    # Save aggregated files
    df.to_csv('nationwide_classifications.csv', index=False)
    df_dcc.to_csv('nationwide_district_contains_county.csv', index=False)
    df_dcd.to_csv('nationwide_district_contains_district.csv', index=False)
    df_dci.to_csv('nationwide_district_county_intersection.csv', index=False)
    return


def nationwide_classifications(fips):
    """Aggregate block equivalency files for redistricting plans by year."""
    return


def aggregate_nationwide(fips, name, first_cols):
    """Aggregate interpolation files nationwide.

    fips: dictionary of state abbreviations and fips code

    name: name of suffix we are aggregating

    first_cols: first columns in the aggregated file (list)
    """
    # Print Progress
    print(name)

    # Intialize aggregation file
    df = pd.DataFrame()

    # Get plan names
    plan_names = redistricting_plan_columns()

    # Iterate over each state
    for state, fips_code in fips.items():
        # progress
        print('\t', state)

        # Get path of file to aggregate
        path = 'clean_data/' + state + '/'
        path += state + '_' + name + '.csv'

        # Load file
        df_state = pd.read_csv(path)

        # Impute years that redistricting plan did not change
        for level in plan_names:
            for plan_ix, plan in enumerate(level):
                # Add column if it does not exist in the file
                if plan not in df_state.columns:
                    df_state[plan] = None

                    # Impute previous plan if it is not the first plan
                    if plan_ix > 0:
                        c = level[plan_ix - 1]
                        df_state[plan] = df_state[plan].fillna(df_state[c])

        # Add state to dataframe
        df_state['state'] = state

        # Append to the nationwide file
        df = df.append(df_state)

    # Sort columns
    df = df[first_cols + plan_names[0] + plan_names[1] + plan_names[2]]
    return df


def nationwide_district_contains_district(fips):
    """Aggregate subdistrict within district assignments."""
    return


def nationwide_district_county_intersection(fips):
    """Aggregate county and district intersections."""
    return


def redistricting_plan_columns():
    """Return list of lists of relevant plan names."""
    cd = ['cd_2003']
    sldl = ['sldl_2000']
    sldu = ['sldu_2000']
    for i in range(2010, 2020):
        cd.append('cd_' + str(i))
        sldu.append('sldu_' + str(i))
        sldl.append('sldl_' + str(i))
    return [cd, sldu, sldu]


if __name__ == "__main__":
    main()
