# -*- coding: utf-8 -*-
"""
Created on Fri Jun 20, 2025

@author: iheijink

This function generates a Dash table with all the categories of clinical symptoms, 
free text annotations, and stimulation type per stimulation pair.

Input:
    stimulations_df: a dataframe containing all neccessary information from the 
            annotations in a structured way. 
            Columns: Electrode 1, Electrode 2, AnnotationIndex, Category, Free text, Stim type
            
    sort_by_column: the column to be sorted. Default = "Electrode 1"
    
Output:
    formatted_df: a dataframe representing the table shown in the app. 
    
    visible_columns: the columns of formatted_df. Default = ['Electrode 1', 'Electrode 2',
            'Category', 'Free text', 'Stim type']
"""
import pandas as pd

def estimapp_generate_table(stimulations_df, sort_by_column="Electrode 1"):

    def format_cell(col, cell):
        if col == "Free text":
            # Handle list or stringified list
            if isinstance(cell, list):
                return "; ".join(map(str, cell))
            elif isinstance(cell, str) and cell.startswith("[") and cell.endswith("]"):
                try:
                    parsed = eval(cell)
                    if isinstance(parsed, list):
                        return ", ".join(map(str, parsed))
                except:
                    pass  # fallback to raw string
        if col == "Category":
            # Handle list or stringified list
            if isinstance(cell, list):
                return "; ".join(map(str, cell))
        return str(cell)
    
    visible_columns = [col for col in stimulations_df.columns if col != "AnnotationIndex"]
    formatted_df = pd.DataFrame([{col: format_cell(col, row[col]) for col in visible_columns}
        for _, row in stimulations_df.iterrows()])
    if sort_by_column in formatted_df.columns:
      formatted_df.sort_values(by=sort_by_column, inplace=True, key=lambda col: col.str.lower() if col.dtype == "object" else col)

    return formatted_df, visible_columns