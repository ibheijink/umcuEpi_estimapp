# -*- coding: utf-8 -*-
"""
Created on Tue May  6, 2025
@author: iheijink

This function localizes the annotated abbreviation of the categories of evoked clinical symptoms
and shows the indices of the annotation per category

Input: 
    annotations_df: a dataframe containing all annotations during stimulation
    
Output:
    categories: a dictionary containing all categories of evoked clinical symptoms

"""

def estimapp_localize_annotated_categories(annotations_df, column_name):
    abbreviations = ['mo', 'sm', 'cm', 'la', 'vest', 'auto', 'aff', 'cog', 'sts', 'vis', 'audi', 'og', 'ot', '?', '!', 'sz', 'AD']
    categories = {}

    for abbr in abbreviations:
        
        indices = annotations_df[annotations_df[column_name].fillna('').str.casefold() == abbr.casefold()].index.tolist()

        categories[abbr] = indices
        
    return categories
