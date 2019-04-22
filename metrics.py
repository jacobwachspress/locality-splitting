# -*- coding: utf-8 -*-
"""
Created on Sat Apr  6 15:13:31 2019

@author: Jacob
"""
import numpy as np

# RENAME THIS METRIC
# Some research shows this is from Rand (1971) and Wallace (1983)
def population_informed_county_split_statistic(pops):
    ''' Calculates PICS statistic given population intersections between
    districts and counties
    
    Arguments: 
        pops: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.
            
    Output: 
        PICS statistic (number between 0 and 1): the probability that 
        two randomly chosen people from the same county are also
        in the same district.'''
    
    # get counties
    counties = set([key[0] for key in pops])
    
    ## calculate number of pairs of people in the same county and same district
    
    # intitialize variable
    same_county_same_district = 0
     
    for county in counties:
        intersections_in_county = [key for key in pops if key[0] == county]
        for intersection in intersections_in_county:
            # get number of people in county-district intersection
            shared_pop = pops[intersection]
            # update number of pairs in same county and same district
            new_pairs = (shared_pop * (shared_pop - 1)) / 2
            same_county_same_district = same_county_same_district + new_pairs
            
    ## calculate number of pairs of people in the same county 
    
    # intitialize variable
    same_county = 0
    
    for county in counties:
        # get population of county
        county_pop = 0
        intersections_in_county = [key for key in pops if key[0] == county]
        for intersection in intersections_in_county:
            county_pop = county_pop + pops[intersection]
        
        # update number of pairs in same county
        new_pairs = (county_pop * (county_pop - 1)) / 2
        same_county = same_county + new_pairs
            
    ## calculate and return PICS
    PICS = same_county_same_district / same_county
    return PICS
        
# Adaptation of criterion here https://doi.org/10.1080/01621459.1954.10501231
def goodman_kruskal_statistic(pops):  
    ''' Calculates GK statistic given population intersections between
    districts and counties
    
    Arguments: 
        pops: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.
            
            
    Output: 
        GK statistic (number between 0 and 1): the fraction of voters who are
        in the congressional district that has the largest number of their
        county's voters.  Alternatively, if everyone assumed that 
        their congressional district was the one with the largest number
        of their county's residents, the proportion who would be correct.'''
    
    # get counties
    counties = set([key[0] for key in pops])
    
    # initialize variables
    state_pop = 0
    in_largest_district = 0
    
    for county in counties:
        # get list of populations intersections in county
        intersections_in_county = [key for key in pops if key[0] == county]
        intersection_pops = [pops[i] for i in intersections_in_county]
        
        # find county population
        county_pop = sum(intersection_pops)
        # find number of people in largest intersection
        max_district_pop = max(intersection_pops)
        
        # update global variables
        state_pop = state_pop + county_pop
        in_largest_district = in_largest_district + max_district_pop
        
    # calculate and return statistic
    GK = in_largest_district / state_pop
    return GK
    
def shannon_entropy(partition):
    ''' Calculates Shannon entropy of a partition according to the formula
    
         - sum (p_i log_2 p_i)
         
        where p_i is the probability of being in the ith element of the 
        partition.
    
    Arguments:
        partition: numpy array containing the number of elements in each part
        
    Output: Shannon entropy'''
    
    normalized = partition / np.sum(partition)
    logs = normalized * np.log2(normalized)
    return (- np.sum(logs))

    
def lopez_de_mantaras(pops):
    ''' Calculates Lopez de Mantaras metric, summing 
        1) conditional entropy of district partition with repsect to county 
        partition 
        2) conditional entropy of county partition with repsect to district 
        partition 
        
        based on this: https://tel.archives-ouvertes.fr/tel-00176776/document
        described in english here: https://www.cs.umb.edu/~dsim/papersps/umb.pdf 
        (slides 19-21)
        
    Arguments: 
        pops: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.
            
    Output: 
        Reciprocal of Lopez de Mantaras metric, so more similar parititions
        yield a higher number'''
        
    # get population of state
    state_pop = sum(pops.values())
    
    # initialize variable for metric
    total = 0
    
    # CALCULATE CONDITIONAL ENTROPY OF EACH PARTITION WITH RESPECT TO 
    # THE OTHER
    
    # indexing over both counties and districts
    for x in [0,1]:
        
        # get counties or districts (depending on x)
        regions = set([key[x] for key in pops])
        
        for region in regions:
            # get list of populations intersections in county
            intersections_in_region = [key for key in pops if key[x] == region]
            intersection_pops = [pops[i] for i in intersections_in_region]
            
            # find region population
            region_pop = sum(intersection_pops)
            
            # update statistic
            total = total + shannon_entropy(intersection_pops) * \
                    region_pop/state_pop
    
    return np.divide(1, total)