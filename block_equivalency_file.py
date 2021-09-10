import pandas as pd
import requests
from io import BytesIO
from zipfile import ZipFile
import math
import us

def congress(election_year):
    """ Return the number of the Congress (e.g., 115th) corresponding to the election year (e.g., 2016)."""
    return math.floor(election_year / 2) - 893


def get_url(year, plan_type):
    """ Get the URL on U.S. Census website to .zip file containing block equivalency file.

    Arguments:
        year: election year
        plan_type: one of cd (for congressional districts), sldu (for state upper chamber), or
            sldl (for state lower chamber)
    Output: URL for downloading .zip file
    """

    # if invalid plan type or year, throw an error
    if plan_type not in ['cd', 'sldu', 'sldl']:
        raise ValueError("Invalid plan_type passed to function")
    if year not in [2012, 2014, 2016, 2018]:
        raise ValueError("Data only available for 2012, 2014, 2016, 2018 elections")

    # initialize base web path for all of this data
    path = 'https://www2.census.gov/programs-surveys/decennial/rdo/mapping-files'

    # if congressional plan
    if plan_type == 'cd':

        # get url
        cng = congress(year)
        url = f'{path}/{year + 1}/{cng}-congressional-district-bef/cd{cng}.zip'

    # if state legislative plan
    else:

        # get url
        if year == 2012:
            suffix = 'post2010'
        else:
            suffix = year
        url = f'{path}/{year}/{year}-state-legislative-bef/{plan_type}_{suffix}.zip'

    return url


def get_block_equivalency_file(year, plan_type):
    """ Get block equivalency file from U.S Census.

    Arguments:
        year: election year
        plan_type: one of cd (for congressional districts), sldu (for state upper chamber), or
            sldl (for state lower chamber)
    Output: pandas DataFrame with a column for census block GEOID and district name
    """

    # get url to read .zip file from
    url = get_url(year, plan_type)

    # read in zip file from url
    content = requests.get(url)
    f = ZipFile(BytesIO(content.content))

    # find the national file in the zipped archive
    natl_files = [filename for filename in f.namelist() if 'National' in filename]
    if len(natl_files) != 1:
        raise ValueError("Did not find exactly one file with 'National' in name")

    # open national file
    file = f.open(natl_files[0])

    # read file to pandas DataFrame, format district column
    df = pd.read_csv(file, dtype=str, usecols=[0, 1])
    df.columns = [df.columns[0], f'{plan_type}_{year}']

    return df


def merge_state_census_block_pops(state, block_equiv_file):
    """ Merge populations into a block equivalency file

    Arguments:
        state: state name, abbreviation, or FIPS code
        block_equiv_file: pandas DataFrame outputted by get_block_equivalency_file()
            with a BLOCKID column and a column for the district
    Output: block_equiv_file sliced down to the given state, with a population column added
    """

    # get FIPS code
    if not isinstance(state, str): # if user appears to provide a FIPS code, make sure it's properly formatted
        state = str(state).zfill(2)
    try:
        fips_code = us.states.lookup(state).fips
    except AttributeError:
        raise ValueError("Invalid state name provided.")

    # get census API query
    base = 'https://api.census.gov/data/2010/dec/sf1'
    variables = '?get=P001001,GEO_ID'
    level = '&for=block:*'
    hierarchy = '&in=state:' + fips_code + '&in=county:*&in=tract:*'
    query = base + variables + level + hierarchy

    # query census for population
    data = requests.get(query).json()

    # make population DataFrame and do some basic cleaning
    df = pd.DataFrame(data[1:], columns=data[0]).iloc[:, :2]
    df.columns = ['pop', 'BLOCKID']
    df = df[['BLOCKID', 'pop']]
    df['pop'] = df['pop'].astype(float)
    df['BLOCKID'] = df['BLOCKID'].apply(lambda x: x.split('S')[1])

    # merge populations and block equivalency file
    merged = pd.merge(df, block_equiv_file, how='left', on='BLOCKID')

    # drop census blocks not in a district (these are unpopulated)
    district_col = block_equiv_file.columns[1]
    merged = merged[~merged[district_col].isin(['ZZ', 'ZZZ'])]

    # check that the merge worked as expected
    if any(merged.isna().sum() != 0):
        raise ValueError('Failed to merge in all district names')

    return merged
