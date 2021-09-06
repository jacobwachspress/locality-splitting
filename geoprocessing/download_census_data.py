"""Download relevant census geography and population data."""
import urllib.request as url
import requests
import os
import pandas as pd
from fips_lookup import state_fips


def main():
    """Extract redistricting boundaries, county boundaries, and blocks.

    The Census limits API requests to 500 per day. Running this file will
    make 50 requests. If you want to use your census API key, save
    a file called census_key.csv with the only entry being the key

    Place the file in the main folder of the repository

    Note we're using 2010 census blocks and census block populations. We are
    not using the combined file and using the and api to join population to
    geography to make transitioning to 2020 census data easier
    """
    # Get list of state fips
    fips = state_fips()

    # Add census data folder if it does not exist
    if not os.path.exists('raw_census'):
        os.makedirs('raw_census')

    # Congressional redistricting boundaries
    extract_congressional_boundaries()

    # Extract County Boundaries
    extract_county_boundaries()

    # State legislative redistricting boundaries
    extract_state_legislative_boundaries(fips)

    # Extract block data geographies
    extract_census_block_geographies(fips)

    # Load census key if it exists
    census_key = False
    if os.path.isfile('census_key.csv'):
        df_key = pd.read_csv('census_key.csv', names=['key'])
        census_key = df_key.iloc[0, 0]

    # Extract block data statistics
    extract_census_block_statistics(fips, census_key)
    return


def extract_state_legislative_boundaries(fips):
    """Extract state legislative boundaries from census tigerline.

    Arguments:
        fips: dictionary of state_fips
    """
    # Display that we are extracting census block populations
    print('EXTRACTING STATE LEGISLATIVE DISTRICTS------------------------\n\n')

    # Create folder for population
    if not os.path.exists('raw_census/state_leg'):
        os.makedirs('raw_census/state_leg')

    # Extract names of csvs that should exist
    zips = state_legislative_zips()

    # Define relevant years
    years = [2000, 2010] + list(range(2011, 2020))

    # While loop in case we disconnect from the census server
    while missing_download('raw_census/state_leg', zips):
        # Iterate through each state's lower chamber
        for i in years:
            # Get the census path and file (2000s path is slightly different)
            path = 'https://www2.census.gov/geo/tiger/TIGER'
            path += str(i) + '/SLDL/'

            # Iterate through each state
            for state, fips_code in fips.items():
                # Continue if nebraska because they don't have a lower chamber
                if state == 'NE':
                    continue

                # Get the file name
                file = 'tl_' + str(i) + '_' + fips_code + '_sldl.zip'
                if i == 2010:
                    path = 'https://www2.census.gov/geo/tiger/TIGER' + str(i)
                    path += '/SLDL/2010/'
                    file = 'tl_' + str(i) + '_' + fips_code + '_sldl10.zip'
                elif i == 2000:
                    path = 'https://www2.census.gov/geo/tiger/TIGER2010/SLDL/'
                    path += '2000/'
                    file = 'tl_2010_' + fips_code + '_sldl00.zip'

                    # Continue if state doesn't have 2000 district data
                    continue_states = ['AR', 'CA', 'FL', 'HI', 'KY', 'ME',
                                       'MD', 'MN', 'MT', 'NH', 'TX']
                    if state in continue_states:
                        continue

                # Get the actual file path
                census_geo = path + file

                # Get the output path
                output_zip = 'raw_census/state_leg/sldl_' + state
                output_zip += '_' + str(i) + '.zip'

                # If file does not exist try to retrieve it
                if not os.path.isfile(output_zip):
                    print(output_zip)
                    try:
                        url.urlretrieve(census_geo, output_zip)
                        url.urlcleanup()
                    # Keep as bare except for now for testing functionality
                    except:
                        print('\tError')
                        print(census_geo)
                        continue

        # Iterate through each state's upper chamber
        for i in years:
            # Get the census path and file (2000s path is slightly different)
            path = 'https://www2.census.gov/geo/tiger/TIGER'
            path += str(i) + '/SLDU/'

            # Iterate through each state
            for state, fips_code in fips.items():
                # Get the file name
                file = 'tl_' + str(i) + '_' + fips_code + '_sldu.zip'
                if i == 2010:
                    path = 'https://www2.census.gov/geo/tiger/TIGER' + str(i)
                    path += '/SLDU/2010/'
                    file = 'tl_' + str(i) + '_' + fips_code + '_sldu10.zip'
                elif i == 2000:
                    path = 'https://www2.census.gov/geo/tiger/TIGER2010/SLDU/'
                    path += '2000/'
                    file = 'tl_2010_' + fips_code + '_sldu00.zip'

                    # Continue if state doesn't have 2000 district data
                    continue_states = ['AR', 'CA', 'FL', 'HI', 'KY', 'ME',
                                       'MD', 'MN', 'MT', 'NH', 'TX']
                    if state in continue_states:
                        continue

                # Get the actual file path
                census_geo = path + file

                # Get the output path
                output_zip = 'raw_census/state_leg/sldu_' + state
                output_zip += '_' + str(i) + '.zip'

                # If file does not exist try to retrieve it
                if not os.path.isfile(output_zip):
                    print(output_zip)
                    try:
                        url.urlretrieve(census_geo, output_zip)
                        url.urlcleanup()
                    # Keep as bare except for now for testing functionality
                    except:
                        print('\tError')
                        print(census_geo)
                        continue

    return


