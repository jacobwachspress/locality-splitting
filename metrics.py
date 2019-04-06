# -*- coding: utf-8 -*-
"""
Created on Sat Apr  6 15:13:31 2019

@author: Jacob
"""
# RENAME THIS METRIC
def population_informed_county_split_statistic(counties):
    ''' Calculates PICS statistic given populaiton intersections between
    districts and counties
    
    Arguments: 
        districts: dictionary where keys are counties, values are
            dictionaries keyed by districts and values are the population
            of the intersection between district and county
            
    Output: 
        PICS statistic (integer between 0 and 1): the probability that 
        two randomly chosen people from the same county are also
        in the same district.'''
    
    ## calculate number of pairs of people in the same county and same district
    
    # intitialize variable
    same_county_same_district = 0
    
    for county in counties:
        districts = counties[county]
        for dist in districts:
            # get number of people in county-district intersection
            shared_pop = districts[dist]
            # update number of pairs in same county and same district
            new_pairs = (shared_pop * (shared_pop - 1)) / 2
            same_county_same_district = same_county_same_district + new_pairs
            
    ## calculate number of pairs of people in the same county 
    ## A THOUGHT: DO THIS DIRECTLY?? SHOULD GET SAME ANSWER IF MY CODE IS GOOD
    
    # intitialize variable
    same_county = 0
    
    for county in counties:
        county_pop = 0
        districts = counties[county]
        # get number of people in county
        for dist in districts:
            county_pop = county_pop + districts[dist]
            # update number of pairs in same county
            new_pairs = (county_pop * (county_pop - 1)) / 2
            same_county = same_county + new_pairs
            
    ## calculate and return PICS
    PICS = same_county_same_district / same_county
    return PICS
        
    