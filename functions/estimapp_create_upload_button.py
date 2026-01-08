# -*- coding: utf-8 -*-
"""
Created on Fri Dec 19 15:11:53 2025

@author: iheijink

This function creates an upload button. 

Input: 
    upload_id: the id used for the upload button
    
    loaded_id: the id used for the loaded file
    
    button_text: the text shown in the button
    
    tooltip_text: the hovertext shown in the information button
    
    example_link: the link to the example data at DataVerseNL
    
    multiple: if it is allowed to upload multiple files. Default = False
    
Output:
    upload button: a button that contains button_text. If you click on the button,
        you can upload one or multiple files from your local disk.
    
    information button: a button for more information about the upload button. 
        If you hover over the button, you see the tooltip_text and example_link.
    
"""
from dash import dcc, html
import dash_mantine_components as dmc

def estimapp_create_upload_button(upload_id, loaded_id, button_text, tooltip_text, example_link, multiple=False):
    return dmc.Group(
        [
            dcc.Upload(
                id=upload_id,
                children=dmc.Button(
                    button_text,
                    variant="outline",
                    color="blue",
                    styles={"root": {"backgroundColor": "white"}},
                ),
                multiple=multiple,
            ),     
            
            dmc.HoverCard(
                      withArrow=True,
                      width=300,
                      children=[
                          dmc.HoverCardTarget(
                              children = dmc.ActionIcon(
                                  children = "i",
                                  variant="outline",
                                  radius="xl",
                                  size="sm",
                                  color="blue",)),
                          dmc.HoverCardDropdown(
                              children = dmc.Text([tooltip_text, example_link], size="sm")),
                      ],),
            
            html.Br(),
            html.Div(id=loaded_id, style={"marginBottom": 10}),
        ],
        align="center",
        gap="xs",
    )