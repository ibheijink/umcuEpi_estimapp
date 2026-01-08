# -*- coding: utf-8 -*-
"""
Created on Tue May 6, 2025

@author: iheijink

This function creates a dataframe stimulations overview. 

Input: 
    annotations_df: a dataframe containing all annotations during stimulation
    
    categories: a dictionary containing all categories of evoked clinical symptoms
        and the annotation index where this symptom was present
    
    stimPeriod: a dataframe containing all Stim_on; and Stim_off; annotations including annotation index
    
    stimTypes_list: a list of all stimulation type to be included
    
Output:
    stimulations_df: The dataframe contains the stimulated electrodes, the index in the annotations dataframe,
        the category of evoked clinical symptoms, free text annotations after a stimulation pair,
        and the stimulation type.
    
    filtered_stimulations_df: The dataframe stimulations_df is filtered to only show stimulations of stimType 
        in stimTypes_list, only when Category or Free text is filled in. This df is used to show the table 
        in the app.

    categories_abbreviations: A dictionary with key the abbreviation of the category 
        used in the annotations and value the full name of the category.
"""
import pandas as pd
import re
    
def estimapp_create_stimulations_overview(annotations_df, categories, stimPeriod, column_name):

    stimulations_df = pd.DataFrame(columns=['Electrode 1', 'Electrode 2', 'AnnotationIndex', 'Category', 'Free text', 'Stim type'])
    pattern = r'([a-zA-Z]{1,3})(\d{1,2})(?:\s*-?\s*)\1(\d{1,2})' # group 1 (1-3 letters) + group 2 (1 or 2 digits) + optional space + group 1 + group 3 (1 or 2 digits)
    count_stimulations = 0
    for i in range(len(annotations_df)):
        matches = re.findall(pattern, annotations_df.loc[i,column_name])
            
        # Filter only where the digits are different
        filtered_matches = [f"{m[0]}{m[1]} {m[0]}{m[2]}" for m in matches if m[1] != m[2]]
        split_matches = [match.split() for match in filtered_matches]

        if split_matches:
            if int(matches[0][1]) > int(matches[0][2]): # First electrode number is lower than second, e.g. AR02 - AR01
            #     # Switch order to low-high, e.g. AR01 - AR02
                elec1 = split_matches[0][1]
                split_matches[0][1] = split_matches[0][0]
                split_matches[0][0] = elec1
            stimulations_df = pd.concat([stimulations_df, pd.DataFrame(split_matches, columns=['Electrode 1', 'Electrode 2'])],
                                        ignore_index=True)
            stimulations_df.loc[count_stimulations, 'AnnotationIndex'] = i
            count_stimulations += 1
    
    del matches, filtered_matches, split_matches, count_stimulations, i, pattern # housekeeping

    for idx in stimulations_df.index: # 2 digits in electrode names (e.g. change AR1 to AR01)
        stimulations_df.loc[idx,"Electrode 1"] = re.sub(r'^([a-zA-Z]{1,3})(\d)$', r'\g<1>0\g<2>', stimulations_df.loc[idx,"Electrode 1"])
        stimulations_df.loc[idx,"Electrode 2"] = re.sub(r'^([a-zA-Z]{1,3})(\d)$', r'\g<1>0\g<2>', stimulations_df.loc[idx,"Electrode 2"])

    # Add stimtype, categories and free text to stimulations_df
    categories_abbreviations = {'mo':'motor', 'sm':'elementary motor', 'cm':'complex motor','la':'language', 'vest':'vestibular', 'auto':'autonomic', 
                                'aff':'affective', 'cog':'cognitive', 'sts':'somatosensory', 'vis':'visual', 
                                'audi':'auditory', 'og':'olfactory or gustatory', 'ot':'other', '?':'patient in doubt', 
                                '!':'pay attention', 'sz':'seizure', 'AD':'after discharge'}
    for cat in categories:
        if not categories[cat]:  # Skip if the list is empty
            continue
        for index in categories[cat]: # index of category annotation
            # Stimulation pair is annotated before category annotation. So look for 
            # smaller closest value in stimulation_df AnnotationIndex
            smaller_values = stimulations_df[stimulations_df["AnnotationIndex"] < index]
            smaller_closest_value = smaller_values["AnnotationIndex"].max()
            stimulations_row = stimulations_df[stimulations_df["AnnotationIndex"] == smaller_closest_value].index[0]
            current_value = stimulations_df.loc[stimulations_row,"Category"]
            cat_full = categories_abbreviations[cat] # full name
            
            # add category (current_value) to stimulations_df at row of stimulated electrodes
            if not isinstance(current_value, list) and pd.isna(current_value): 
                # If NaN or empty, set to a list with the current cat
                stimulations_df.at[stimulations_row, "Category"] = [cat_full]
            elif cat_full not in current_value:
                current_value.append(cat_full)
                stimulations_df.at[stimulations_row, "Category"] = current_value
    del cat, smaller_values, smaller_closest_value, stimulations_row, current_value, cat_full, index # housekeeping


    for period in range(0,len(stimPeriod.index),2):
        idx_stimOn = stimPeriod.index[period]
        idx_stimOff = stimPeriod.index[period + 1]
        stimType = stimPeriod.loc[stimPeriod.index[period], column_name]        
        stimType = stimType[8:]

        # Check if stimType is spelled correctly
        #if stimType not in stimTypes_list:
        #    print("stimType " + stimType + " is not in " + ' '.join(map(str, stimTypes_list)) + ". Check if annotation is spelled correctly, the annotation will be ignored.")
        stimulations_row = stimulations_df["AnnotationIndex"].between(idx_stimOn, idx_stimOff) 
        stimulations_df.loc[stimulations_row, "Stim type"] = stimType
    del period, idx_stimOn, idx_stimOff, stimType, stimulations_row
        
    indices_categories = [index for sublist in categories.values() for index in sublist]
    indices_stimulations = stimulations_df["AnnotationIndex"]
    indices_all = pd.concat([pd.Series(indices_categories), indices_stimulations, stimPeriod.index.to_series()], ignore_index=True)
    indices_freetext = [i for i in annotations_df.index if i not in set(indices_all)]

    freeText_df = annotations_df.iloc[indices_freetext]
    for index in freeText_df.index:
        # Stimulation pair is annotated before free text annotation. So look for 
        # smaller closest value in freeText_df
        smaller_values = stimulations_df[stimulations_df["AnnotationIndex"] < index]
        if smaller_values.empty:
            continue # annotation is not linked to a stimulation pair
        smaller_closest_value = smaller_values["AnnotationIndex"].max()
        stimulations_row = stimulations_df[stimulations_df["AnnotationIndex"] == smaller_closest_value].index[0]
        current_freeText = stimulations_df.loc[stimulations_row,"Free text"]
        
        current_annotation = freeText_df.at[index, column_name]
        if current_annotation == "niets":
            continue # do not show in stimulations overview
        
        if not isinstance(current_freeText, list) and pd.isna(current_freeText):
            # If NaN, set to a list with the current cat
            stimulations_df.at[stimulations_row, "Free text"] = [current_annotation]
        else:
            current_freeText.append(current_annotation)
            stimulations_df.at[stimulations_row, "Free text"] = current_freeText
            
    del index, smaller_values, smaller_closest_value, stimulations_row, current_freeText, current_annotation
    del indices_categories, indices_stimulations, indices_all, indices_freetext
    
    # Filter table: only stimulations of stimType in stimTypes_list; 
    # only when Category or Free text is filled in
    filtered_stimulations_df = stimulations_df[
        (stimulations_df['Category'].notna() | stimulations_df['Free text'].notna())] #&
    #    (stimulations_df['Stim type'].isin(stimTypes_list))]
    
    filtered_stimulations_df = filtered_stimulations_df.fillna("")
    
    return stimulations_df, filtered_stimulations_df, categories_abbreviations