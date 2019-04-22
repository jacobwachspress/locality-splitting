# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 17:46:38 2019

@author: Jacob
"""

import shapely as shp
import geopandas as gpd
import pandas as pd
from shapely.ops import cascaded_union
from rtree import index

def get_county_district_intersections(counties, districts):
    ''' Finds geometric intersections of counties and districts
    
    Arguments: 
        counties: GeoDataFrame of the counties in a state
        districts: GeoDataFrame of the districts in a state
        
    Output: dictionary whose keys are ordered pairs (county, district)
        and whose values are the geometries corresponding to the intersections.
        County and district names are not preserved, indices are whole numbers.
    '''
    
    # initialize dictionary to be returned
    intersections = {}
    
    # initialize r-tree index
    idx = index.Index()
    
    # populate R-tree index with bounds of counties
    for i, county in counties.iterrows():
        idx.insert(i, county['geometry'].bounds)
    
    # find intersections
    for j, district in districts.iterrows():
        for i, county in counties.iterrows():
            county_geom = county['geometry']
            district_geom = district['geometry']
            # use rtree to quickly eliminate many cases
            if i not in idx.intersection(district_geom.bounds):
                intersections[(i, j)] = None
            else:
                intersection = county_geom.intersection(district_geom)
                if intersection.is_empty:
                    intersections[(i, j)] = None
                else:
                    intersections[(i, j)] = intersection
                    
    
    return intersections

def get_pops_of_intersections(intersections, block_groups, pop_str):
    ''' Calculates population of each county-district intersection,
    based on block group populations.
    
    Arguments: 
        intersections: as outputted by get_county_district_intersections,
            a dictionary whose keys are ordered pairs (county, district)
            and whose values are the geometries corresponding to the 
            intersections.
        block_groups: GeoDataFrame of the block_groups in a state
        pop_str: the name of the column in block_groups that contains 
            population data (type: string)
        
    Output: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.
    
    Note: There is some imprecision associated with this function.  If a 
        district boundary splits a block group, then there is no way to assign
        the members of the block group to their district(s) with certainty. 
        (Luckily,all block groups are in exactly one county.)  When a 
        block group is split, we assign population by area, which is the best
        proxy wew have for population.
        
        Furthermore, since the district shapefiles from the census drawn 
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
    
    # initialize r-tree index
    idx = index.Index()
    
    # populate R-tree index with bounds of block groups
    for i, blk_grp in block_groups.iterrows():
        idx.insert(i, blk_grp['geometry'].bounds)
    
    # iterate over block groups
    for i, blk_grp in block_groups.iterrows():
        
        # get blk_grp data once 
        blk_grp_geom = blk_grp['geometry']
        blk_grp_area = blk_grp_geom.area
        blk_grp_pop = int(blk_grp[pop_str])
        
        # initialize dictionary for population updates
        blk_grp_pops = {}
        
        # iterate over county-district pairs
        for key in intersections:
            # get geometry of county-district intersection
            geom = intersections[key]
            if geom is not None:
                bounds = geom.bounds
                # use rtree to filter out a whole bunch of cases
                if i in idx.intersection(bounds):
                    # get intersection of block group with county-district
                    # overlap, will be zero or entire block group most of the
                    # time, if block group is split, assume population is 
                    # uniform over area
                    
                    intersect_area = geom.intersection(blk_grp_geom).area
                    proportion = intersect_area/blk_grp_area
                    # population to add
                    blk_grp_pops[key] = blk_grp_pop * proportion
        
        # scale for intersections not found (so no population is lost)
        # this is a source of error: if the district shp does not cover all the
        # block groups, we can't assign the people in the block group with
        # certainty, so we scale this by the people already found
        found_pop = sum(blk_grp_pops.values())
        if found_pop > 0:
            for d in blk_grp_pops:
                blk_grp_pops[d] = blk_grp_pops[d] * blk_grp_pop / found_pop
                
        # update populations
        for d in blk_grp_pops:
            pops[d] = pops[d] + blk_grp_pops[d]

    # remove keys with no population
    to_remove = [key for key in pops if pops[key] == 0]
    for key in to_remove:
        pops.pop(key, None)
    
    return pops

def county_district_intersection_pops(counties, districts, \
                                      block_groups, pop_str):
    ''' Calculates population of each county-district intersection,
    based on appropriate GeoDataFrames and block group populations.
    
    Arguments: 
        counties: GeoDataFrame of the counties in a state
        districts: GeoDataFrame of the districts in a state
        block_groups: GeoDataFrame of the block_groups in a state
        pop_str: the name of the column in block_groups that contains 
            population data (type: string)
            
    Output: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.
        County and district names are not preserved, indices are whole numbers.
    '''
    
    intersections = get_county_district_intersections(counties, districts)
    return get_pops_of_intersections(intersections, block_groups, pop_str)

def counties_from_block_groups(block_groups, county_str):
    ''' Generates county GeoDataFrame (geometries only) based on block group
    GeoDataFrame.
    
    Arguments:
        block_groups: GeoDataFrame of the block_groups in a state
        county_str: the name of the column in block_groups that contains 
            the ID of the county (type: string)
            
    Output: GeoDataFrame with geometries of all counties in the state
    '''
    counties = list(set(block_groups.loc[:, county_str]))
    geometries = []
    for county in counties:
        in_county = block_groups.loc[block_groups[county_str] == county]
        geometries.append(cascaded_union(list(in_county.loc[:, 'geometry'])))
    df = pd.DataFrame(counties)
    return gpd.GeoDataFrame(df, geometry=geometries)



    