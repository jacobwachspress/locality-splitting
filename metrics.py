# -*- coding: utf-8 -*-
"""
Created on Sat Apr  6 15:13:31 2019

@author: Jacob
"""
import numpy as np

def threshold(pops, threshold=50):
    ''' Remove elements of a dictionary with values below a certain threshold.
    
    Arguments: 
        pops: dictionary whose keys are ordered pairs (county, district)
            and whose values are the populations within these intersections.
        threshold: vlaue below which we filter out
            
    Output: 
        thresholded pops dictionary
    '''
    keys_to_remove = [key for key in pops if pops[key] < threshold]
    for key in keys_to_remove:
        pops.pop(key, None)
    return pops
        
def split_counties(pops):
    counties = set([key[0] for key in pops])
    
    split_counties = [1 for county in counties \
                      if len([key for key in pops if key[0] == county]) > 1]
    
    return sum(split_counties)

def non_empty_county_district_pairs(pops):
    return len(pops)
    
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
    
    # get number of pairs in same county and same district
    same_county_same_district = sum([i*(i-1)/2 for i in pops.values()])
    
    # get counties
    counties = set([key[0] for key in pops])
    
    # get number of pairs in same county
    county_pops = [sum([pops[key] for key in pops if key[0] == county]) \
                   for county in counties] 
    same_county = sum([i*(i-1)/2 for i in county_pops])
            
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
    
    # get size of largest intersection in each county
    county_maxes = [max([pops[key] for key in pops if key[0] == county]) \
                   for county in counties] 
    
    # calculate and return GK
    GK = sum(county_maxes) / sum(pops.values())
    return GK
    
    
def min_entropy(pops):
    ''' Calculates conditional entropy of district partition with respect to 
        county partition 
        
    Arguments: 
        pops: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.
            
    Output: 
        Reciprocal of conditional entropy, so more similar parititions
        yield a higher number'''
        
    # get counties
    counties = set([key[0] for key in pops])
    
    # compile lists to sum
    county_entropies = []
    for county in counties:
        districts = [key for key in pops if key[0] == county]
        county_size = sum([pops[key] for key in districts])
        county_entropy = sum([pops[key] * np.log2(pops[key]/county_size) \
                          for key in districts])
        county_entropies.append(county_entropy)
        
    # calcuate conditional entropy, return reciprocal
    c_entropy = (-1) * sum(county_entropies) / sum(pops.values())
    return 1/(1+c_entropy)
