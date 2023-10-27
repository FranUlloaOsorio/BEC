# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 09:12:39 2023

@author: faull
"""

import os
params=([0,0],[50,0],[300,0],[0,75],[50,75],[300,75])

for param in params:
    print(param[0],param[1])
    os.system("python Main_Exclusive.py 150 "+str(param[0])+" "+str(param[1]) )
# 