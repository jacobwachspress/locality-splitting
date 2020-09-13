"""General handling of geographic files for county split analysis."""

import geopandas as gpd
import pandas as pd
import json
from shapely.ops import cascaded_union
from rtree import index


def get_county_district_intersections(c_df, d_df, county_str):
    ''' Finds geometric intersections of c_df and d_df

    Arguments:
        c_df: GeoDataFrame of the counties in a state
        d_df: GeoDataFrame of the d_df in a state
        county_str: name of county column in c_df

    Output: dictionary whose keys are ordered pairs (county, district)
        and whose values are the geometries corresponding to the intersections.
    '''
    # initialize dictionary to be returned
    intersections = {}

    # initialize r-tree index
    idx = index.Index()

    # populate R-tree index with bounds of c_df
    for i, county in c_df.iterrows():
        idx.insert(i, county['geometry'].bounds)

    # find intersections
    for j, district in d_df.iterrows():
        for i, county in c_df.iterrows():
            county_geom = county['geometry']
            district_geom = district['geometry']
            # use rtree to quickly eliminate many cases
            if i in idx.intersection(district_geom.bounds):
                intersection = county_geom.intersection(district_geom)
                if not intersection.is_empty:
                    intersections[(county[county_str], j)] = intersection

    return intersections


def get_pops_of_intersections(intersections, b_df, county_str, pop_str):
    ''' Calculates population of each county-district intersection,
    based on block group populations.

    Arguments:
        intersections: as outputted by get_county_district_intersections,
            a dictionary whose keys are ordered pairs (county, district)
            and whose values are the geometries corresponding to the
            intersections.
        b_df: GeoDataFrame of the census blocks in a state
        county_str: name of county column in c_df
        pop_str: the name of the population column in b_df

    Output: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.

    Note: There is some imprecision associated with this function.  If a
        district boundary splits a block, then there is no way to assign
        the members of the block to their district(s) with certainty.
        (Luckily, all block groups are in exactly one county.)  When a
        block group is split, we assign population by area, which is the best
        proxy we have for population.

        Furthermore, since the district shapefiles from the census are drawn
        separately from the block group files (i.e. there are no block group
        equivalency files), it may be the case that the districts do not
        entirely cover a block group.  In this case, we assign the population
        of the block group proportionally to intersections that were found,
        so as to preserve the total population of the state.
    '''

    # initialize population dictionary to 0 at all intersections
    pops = {}
    for key in intersections:
        pops[key] = 0

    # iterate over counties
    counties = list(set([key[0] for key in intersections]))
    for county in counties:
        # initialize list for used blocks
        used = []

        # cut down the block dataframe to what is necessary (specific county)
        cblocks_df = b_df.loc[b_df[county_str] == county]

        # shortcut if county is not split
        county_intersections = [key for key in pops if key[0] == county]
        if len(county_intersections) == 1:
            intersection = county_intersections[0]
            block_pops = list(cblocks_df.loc[:, pop_str])
            pops[intersection] = pops[intersection] + sum(block_pops)

        else:
            # initialize r-tree index
            idx = index.Index()

            # populate R-tree index with bounds of block groups
            for i, block in cblocks_df.iterrows():
                idx.insert(i, block['geometry'].bounds)

            # iterate over block groups
            for i, block in cblocks_df.iterrows():

                # get block data once
                block_geom = block['geometry']
                block_area = block_geom.area
                block_pop = int(block[pop_str])

                for key in county_intersections:
                    # get geometry of county-district intersection
                    geom = intersections[key]
                    if geom is not None:
                        bounds = geom.bounds
                        # use rtree to filter out a whole bunch of cases
                        if i not in used and i in idx.intersection(bounds):
                            # get intersection of block group with
                            # county-district overlap, will be zero or entire
                            # block group most of the time, if block group is
                            # split, assume population is uniform over area

                            intersect_area = geom.intersection(block_geom).area
                            proportion = intersect_area / block_area
                            # population to add
                            pop_to_add = block_pop * proportion
                            pops[key] = pops[key] + pop_to_add
                            # mark as used
                            if proportion > 0.99:
                                used.append(i)

    # remove keys with no population
    to_remove = [key for key in pops if pops[key] == 0]
    for key in to_remove:
        pops.pop(key, None)
    return intersections, pops


