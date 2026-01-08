# -*- coding: utf-8 -*-
"""
Created on Tue May  6 
@author: iheijink

This function defines the stimulation period based on Stim_on; and Stim_off; annotations

Input: 
    annotations_df: a dataframe containing all annotations during stimulation
    
    column_name: the column name in the annotations files where the notes are located.
        Default = 'Comment'
    
Output:
    stimPeriod: a dataframe containing all Stim_on; and Stim_off; annotations including annotation index
"""
import pandas as pd

def estimapp_define_stimulation_period(annotations_df, column_name):
    print('function define stimulation period')
    print(type(annotations_df))
    print("Length of annotations_df:", len(annotations_df))
    
    stimPeriod = annotations_df[annotations_df[column_name].str.contains("Stim_on", na=False)]
    
    stimPeriod = pd.concat([stimPeriod, annotations_df[annotations_df[column_name].str.contains("Stim_off", na=False)]])
    stimPeriod = stimPeriod.sort_index()
       
    return stimPeriod