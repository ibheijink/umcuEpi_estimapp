# -*- coding: utf-8 -*-
"""
Created on Wed Jun  4, 2025
@author: iheijink

This function generates a 2D projection of clinical symptom categories on the electrode overview.

Input:
    electrodes_df: a dataframe with the 2D configuration of patient specific electrodes. 
        
    stimulations_df: a dataframe with the processed annotations (output from estimapp_process_annotations)
    
Output:
    fig: a plotly figure with the 2D projection of clinical symptom categories on the electrode overview.
"""

import numpy as np
import matplotlib
matplotlib.use('agg')
import re
import plotly.express as px
import plotly.io as pio


#from estimapp_set_local_datapath import estimapp_set_local_datapath
from functions.estimapp_open_icon import estimapp_open_icon
from functions.estimapp_merge_stimpairs import estimapp_merge_stimpairs
from functions.estimapp_rearrange_electrodescheme import estimapp_rearrange_electrodescheme

pio.renderers.default = 'browser'

def estimapp_generate_plot(electrodes_df, stimulations_df):
    #%% Filter unique categories per stimpair and return stimulations_df_merged
    stimulations_df, stimulations_df_merged = estimapp_merge_stimpairs(stimulations_df)

    # Create more whitespace in electrodes_df if multiple categories
    topo, channel = estimapp_rearrange_electrodescheme(stimulations_df_merged, electrodes_df)
        
    # Get the electrode names
    channel_name = [re.match(r'[A-Za-z]+', ch).group() for ch in channel]
    
    # Get the unique channel positions and the repetitions
    channel_name_unique = np.unique(channel_name, return_inverse=True)
    
    # Get the electrode numbers
    channel_number = [ch[-2:] for ch in channel]
    channel_indices_01 = [i for i, x in enumerate(channel_number) if x == '01']
    
    #%% Create Plotly figure
    fig = px.scatter(x=topo['x'], y=topo['y'], width=800, height=1000)
    fig.update_yaxes(autorange="reversed")
    fig.update_yaxes(visible=False, showticklabels=False, scaleanchor='x', scaleratio=1)
    fig.update_xaxes(visible=False, showticklabels=False)
    fig.update_traces(marker=dict(size=30, symbol='square-open', line=dict(width=2, color='DarkSlateGrey')), 
                      selector=dict(mode='markers'), mode='markers+text', text=channel_number, hoverinfo='skip', hovertemplate=None)
    fig.update_layout(
        title={'y':0.95, 'x':0.5,'xanchor':'center', 'yanchor':'top'}, paper_bgcolor="rgb(243,250,255)")
    
    # Plot the channel names according to the placement orientation
    for p in range(len(channel_indices_01)):
        topo_px = topo['x'][channel_indices_01[p]]
        topo_py = topo['y'][channel_indices_01[p]]
    
        if channel_indices_01[p] > 0 and channel_name[channel_indices_01[p]] == channel_name[channel_indices_01[p]-1]: # right to left
            fig.add_annotation(x=topo_px+1, y=topo_py, text=channel_name[channel_indices_01[p]], showarrow=False)
            topo['direction'][channel_indices_01[p]] = 'RtoL' # electrode direction
    
        elif channel_indices_01[p] < len(channel_name)-1 and channel_name[channel_indices_01[p]] == channel_name[channel_indices_01[p]+1]: # left to right
            fig.add_annotation(x=topo_px-1, y=topo_py, text=channel_name[channel_indices_01[p]], showarrow=False)
            topo['direction'][channel_indices_01[p]] = 'LtoR'
    
        elif topo_py-1 in topo['y'] and topo_py+1 not in topo['y']: # bottom to top
            fig.add_annotation(x=topo_px, y=topo_py+0.8, text=channel_name[channel_indices_01[p]], showarrow=False)
            topo['direction'][channel_indices_01[p]] = 'BtoT'
    
        elif topo_py+1 in topo['y'] and topo_py-1 not in topo['y']: # top to bottom
            fig.add_annotation(x=topo_px, y=topo_py-0.8, text=channel_name[channel_indices_01[p]], showarrow=False)
            topo['direction'][channel_indices_01[p]] = 'TtoB'
    
        else:
            print("WARNING: channel ", channel[channel_indices_01[p]], " cannot be localized correctly")
    del p, topo_px, topo_py
    
    # Add electrode orientation to all electrode contacts in topo dictionary
    for idx in channel_indices_01:
        current_direction = topo['direction'][idx]
        indexes = [i for i, val in enumerate(channel_name) if val == channel_name[idx]]
        for ii in indexes:
            topo['direction'][ii] = current_direction
            
    
    #%% Project symptoms  
    # Load icons
    icon_size = 0.005
    list_topo_x_icon = []
    list_topo_y_icon = []
    list_icons = []
  
    # calculate coordinates of icons
    for stim in stimulations_df_merged.index: 
        topo_idx_elec1 = channel.index(stimulations_df_merged["Electrode 1"][stim]) 
        topo_idx_elec2 = channel.index(stimulations_df_merged["Electrode 2"][stim]) 
        
        categories = stimulations_df_merged["Category"].loc[stim] # list
        count_per_stim = 0
        
        for cat in categories:
            # Change cat ? and ! to load icon
            if cat == '?':
                cat = 'questionmark'
            elif cat == '!':
                cat = 'exclamationmark'
                
            # Check direction of electrodes, calculate coordinates of icon
            if topo['direction'][topo_idx_elec1] == topo['direction'][topo_idx_elec2] and \
                (topo['direction'][topo_idx_elec1] == 'LtoR' or topo['direction'][topo_idx_elec1] == 'RtoL'):
                    #horizontal
                    list_topo_x_icon.append((topo["x"][topo_idx_elec1] + topo["x"][topo_idx_elec2]) / 2 - 0.5)
                    list_topo_y_icon.append(topo["y"][topo_idx_elec1] - 0 - 1*count_per_stim)
            elif topo['direction'][topo_idx_elec1] == topo['direction'][topo_idx_elec2] and \
                 (topo['direction'][topo_idx_elec1] == 'BtoT' or topo['direction'][topo_idx_elec1] == 'TtoB'):
                    # vertical
                    list_topo_x_icon.append(topo["x"][topo_idx_elec1] - 0 - 1*count_per_stim)
                    list_topo_y_icon.append((topo["y"][topo_idx_elec1] + topo["y"][topo_idx_elec2]) / 2 - 0.5)
            else:
                print("Stimulated electrodes are in different directions, check if stimulation pair and direction is correct.")
                            
            current_icon, _ = estimapp_open_icon(cat) #png
            list_icons.append(current_icon)
            count_per_stim += 1   

    if 'current_icon' in locals():
        width, height = current_icon.size
        scaled_width = width * icon_size
        scaled_height = height * icon_size              
                
    list_images = []
    
    for i in range(len(list_icons)):  # Loop over multiple icons
        list_images.append(dict(
            source = list_icons[i],  
            x = list_topo_x_icon[i],
            y = list_topo_y_icon[i],
            xref = 'x',
            yref = 'y',
            sizex = scaled_width,
            sizey = scaled_height,
            xanchor = 'left',
            yanchor = 'top',
            sizing = 'stretch',
            opacity = 1.0,
            layer = 'above'
        ))
    
    fig.update_layout(images=list_images)
    return fig
    
