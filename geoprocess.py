# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 14:53:06 2019

@author: Jacob
"""

import geopandas
import sys

print(sys.argv[1])

with open('testOut.txt', 'w') as f:
    f.writelines(sys.argv[1])