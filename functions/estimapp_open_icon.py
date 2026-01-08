# -*- coding: utf-8 -*-
"""
Created on Tue May 20, 2025
@author: iheijink

This function opens an icon from the relative path

Input:
    cat: the category of clinical symptoms
    
Output:
    icon: resized png of the icon of cat
    icon_array: the icon as a numpy array
"""
from PIL import Image
import os
import os.path as op
import base64

def estimapp_open_icon(cat):
    RepoPath = op.abspath(op.join(__file__, op.pardir, op.pardir))
    icon_folder = os.path.join(RepoPath, 'icons', cat + '.png')
    
    icon = Image.open(icon_folder).resize((200,200)) # Open the image and resize
    
    with open(icon_folder, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode()
    return icon, f"data:image/png;base64,{encoded}"