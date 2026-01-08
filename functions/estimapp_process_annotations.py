# -*- coding: utf-8 -*-
"""
Created on Wed May 28, 2025
@author: iheijink

This function processes a list of excel files containing EEG annotations and 
creates a dataframe stimulations_df containing all neccessary information from 
the annotations in a structured way.

Input:
    annotations_df: a dataframe containing all EEG annotations. 
    
    column_name: the column that contains the notes. Default = 'Comment'
        
Output:
    stimulations_df: The dataframe contains the stimulated electrodes, the index in the annotations dataframe,
        the category of evoked clinical symptoms, free text annotations after a stimulation pair,
        and the stimulation type.
        
    filtered_stimulations_df: The dataframe stimulations_df is filtered to only show stimulations of stimType 
        in stimTypes_list, only when Category or Free text is filled in. This df is used to show the table 
        in the app.

    categories: A dictionary with key the abbreviation of the category 
        used in the annotations and value the full name of the category.
"""
import os
import pandas as pd
import sys

current_file = os.path.abspath(__file__)
scripts_dir = os.path.dirname(current_file)
python_dir = os.path.abspath(os.path.join(scripts_dir, '..'))
sys.path.append(python_dir)

from functions.estimapp_localize_annotated_categories import estimapp_localize_annotated_categories
from functions.estimapp_define_stimulation_period import estimapp_define_stimulation_period
from functions.estimapp_create_stimulations_overview import estimapp_create_stimulations_overview

def estimapp_process_annotations(annotations_df, column_name="Comment"):
    print("process annotations")    
    print("define stimulation period")
    
    # Define stimulation period
    stimPeriod = estimapp_define_stimulation_period(annotations_df, column_name)
    print("remove annotations outside stimulation period")
    print("stimPeriod", stimPeriod.shape, stimPeriod[column_name])
    
    # Remove annotations outside stimulation period
    filtered_annotations_df = pd.DataFrame()
    if all(stimPeriod.iloc[::2, ::2][column_name].str.contains("Stim_on")) and len(stimPeriod) %2 == 0: 
        # Stim_on and off annotations complete
        for period in range(0,len(stimPeriod.index),2):
            idx_stimOn = stimPeriod.index[period]
            idx_stimOff = stimPeriod.index[period + 1]
            annotations_currentPeriod = annotations_df[idx_stimOn:idx_stimOff+1] 
            filtered_annotations_df = pd.concat([filtered_annotations_df, annotations_currentPeriod], ignore_index=True)
    else: 
        raise ValueError("Stim_on or Stim_off annotation missing, adjust in annotations overview Excel")
    del idx_stimOn, idx_stimOff, annotations_currentPeriod, period, annotations_df, stimPeriod
    
    print("Filtered annotations", type(filtered_annotations_df), filtered_annotations_df.shape)
    stimPeriod = estimapp_define_stimulation_period(filtered_annotations_df, column_name)
         
    annotated_categories = estimapp_localize_annotated_categories(filtered_annotations_df, column_name)
    print("Annotated categories are:", annotated_categories)
    
    # Create stimulations_df which contains all stimulations
    #stimTypes_list = ["CHOCS1", "CHOCS2", "TRENI"]
    #print("Stimulation types inluded in analysis are: ", stimTypes_list)
    
    stimulations_df, filtered_stimulations_df, categories = estimapp_create_stimulations_overview(filtered_annotations_df, annotated_categories, stimPeriod, column_name)
    
    return stimulations_df, filtered_stimulations_df, categories