def county_district_intersection_pops(c_df, d_df, b_df,
                                      b_county_str='COUNTYFP10',
                                      c_county_str='COUNTYFP10',
                                      pop_str='POP10'):
    ''' Calculates population of each county-district intersection,
    based on appropriate GeoDataFrames and block group populations.

    Arguments:
        c_df: GeoDataFrame of the counties in a state
        d_df: GeoDataFrame of the districts in a state
        b_df: GeoDataFrame of the blocks in a state
        b_county_str: name of county column in b_df
        c_county_str: name of county column in c_df
        pop_str: the name of the column in b_df that contains
            population data (type: string)

    Output: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.
        County and district names are not preserved, indices are whole numbers.
    '''

    intersections = get_county_district_intersections(c_df, d_df, c_county_str)
    return get_pops_of_intersections(intersections, b_df, b_county_str,
                                     pop_str)


def counties_from_blocks(b_df, county_str):
    ''' Generates county GeoDataFrame (geometries only) based on block group
    GeoDataFrame.

    Arguments:
        b_df: GeoDataFrame of the blocks in a state
        county_str: name of county column in b_df

    Output: GeoDataFrame with geometries of all counties in the state
    '''
    counties = list(set(b_df.loc[:, county_str]))
    geometries = []
    for county in counties:
        in_county = b_df.loc[b_df[county_str] == county]
        geometries.append(cascaded_union(list(in_county.loc[:, 'geometry'])))
    df = pd.DataFrame(counties)
    return gpd.GeoDataFrame(df, geometry=geometries)


def left_position(geom):
    return geom.bounds[0]


def same_plan(d_df1, d_df2, precision=0.01):
    try:
        geos1 = d_df1.loc[:, 'geometry']
        geos2 = d_df2.loc[:, 'geometry']
        geos1 = sorted(geos1, key=left_position)
        geos2 = sorted(geos2, key=left_position)

        # If there is only one district it must be the same plan
        if len(geos1) == 1 and len(geos2) == 1:
            return True

        # If a different number of districts it must be different plans
        if len(geos1) != len(geos2):
            return False

        # Get intersections between geometries of both plans
        # At this point, they have the same number of districts
        geo_ran = range(len(geos1))
        intersections = [geos1[i].intersection(geos2[i]).area for i in geo_ran]

        # Get intersection ratios for both plans
        intersections1 = [intersections[i] / geos1[i].area for i in geo_ran]
        intersections2 = [intersections[i] / geos2[i].area for i in geo_ran]

        # If any of the iterations is outside of the precision the plans
        # are not the same
        for i in intersections1:
            if i < 1 - precision or i > 1 + precision:
                return False
        for i in intersections2:
            if i < 1 - precision or i > 1 + precision:
                return False

        # If all intersections were within precisoin, the plans are the same
        return True
    except:
        return False


def dict_to_json(pops, output_file):
    """Convert our tuple indexed dictionary object into a json.

    We have been using a dictionary for each of the intersection as follows

    The keys have been an ordered pair of (county, district) with the values
    being population. However, values do not necessarily need to be population
    for this function

    This function converts this dictionary to a json file using the structure
        "C{county id}D{district id}"

    Arguments:
        pops:
            dictionary containing intersection populations

        output_file:
            file to save to
    """
    # make keys strings
    output_pops = {}
    for key in pops:
        output_pops[f'C{key[0]}D{key[1]}'] = pops[key]
    # write json
    with open(output_file, 'w') as fp:
        json.dump(output_pops, fp)


def json_to_dict(input_file):
    """Convert json function to our intersection dictionary structure

    This function is the inverse of dict_to_json

    We will result with a dictionary with the keys being an ordered tuple
    of county id and district id
    """
    # read json
    with open(input_file, 'r') as fp:
        string_key_dict = json.load(fp)

    # make keys ordered pairs
    output_dict = {}
    for key in string_key_dict:
        D = key.index('D')
        output_dict[(key[1:D], key[D+1:])] = string_key_dict[key]
    return output_dict