def extract_census_block_statistics(fips, census_key=False):
    """Extract population data for each census block.

    Arguments:
        fips: dictionary of state_fips

        census_key: optional census API key
    """
    # Display that we are extracting census block populations
    print('EXTRACTING CENSUS BLOCK POPULATIONS------------------------\n\n')

    # Create folder for population
    if not os.path.exists('raw_census/block_pop'):
        os.makedirs('raw_census/block_pop')

    # Extract names of csvs that should exist
    csvs = census_block_pop_csvs()

    # While loop in case we disconnect from the census server
    while missing_download('raw_census/block_pop', csvs):
        # Iterate through each state
        for state, fips_code in fips.items():
            # Get the api query
            base = 'https://api.census.gov/data/2010/dec/sf1'
            variables = '?get=P001001,GEO_ID'
            level = '&for=block:*'
            hierarchy = '&in=state:' + fips_code + '&in=county:*&in=tract:*'
            query = base + variables + level + hierarchy
            if census_key:
                query += '&key=' + census_key

            # Get the path for the dataframe we will save
            output = 'raw_census/block_pop/block_population_' + state + '.csv'

            if not os.path.isfile(output):
                print(output)
                try:
                    data = requests.get(query).json()
                    df = pd.DataFrame(data[1:], columns=data[0])
                    df.to_csv(output, index=False)
                # Keep as bare except for now for testing functionality
                except:
                    print('\tError')
                    continue
    return


def extract_census_block_geographies(fips):
    """Extract geography data for each census block.

    Arguments:
        fips: dictionary of state_fips
    """
    # Display that we are extracting census block populations
    print('EXTRACTING CENSUS BLOCK GEOGRAPHIES------------------------\n\n')

    # Create folder for population
    if not os.path.exists('raw_census/block_geo'):
        os.makedirs('raw_census/block_geo')

    # Extract names of zip folders that should exist
    zips = census_block_geo_zips()

    # While loop in case we disconnect from the census server
    while missing_download('raw_census/block_geo', zips):
        # Get the path to the census block geometry folder
        path = 'https://www2.census.gov/geo/tiger/TIGER2019/TABBLOCK/'
        # Iterate through each state
        for state, fips_code in fips.items():
            # Get the file to download
            census_geo = path + 'tl_2019_' + fips_code + '_tabblock10.zip'

            # Get the path where we will save the zip folder
            output = 'raw_census/block_geo/block_geography_' + state + '.zip'

            # If file does not exist try to retrieve it
            if not os.path.isfile(output):
                print(output)
                try:
                    url.urlretrieve(census_geo, output)
                    url.urlcleanup()
                # Keep as bare except for now for testing functionality
                except:
                    print(census_geo)
                    print('\tError')
                    continue
    return


def extract_county_boundaries():
    """Obtain relevant county boundaries for each year."""
    # Display that we are extracting congressionall Boundaries
    print('EXTRACTING COUNTY BOUNDARIES------------------------\n\n')

    # Create folder for congressional districts
    if not os.path.exists('raw_census/county'):
        os.makedirs('raw_census/county')

    # Extract names of zip folders that should exist
    zips = county_boundaries_zips()

    # Define relevant years
    years = [2000, 2010] + list(range(2011, 2020))

    # While loop in case we disconnect from census server
    while missing_download('raw_census/county', zips):
        # Iterate through each years
        for i in years:
            # Get the census path and file (2000s path is slightly different)
            path = 'https://www2.census.gov/geo/tiger/TIGER'
            path += str(i) + '/COUNTY/'
            file = 'tl_' + str(i) + '_us_county.zip'
            if i == 2010:
                path += '2010/'
                file = 'tl_2010_us_county10.zip'
            elif i == 2000:
                path = 'https://www2.census.gov/geo/tiger/TIGER2010/COUNTY/'
                path += '2000/'
                file = 'tl_2010_us_county00.zip'

            # Get the actual file path
            census_geo = path + file

            # Get the output path
            output_zip = 'raw_census/county/counties_' + str(i) + '.zip'

            # If file does not exist try to retrieve it
            if not os.path.isfile(output_zip):
                print(output_zip)
                try:
                    url.urlretrieve(census_geo, output_zip)
                    url.urlcleanup()
                # Keep as bare except for now for testing functionality
                except:
                    print('\tError')
                    continue

    return


