# -*- coding: utf-8 -*-
"""
Created on Thu Dec 18, 2025

@author: iheijink

This function rearranges the 2D electrode overview to create more whitespace in 
electrodes_df if multiple categories appear at one stimulation pair to prevent overlapping.

Input: 
    stimulations_df: a dataframe with the processed annotations (output from estimapp_process_annotations)
    
    electrodes_df: a dataframe with the 2D configuration of patient specific electrodes.
    
Output:
    topo: a dictionary containing the x and y coordinates of the electrodes (length and order equals the number of channels)
        with extra white space if multiple categories are present at one stimpair.
        
    channel: a list containing the channel name and number (length and order matches topo dictionary)
"""
import numpy as np
import pandas as pd

from functions.estimapp_localize_electrode_positions import estimapp_localize_electrode_positions

def estimapp_rearrange_electrodescheme(stimulations_df, electrodes_df):
    # Localize electrodes in grid
    topo, channel = estimapp_localize_electrode_positions(electrodes_df)
    
    nr_of_categories = stimulations_df['Category'].str.len()
    idx_multiple_categories = nr_of_categories[nr_of_categories > 2].index
    for idx in idx_multiple_categories:
        elec1 = stimulations_df["Electrode 1"].loc[idx]
        elec2 = stimulations_df["Electrode 2"].loc[idx]
        
        idx_channel1 = channel.index(elec1)
        idx_channel2 = channel.index(elec2)
        
        nr_of_extra_lines = nr_of_categories[idx] - 2
        check_column_x = topo['x'][idx_channel1] - nr_of_extra_lines
        check_row_y = topo['y'][idx_channel1] - nr_of_extra_lines 
        if topo['x'][idx_channel1] == topo['x'][idx_channel2] and check_column_x >= 0 and electrodes_df.loc[check_column_x].notna().any():
            nan_columns = pd.DataFrame(np.nan, index=electrodes_df.index, columns=[f"nan_col_{i}" for i in range(nr_of_extra_lines)])
            pos = topo['x'][idx_channel1]
            electrodes_df = pd.concat([electrodes_df.iloc[:,:pos], nan_columns, electrodes_df.iloc[:,pos:]], axis=1)
            topo, channel = estimapp_localize_electrode_positions(electrodes_df) # update location of electrodes (topo and channel)()
      
        elif topo['y'][idx_channel1] == topo['y'][idx_channel2] and check_row_y >=0 and electrodes_df.loc[check_row_y].notna().any():
            nan_rows = pd.DataFrame(np.nan, index=range(nr_of_extra_lines), columns=electrodes_df.columns)
            pos = topo['y'][idx_channel1]
            electrodes_df = pd.concat([electrodes_df.iloc[:pos], nan_rows, electrodes_df.iloc[pos:]]).reset_index(drop=True)
            topo, channel = estimapp_localize_electrode_positions(electrodes_df) # update location of electrodes (topo and channel)
            
    return topo, channel