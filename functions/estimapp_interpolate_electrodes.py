# -*- coding: utf-8 -*-
"""
Created on Wed Jul 16, 2025

@author: iheijink

This function interpolates for every electrode row evenly spaced points between 
    entry (X1,Y1,Z1) and target (X2,Y2,Z2), and return all as individual rows in 
    a flat DataFrame. Includes entry and target as separate rows.

Input:
    electrode_coordinates: a dataframe with the patient specific electrode names,
        number of channels, and entry and target coordinates of the implanted electrodes.
        
    electrode_distance: the distance in mm between electrode contacts. For Dixi electrodes
        the distance is 3.5mm. Default = 3.5
        
Output:
    interpolated_electrodes: a dataframe with the interpolated electrode coordinates
"""

import pandas as pd
import numpy as np

def estimapp_interpolate_electrodes(electrode_coordinates, electrode_distance=3.5):
    results = []

    for _, row in electrode_coordinates.iterrows():
        name = row['electrode_name']
        n_channels = int(row['nr_of_channels'])
        entry = np.array([row['entry_x'], row['entry_y'], row['entry_z']], dtype=float) # highest channel number
        target = np.array([row['target_x'], row['target_y'], row['target_z']], dtype=float) # channel number 1 (deepest)

        # Generate n_channels points between target and entry
        vec = entry - target
        dist = np.linalg.norm(vec)
        direction = vec / dist
        
        for n in range(n_channels):
            point = target + n * electrode_distance * direction
            channel_name = f"{name}{n+1:02d}" # combine electrode name and channel number, add 0 for channel 1-9
            results.append({
                'Electrode': channel_name,
                'X': point[0],
                'Y': point[1],
                'Z': point[2]
            })
    
    interpolated_electrodes = pd.DataFrame(results)
    return interpolated_electrodes