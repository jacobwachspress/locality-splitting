"""Extract relevant census data from tigerline."""
import urllib.request as url
import requests
import os
import pandas as pd


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
    # extract_upper_state_legislative_boundaries()
    # extract_lower_state_legislative_boundaries()s
    #
    # # Extract block data geographies
    # extract_census_block_geographies()

    # Load census key if it exists
    census_key = False
    if os.path.isfile('census_key.csv'):
        df_key = pd.read_csv('census_key.csv', names=['key'])
        census_key = df_key.iloc[0, 0]

    # Extract block data statistics
    extract_census_block_statistics(fips, census_key)
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
    csvs = census_block_csvs()

    # While loop in case we disconnect from the census server
    while missing_download('raw_census/block_pop', csvs):
        # Iterate through each state
        for state, fips_code in fips.items():
            # Get the api query
            base = 'https://api.census.gov/data/2010/dec/sf1'
            variables = '?get=H010001,GEO_ID'
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
                    continue
    return


def extract_congressional_boundaries():
    """Obtain relevant congressional district boundaries.

    Arguments:
        fips: dictionary of states and their FIPS code
    """
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
                    continue

    return


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


def census_block_csvs():
    """Derive csv names for census block csvs."""
    # Initialize paths and get state fips dictionary
    paths = []
    fips = state_fips()

    # Get names for each
    for key, elem in fips.items():
        paths.append('block_population_' + key + '.csv')
    return paths


if __name__ == "__main__":
    main()
