# -*- coding: utf-8 -*-
"""
Created on Tue May  6, 2025
@author: iheijink

This function creates a dictionary containing all xy-coordinates of the electrodes

Input:
    electrodes: a dataframe read from the excel electrodes containing the electrode scheme
    
Output:
    topo: a dictionary containing the x and y coordinates of the electrodes (length and order equals the number of channels)
    
    channel: a list containing the channel name and number (length and order matches topo dictionary)
"""
import numpy as np
import pandas as pd

def estimapp_localize_electrode_positions(electrodes):
    topo = {}
    count = 0
    x = []
    y = []
    channel = []
    
    for nRow in range(electrodes.shape[0]):
        for nCol in range(electrodes.shape[1]):
            if pd.notna(electrodes.iat[nRow, nCol]):
                #letter = np.array(list(filter(str.isalpha, electrodes.iat[nRow, nCol])))
                number = np.array(list(filter(str.isdigit, electrodes.iat[nRow, nCol])))
                test1 = electrodes.iat[nRow, nCol]
                test2 = electrodes.iat[nRow, nCol][0:-1] + '0' + electrodes.iat[nRow, nCol][-1:]
    
                if len(number) == 2:
                    channel.append(test1)
                    y.append(nRow)
                    x.append(nCol)
                    count += 1
                elif len(number) == 1:
                    channel.append(test2)
                    y.append(nRow)
                    x.append(nCol)
                    count += 1
                elif len(number) >2:
                    print(f'Warning: Electrode {test1} or {test2} is not found')
    
    # Place the locations of the electrodes in the structure
    topo['x'] = np.array(x)
    topo['y'] = np.array(y)
    topo['direction'] = [''] *len(x)
    
    return topo, channel