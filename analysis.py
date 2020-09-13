"""Perform county-split analysis."""

import matplotlib.pyplot as plt
from geoprocessing import json_to_dict
from metrics import (threshold, counties_split, county_intersections,
                     preserved_pairs, largest_intersection, min_entropy)
import os
import pandas as pd
import geopandas as gpd


def main():
    # define state fips dictionary
    fips = state_fips()

    # Create plans evaluation and save
    df_plans = calculate_metrics(fips)
    df_plans.to_csv('evaluated_plans.csv', index=False)

    # Perform Pennsylvania analysis
    pennsylvania_analysis('2016')
    pennsylvania_analysis('2018')
    return


def calculate_metrics(fips):
    """Calculate county split metrics for each redistricting plan."""
    # Initialize dataframe that will keep stats for each plan
    plans_cols = ['state', 'body', 'year', 'pops', 'counties_split',
                  'county_intersections', 'preserved_pairs',
                  'largest_intersection', 'min_entropy']
    df_plans = pd.DataFrame(columns=plans_cols)

    # Iterate through each states redistricting plnas
    for state, fips_code in fips.items():
        path = 'Data/Output/' + state + '/'
        for file in os.listdir(path):
            year = int(file[:4])
            body = file[5:-5]

            # Attempt to calculate metrics
            try:
                pops = json_to_dict(path + file)
                num_districts = len(set([key[1] for key in pops]))

                # define the threshold for removing members from districts
                # minimum of 500 or 0.5% of average district population
                thresh = 0.005 * sum(pops.values()) / num_districts
                thresh = min(thresh, 500)

                # Remove intersection population errors
                pops = threshold(pops, threshold=thresh)

                # Create appending dictionary
                row = {}
                row['state'] = state
                row['body'] = body
                row['year'] = year
                row['pops'] = pops

                # Add metric calculations
                row['counties_split'] = counties_split(pops)
                row['county_intersections'] = county_intersections(pops)
                row['preserved_pairs'] = preserved_pairs(pops)
                row['largest_intersection'] = largest_intersection(pops)
                row['min_entropy'] = min_entropy(pops)

                # Append to df_plans
                df_plans = df_plans.append(row, ignore_index=True)

            # Print file if we canot get metrics
            except Exception as e:
                print(path + file)
                print(str(e))
    return df_plans


def pennsylvania_analysis(year='2018'):
    """Perform relevant analyiss on PA for the paper.

    We compare either the 2018 and 2016 districting plans.

    Arguments:
        year: a string for which year to evaluate
    """
    # Read in shapefiles and population jsons
    geo_df = gpd.read_file('Data/PA/2010_counties.shp')
    districts = gpd.read_file('Data/PA/' + year + '_congress.shp')
    pops = json_to_dict('Data/Output/PA/' + year + '_congress.json')

    # Extract pennsylvania counties
    counties = set([key[0] for key in pops])

    # Create dictionary that has list of populations for each district that
    # intersect with a county
    intersect_pops = {county: [pops[key] for key in pops if key[0] == county]
                      for county in counties}

    # (i * (i-1)) / 2 = [1 + 2 + ... + i-1]. Graph theory # connections between
    # people. Get the number of connections within district county intersection
    county_district_conn = {county: sum([i * (i - 1) / 2
                            for i in intersect_pops[county]])
                            for county in counties}

    # Calculate the population of each county
    county_pops = {county: sum([pops[key] for key in pops if key[0] == county])
                   for county in counties}

    # Calculate the total number of connections in the county
    county_conn = {county: county_pops[county] * (county_pops[county] - 1) / 2
                   for county in counties}

    # Get the propoortion of county district connections to county connections
    proportions = {county: county_district_conn[county] / county_conn[county]
                   for county in counties}

    # Convert results to dataframe
    df = pd.DataFrame(list(proportions.items()),
                      columns=['COUNTYFP10', 'PROP'])

    # Join to geometries
    geo_df = geo_df.merge(df, on='COUNTYFP10')

    # Plot results
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    geo_df.plot(ax=ax, column='PROP', cmap='Greens', edgecolor='white',
                linewidth=1)
    districts.plot(ax=ax, color=[1, 1, 1, 0], edgecolor='red', linewidth=1)
    fig.savefig('Data/Output/pa' + year + '.png')


def state_fips():
    """Return dictionary of state abbreviations and fips code.

    Fips code will be a string and abbreviations are two letters.
    """
    fips = {'AL': '01',
            'AK': '02',
            'AZ': '04',
            'AR': '05',
            'CA': '06',
            'CO': '08',
            'CT': '09',
            'DE': '10',
            'FL': '12',
            'GA': '13',
            'HI': '15',
            'ID': '16',
            'IL': '17',
            'IN': '18',
            'IA': '19',
            'KS': '20',
            'KY': '21',
            'LA': '22',
            'ME': '23',
            'MD': '24',
            'MA': '25',
            'MI': '26',
            'MN': '27',
            'MS': '28',
            'MO': '29',
            'MT': '30',
            'NE': '31',
            'NV': '34',
            'NM': '35',
            'NY': '36',
            'NC': '37',
            'ND': '38',
            'OH': '39',
            'OK': '40',
            'OR': '41',
            'PA': '42',
            'RI': '44',
            'SC': '45',
            'SD': '46',
            'TN': '47',
            'TX': '48',
            'UT': '49',
            'VT': '50',
            'VA': '51',
            'WA': '53',
            'WI': '55',
            'WY': '56'}
    return fips


if __name__ == "__main__":
    main()
