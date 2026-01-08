# -*- coding: utf-8 -*-
"""
Created on Thu Dec 18, 2025
@author: iheijink

This function creates a dataframe with unique stimulation pairs and merged categories of evoked clinical symptoms.

Input:
    stimulations_df: The dataframe contains the stimulated electrodes, the index in the annotations dataframe,
        the category of evoked clinical symptoms, free text annotations after a stimulation pair,
        and the stimulation type.
    
Output:
    stimulations_df: The updated dataframe contains the stimulated electrodes, the index in the annotations dataframe,
        the category of evoked clinical symptoms, free text annotations after a stimulation pair,
        and the stimulation type.
    
    stimulations_df_merged: The dataframe contains the stimulated electrodes, the index in the annotations dataframe,
        the category of evoked clinical symptoms, free text annotations after a stimulation pair,
        and the stimulation type. Each stimpair appears once and all evoked categories are merged per stimpair.
"""
import pandas as pd

def estimapp_merge_stimpairs(stimulations_df):
    list_index = []
    list_elec1 = []
    list_elec2 = []
    list_categories = []    
    
    for stim in stimulations_df.index:
        elec1 = stimulations_df["Electrode 1"].loc[stim]
        elec2 = stimulations_df["Electrode 2"].loc[stim]
    
        categories = stimulations_df["Category"].loc[stim]        
            
        if isinstance(categories, list):
            list_index.append(stim)
            list_elec1.append(elec1)
            list_elec2.append(elec2)
            list_categories.append(categories)
            
    stimulations_df = pd.DataFrame({'Electrode 1': list_elec1, 'Electrode 2': list_elec2, 'Category':list_categories}, index=list_index)
    del elec1, elec2, categories, list_index, list_elec1, list_elec2, list_categories
    
    from itertools import chain
    stimulations_df_merged = stimulations_df.groupby(['Electrode 1','Electrode 2']).agg({
        'Category': lambda x: list(chain.from_iterable(x)),
    }).reset_index()
    index = (stimulations_df.groupby(['Electrode 1','Electrode 2']).apply(lambda x: x.index[0]))
    stimulations_df_merged.index = index.values
    
    stimulations_df_merged['Category'] = stimulations_df_merged['Category'].apply(lambda lst: list(dict.fromkeys(lst)))
    
    return stimulations_df, stimulations_df_merged