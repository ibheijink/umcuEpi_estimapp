# -*- coding: utf-8 -*-
"""
Created on Wed Jul  9, 2025

@author: iheijink

This function generates a projection of the implanted electrodes and clinical symptom categories on the 3D brain rendering.

Input:
    mesh_loaded: the decoded 3D PLY object containing the brain rendering.
    
    electrode_coordinates: a dataframe with the patient specific electrode names,
        number of channels, and entry and target coordinates of the implanted electrodes.
        
    stimulations_df: a dataframe with the processed annotations (output from estimapp_process_annotations)
    
    opacity: the opacity of the 3D plot, can be tuned by the end-user. Default = 0.8
    
    flip_mode: the mode to flip the brain rendering. Default = "xy"
    
Output:
    fig: a plotly figure with the 3D projection of clinical symptom categories on the electrodes implanted in the brain.
"""
import plotly.graph_objs as go
import numpy as np

from functions.estimapp_interpolate_electrodes import estimapp_interpolate_electrodes

def estimapp_generate_3d_plot(mesh_loaded, electrode_coordinates, stimulations_df, opacity=0.8, flip_mode="xy"):
    """
    ply_mesh: object with .vertices (N,3) and .faces (M,3) or a (verts, faces) tuple
    flip_mode: "none" | "x" | "y" | "z" | "xy" | "xz" | "yz" | "xyz"
    """
    # Get vertices and face indices
    vertices = mesh_loaded.vertices
    faces = mesh_loaded.faces
    
    vertices = vertices.copy()  # don't mutate original
    # Fix orientation (common case: flip X and Y)
    if "x" in flip_mode:
        vertices[:, 0] *= -1.0
    if "y" in flip_mode:
        vertices[:, 1] *= -1.0
    if "z" in flip_mode:
        vertices[:, 2] *= -1.0
    
    # Split into x, y, z
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
    i, j, k = faces[:, 0], faces[:, 1], faces[:, 2]
    
    fig = go.Figure(data=[
        go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k,
            color='mistyrose', opacity=opacity, name="Brain Surface", hovertemplate="<extra><extra></extra>")
    ])
    
    # Calculate electrode coordinates
    electrode_coordinates_interpolated = estimapp_interpolate_electrodes(electrode_coordinates)
    
    # Electrode labels
    text_labels=[""]*len(electrode_coordinates_interpolated)
    contacts01 = electrode_coordinates_interpolated['Electrode'].str.endswith('01')
    idx_contacts_01 = electrode_coordinates_interpolated.index[contacts01].to_numpy() # first contact point
    idx_contacts_last = idx_contacts_01 - 1 # last contact point
    idx_contacts_last[0] = len(electrode_coordinates_interpolated)-1 # replace -1 with highest index
    idx_labels = np.concatenate((idx_contacts_01, idx_contacts_last))
    for idx in idx_labels:
        elec = electrode_coordinates_interpolated['Electrode'][idx]
        text_labels[idx] = elec
       
    hover_labels = electrode_coordinates_interpolated['Electrode']
    print("hover labels", hover_labels)
    
    # Plot electrode coordinates
    fig.add_trace(go.Scatter3d(
        x=electrode_coordinates_interpolated['X'],
        y=electrode_coordinates_interpolated['Y'],
        z=electrode_coordinates_interpolated['Z'],
        mode="markers+text",
        marker=dict(size=3, color="rgb(147,149,152)"),
        text=text_labels,
        hovertext=hover_labels,
        hovertemplate="%{hovertext}<extra></extra>",
        customdata=hover_labels,
        showlegend=False
        
    ))
    fig.update_layout(scene_camera=dict(up=dict(x=0, y=0, z=1),), scene_dragmode='turntable', hovermode='closest',
                      scene = dict(xaxis = dict(showgrid = False, showbackground=False, showticklabels = False, showline=False, zeroline=False, showspikes=False),  
                                   yaxis = dict(showgrid = False, showbackground=False, showticklabels = False, showline=False, zeroline=False, showspikes=False), 
                                   zaxis = dict(showgrid = False, showbackground=False, showticklabels = False, showline=False, zeroline=False, showspikes=False))) 
  
    # Color map
    color_map = {"motor":"rgb(237,28,36)", "elementary motor":"rgb(237,28,36)", "complex motor":"rgb(159,29,32)", 
                 "language":"rgb(0,166,81)", "visual":"rgb(0,114,188)", "emotional":"rgb(247,148,29)",
                 "autonomic":"rgb(143,83,161)", "auditory":"rgb(0,174,239)","cognitive":"rgb(144,208,180)",
                 "vestibular":"rgb(239,154,192)","olfactory or gustatory":"rgb(166,117,79)","other":"rgb(147,149,152)",
                 "somatosensory":"rgb(254,225,15)", "after discharge":"rgb(255,255,255)", "patient in doubt":"rgb(147,149,152)",
                 "pay attention":"rgb(236,0,140)", "seizure":"rgb(35,31,32)", "recognizable":"rgb(255,0,0)", "not recognizable":"rgb(255,0,0)"}
    sizes = list(range(5, 5 + 2*len(color_map), 4)) # sizes of the color dots to show multiple categories
  
    for stim in stimulations_df.index:
        if isinstance(stimulations_df["Category"].loc[stim], list): # category annotated
            elec1 = stimulations_df["Electrode 1"].loc[stim]
            elec2 = stimulations_df["Electrode 2"].loc[stim]

            topo_elec1 = electrode_coordinates_interpolated.loc[
                electrode_coordinates_interpolated["Electrode"] == elec1, ["X", "Y", "Z"]]
            topo_elec2 = electrode_coordinates_interpolated.loc[
                electrode_coordinates_interpolated["Electrode"] == elec2, ["X", "Y", "Z"]]
            
            categories = stimulations_df["Category"].loc[stim] # list
            size_count = len(categories) - 1
            
            # Plot concentric markers for electrodes with multiple categories
            for cat in categories:

                fig.add_trace(go.Scatter3d(
                    x=topo_elec1['X'], y=topo_elec1['Y'], z=topo_elec1['Z'],
                    mode="markers+text",
                    text=elec1,
                    marker=dict(
                        size=sizes[size_count],
                        color=color_map[cat],
                        opacity=1.0,
                        line=dict(width=0)  # remove outline
                    ),
                    name=cat,
                    customdata = [[elec1, cat]],
                    hovertemplate="%{customdata[0]}<extra>%{customdata[1]}</extra>",
                    showlegend=False  # avoid duplicate legend entries
                ))
                fig.add_trace(go.Scatter3d(
                    x=topo_elec2['X'], y=topo_elec2['Y'], z=topo_elec2['Z'],
                    mode="markers+text",
                    text=elec2,
                    marker=dict(
                        size=sizes[size_count],
                        color=color_map[cat],
                        opacity=1.0,
                        line=dict(width=0)  # remove outline
                    ),
                    name=cat,
                    customdata = [[elec2, cat]],
                    hovertemplate="%{customdata[0]}<extra>%{customdata[1]}</extra>",
                    showlegend=False  # avoid duplicate legend entries
                ))
                size_count -= 1
                fig.update_layout(hovermode='closest')
                    
    return fig