def extract_congressional_boundaries():
    """Obtain relevant congressional district boundaries."""
    # Display that we are extracting congressionall Boundaries
    print('EXTRACTING CONGRESSIONAL BOUNDARIES------------------------\n\n')
    # Create folder for congressional districts
    if not os.path.exists('raw_census/cd'):
        os.makedirs('raw_census/cd')

    # Extract names of zip folders that should exist
    zips = congressional_district_zips()

    # Define relevant years
    years = [2003, 2010] + list(range(2011, 2020))

    # While loop in case we disconnect from census server
    while missing_download('raw_census/cd', zips):
        # Iterate through each years congressional maps during 2010s
        for i in years:
            # Get congress number
            congress_num = years_to_congress_num(i)

            # Get the census path and file (2000s path is slightly different)
            path = 'https://www2.census.gov/geo/tiger/TIGER' + str(i) + '/CD/'
            file = 'tl_' + str(i) + '_us_cd' + congress_num + '.zip'
            if i == 2010:
                path += congress_num + '/'
            elif i == 2003:
                path = 'https://www2.census.gov/geo/tiger/TIGER2010/CD/108/'
                file = 'tl_2010_us_cd108.zip'

            # Get the actual file path
            census_geo = path + file

            # Get the output path
            output_zip = 'raw_census/cd/national_' + str(i) + '.zip'

            # If file does not exist try to retrieve it
            if not os.path.isfile(output_zip):
                print(output_zip)
                try:
                    url.urlretrieve(census_geo, output_zip)
                    url.urlcleanup()
                # Keep as bare except for now for testing functionality
                except:
                    print('\tError')
                    continue

    return

def years_to_congress_num(year):
    """For a given year return the Nth congress

    Used for census name in congressional district shapefiles.

    As found here https://www2.census.gov/geo/tiger/TIGER2012/CD/ for each
    individual year
    """
    d = {}
    d[2019] = '116'
    d[2018] = '116'
    d[2017] = '115'
    d[2016] = '115'
    d[2015] = '114'
    d[2014] = '114'
    d[2013] = '113'
    d[2012] = '112'
    d[2011] = '112'
    d[2010] = '111'
    d[2003] = '108'
    return d[year]


def missing_download(directory, files):
    """Check if all files in a list exists in a folder.

    If this returns False, this means we need to download files

    Arguments:
        directory:
            directory that we are checking if files exist

        files:
            list of files to check if they are in the directory

    Output:
        True if all files are in directory otherwise False
    """
    # Get files in the directory
    files_in_directory = set(os.listdir(directory))

    # If there are files not in the directory we are missing downloads
    if set(files) - set(files_in_directory):
        return True
    return False


def congressional_district_zips():
    """Derive zip folder names for congressional districts."""
    paths = []

    # Get paths in the 2010
    years = [2003, 2010] + list(range(2011, 2020))
    for i in years:
        paths.append('national_' + str(i) + '.zip')
    return paths


def state_legislative_zips():
    """Derive zip folder names for state legislative districts."""
    paths = []
    fips = state_fips()

    # Get list of 2000 continue states
    skip_states_lower = ['AR', 'CA', 'FL', 'HI', 'KY', 'ME', 'MD', 'MN', 'MT',
                         'NH', 'TX']
    # Get paths for both upper and lower districts
    years = [2000, 2010] + list(range(2011, 2020))
    for i in years:
        for state, fips_code in fips.items():
            # Append paths (Nebraska doesn't have a lower house)
            if i != 2000 or state not in skip_states_lower:
                if state != 'NE':
                    paths.append('sldl_' + state + '_' + str(i) + '.zip')
                paths.append('sldu_' + state + '_' + str(i) + '.zip')
    return paths


def county_boundaries_zips():
    """Derive zip folder names for county boundaries."""
    paths = []

    # Get paths in the 2010
    years = [2000, 2010] + list(range(2011, 2020))
    for i in years:
        paths.append('counties_' + str(i) + '.zip')
    return paths


def census_block_pop_csvs():
    """Derive csv names for census block population csvs."""
    # Initialize paths and get state fips dictionary
    paths = []
    fips = state_fips()

    # Get names for each
    for key, elem in fips.items():
        paths.append('block_population_' + key + '.csv')
    return paths


def census_block_geo_zips():
    """Derive csv names for census block geography zip folders."""
    # Initialize paths and get state fips dictionary
    paths = []
    fips = state_fips()

    # Get names for each
    for key, elem in fips.items():
        paths.append('block_geography_' + key + '.zip')
    return paths


if __name__ == "__main__":
    main()
