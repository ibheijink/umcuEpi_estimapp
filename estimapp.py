"""
Created on Mon May 26, 2025
@author: Irene Heijink

Run this dash app to host the webpage at localhost:8050/

The app visualises the result of electrical stimulation during intracranial monitoring.

Input:
    Electrodes overview: an excel file with the patient specific electrode scheme. 
    
    Annotations: one or multiple csv files with the EEG annotations during stimulation. 
        The categories of clinical symptoms should be annotated using the correct abbreviations, 
        please find the user instructions. Column names: ['Start from:', 'Time End', 'Duration', 'Category', 'Comment']
        
    Optional, required for 3D rendering:
        
    Electrode coordinates: an excel file with the patient specific electrode names,
        number of channels, and entry and target coordinates of the implanted electrodes.
        Column names: ['electrode_name', 'nr_of_channels', 'entry_x', 'entry_y', 'entry_z', 'target_x', 'target_y', 'target_z']
        
    PLY brain rendering: a PLY file with the patient specific 3D brain rendering.
        Can be saved via EpiNav or other visualization software.
        
    Example data is available for all input data at DataVerseNL.

Output:
    2D figure: the projection of clinical symptom categories on the electrode overview.
    
    Table: category of clinical symptoms, free text annotations, and stimulation type 
        sorted per stimulated electrode pair.
        
    3D figure: the projection of clinical symptom categories on the implanted electrodes
        and brain rendering in 3D. The end-user can rotate and translate the figure and
        change the opacity.
"""

import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_mantine_components as dmc
import base64
import io
import pandas as pd
import trimesh
import csv

from functions.estimapp_process_annotations import estimapp_process_annotations
from functions.estimapp_generate_plot import estimapp_generate_plot
from functions.estimapp_generate_table import estimapp_generate_table
from functions.estimapp_generate_3d_plot import estimapp_generate_3d_plot
from functions.estimapp_create_upload_button import estimapp_create_upload_button

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "EStiMapp"
  
# Layouts
app.layout = dmc.MantineProvider(
    children=html.Div([
        dcc.Location(id="main-url", refresh=False),
        dcc.Store(id="session-data", storage_type='memory'),
        html.Div(id="warning-alert"),
        html.Div(id="page-content")],
        style={"backgroundColor":"rgb(243,250,255)"}
        )
    )

def layout_home():
    return dmc.Container(
        dmc.Stack([
        dmc.Title("EStiMapp", order=2),
        dmc.Text("A practical tool for mapping clinical symptoms evoked by electrical stimulation in intracranial EEG for epilepsy surgery", 
                 fw=500, ta="center", w="450px"),
        html.Br(),
        html.Br(),
        
        dmc.TextInput(
            id="name-input",
            label="Enter patient name or ID (optional)",
            placeholder="e.g., John Doe",
            required=False,
            style={"marginBottom": 20}),
        estimapp_create_upload_button("upload-electrodes", "upload-overview-electrodes", "Upload overview electrodes", 
                                      "xlsx file containing electrode names and ordering. Example file: ","https://doi.org/10.34894/KMT3VI"),
        estimapp_create_upload_button("upload-annotations", "upload-overview-annotations", "Upload overview annotations", 
                                      "csv file(s) containing annotations from iEEG software. Multiple files can be uploaded at once. For Micromed users: these files can be compiled automatically from a Micromed TRC using the Export Notes option in Micromed. Example files: ","https://doi.org/10.34894/KMT3VI", multiple=True),
        
        dmc.Text("Optional, required for 3D rendering:", fw=500),
        estimapp_create_upload_button("upload-coordinates", "upload-electrode-coordinates", "Upload electrode coordinates", 
                                      "xlsx file containing electrode names, number of contacts, and entry and target coordinates. Example file: ","https://doi.org/10.34894/KMT3VI"),
        estimapp_create_upload_button("upload-ply", "upload-ply-rendering", "Upload PLY brain rendering", 
                                      "ply file containing 3D brain rendering. Example file: ","https://doi.org/10.34894/KMT3VI"),

        html.Br(),
        dmc.Button("Create EStiMapp", id="submit-btn"),
        dmc.Text("EStiMapp is a visualization tool that was evaluated by the CE-committee of the UMC Utrecht and was labeled not to be a medical device. The use or reliance of any information contained on the site is solely at your own risk.", 
                 fw=300, ta="center", w="450px"),
        html.Div(id="warning-alert"),
        ], align="center", gap="sm"),size="sm")

def layout_result():
    print("layout_result is called")
    return html.Div([
        html.H3("Result Page", style={'font-family':'verdana'}),
        html.H4(id="result-name", style={'font-family':'verdana'}),
        dcc.Tabs(id="result-tabs", value="tab-2d", children=[
            dcc.Tab(label="2D visualization", value="tab-2d", 
                    style={'background':'white', 'color':'black', 'font-family':'verdana'}, 
            selected_style={'background':'blue', 'color':'white', 'font-family':'verdana'}),
            dcc.Tab(label="3D visualization", value="tab-3d", 
                    style={'background':'white', 'color': 'black', 'font-family': 'verdana'},
                    selected_style={'background':'blue', 'color':'white', 'font-family':'verdana'})]),
        html.Div(id="result-tab-content"),
        html.Br(),
        dcc.Store(id="processed-annotations"),
        dcc.Store(id="edited-processed-annotations"),
        html.Div(id="result-table") # table is outside tab
    ])

# Show uploaded file names
@app.callback(
    Output("upload-overview-electrodes", "children"),
    Input("upload-electrodes", "filename")
)
def update_electrodes(filename):
    return f"Selected: {filename}" if filename else ""

@app.callback(
    Output("upload-overview-annotations", "children"),
    Input("upload-annotations", "filename")
)
def update_annotations(filenames):
    if filenames:
        return "Selected: " + ", ".join(filenames)
    return ""

@app.callback(
    Output("upload-electrode-coordinates", "children"),
    Input("upload-coordinates", "filename")
)
def update_coordinates(filename):
    if filename:
        return f"Selected: {filename}" if filename else ""
    return ""

@app.callback(
    Output("upload-ply-rendering", "children"),
    Input("upload-ply", "filename")
)
def update_ply(filename):
    if filename:
        return f"Selected: {filename}" if filename else ""
    return ""
    
# Result page
def show_result(data):
    print("⚡ show_result called")

    name = data.get("name", "")
    electrodes = data.get("electrodes")
    annotations = data.get("annotations")
    coordinates = data.get("coordinates")
    ply = data.get("ply")
    
    def decode_excel(content):
        _, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        xls = pd.ExcelFile(io.BytesIO(decoded))
        sheet_names = xls.sheet_names
        print("sheet names", sheet_names)
        if len(sheet_names) > 1 and "sjabloon" in sheet_names:
            sheet_name = "sjabloon"
        elif len(sheet_names) > 1 and "Sheet 1" in sheet_names:
            sheet_name = "Sheet 1"
        elif len(sheet_names) > 1 and "Sheet1" in sheet_names:
            sheet_name = "Sheet1"
        elif len(sheet_names) > 1 and "elektroden" in sheet_names:
            sheet_name = "elektroden"
        elif len(sheet_names) > 1 and "Elektroden" in sheet_names:
            sheet_name = "Elektroden"
        else:
            sheet_name = 0 # Default to read first worksheet of excel file
        decoded_excel = pd.read_excel(io.BytesIO(decoded), sheet_name=sheet_name, keep_default_na=False)
        return decoded_excel

    def decode_annotations(content):
        _, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        
        annotations = pd.read_csv(io.BytesIO(decoded),
            encoding="latin1",     # handles special characters like °, é, etc.
            sep="\t",              # tab-delimited
            engine="python",       # more forgiving parser
            quoting=csv.QUOTE_NONE # <-- ignore quotes completely
        )     

        return annotations
    
    def decode_ply(content):
        _, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        mesh = trimesh.load(io.BytesIO(decoded), file_type='ply')
        return mesh

    print("decode annotations, file type:", type(annotations), type(annotations[0])) # <class 'list'> <class 'str'>
    annotations_df = pd.DataFrame()
    for file in annotations:
        decoded_annotations = decode_annotations(file)
        print("decoded annotations type", type(decoded_annotations), decoded_annotations.shape)
        print("add annotations to dataframe")
        annotations_df = pd.concat([annotations_df, decoded_annotations], ignore_index=True)

    print("decoded annotations", type(annotations_df), "size df", annotations_df.shape, annotations_df['Comment']) #decoded annotations <class 'list'> <class 'pandas.core.frame.DataFrame'>

    print('decoding electrodes')    
    decoded_electrodes = decode_excel(electrodes) # df   
    stimulations_df, processed_annotations, categories_dict = estimapp_process_annotations(annotations_df)
    
    # 3D
    coordinates_df = decode_excel(coordinates) if data.get("coordinates") else None
    mesh = decode_ply(ply) if data.get("ply") else None
    return name, decoded_electrodes, processed_annotations, categories_dict, coordinates_df, mesh
    
# Page routing
@app.callback(
    Output("page-content", "children"),
    Input("main-url", "pathname")
    )
def display_page(pathname):
    print("📍 Navigated to pathname:", pathname)
    if pathname == "/result":
        return layout_result()
    else:
        return layout_home()

# Handle submit
@app.callback(
    Output("main-url", "pathname"),
    Output("session-data", "data"),
    Output("warning-alert", "children"),
    Input("submit-btn", "n_clicks"),
    State("name-input", "value"),
    State("upload-electrodes", "contents"),
    State("upload-annotations", "contents"),
    State("upload-coordinates", "contents"),
    State("upload-ply", "contents"),
    
    prevent_initial_call=True
)
def handle_submit(n_clicks, name, electrodes, annotations, coordinates, ply):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    print("🚨 Submit clicked")
    print("  ↳ Electrodes content present:", isinstance(electrodes, str))
    print("  ↳ Annotations content list:", isinstance(annotations, list), "Length:", len(annotations) if annotations else 0)
    print("  ↳ Electrode coordinates content present:", isinstance(coordinates, str))
    print("  ↳ PLY content present:", isinstance(ply, str)) # string?
        
    missing = []
    if not electrodes or not isinstance(electrodes, str):
        missing.append("Excel electrodes")
    if not annotations or not isinstance(annotations, list) or len(annotations) == 0:
        missing.append("Annotations")

    if missing:
        return dash.no_update, dash.no_update, dmc.Alert(
            title="Missing Information",
            color="red",
            radius="md",
            children="Please provide: " + ", ".join(missing)
        )

    data = {
        "name": name or "",
        "electrodes": electrodes,
        "annotations": annotations,
        "coordinates": coordinates,
        "ply": ply # Default value if missing is None
    }
    return "/result", data, None # None is default value for Alert missing data

# Result Display
@app.callback(
    Output("result-name", "children"),
    Output("result-table", "children"),
    Output("result-tab-content", "children"),
    Output("processed-annotations", "data"),
    Input("result-tabs", "value"), 
    Input("session-data", "data"),
)
def update_result_tabs(tab, data):
    if not data:
        return "No data submitted", html.Div(), html.Div(), html.Div()
    
    name, decoded_electrodes, processed_annotations, categories_dict, coordinates_df, mesh = show_result(data)
    table, table_columns = estimapp_generate_table(processed_annotations)
    dropdown_individual_cat = set(categories_dict.values())
    dropdown_multiple_cat = set(table["Category"].unique())
    dropdown_menu = sorted(dropdown_individual_cat | dropdown_multiple_cat) # removes duplicates
    
    table_section =  html.Div([html.Label("Overview of all annotations per stimulation pair ", style={'font-family':'verdana', 'font': 'bold'}), 
            html.Div( html.Button("Download table", id="download-table-btn", style={
        "backgroundColor": "white", "border": "2px solid #228be6", "color": "#228be6", "padding": "6px 14px",
        "borderRadius": "6px", "cursor": "pointer", "fontSize": "14px",}),
            style={"display":"flex", "justifyContent":"flex-end", "marginBottom":"10px"}),
            dcc.Download(id="download-table"),
            dash_table.DataTable(id="editable-table", data=table.to_dict("records"),
            #columns=[{"name": col, "id": col} for col in table_columns],
            
            columns=[{"name": "Electrode 1", "id": "Electrode 1", "editable": False},
                      {"name": "Electrode 2", "id": "Electrode 2", "editable": False},
                      {"name": "Category", "id": "Category", "editable": True, "presentation": "dropdown"},
                      {"name": "Free text", "id": "Free text", "editable": True},
                      {"name": "Stim type", "id": "Stim type", "editable": False},
],
            dropdown = {
                "Category": {
                    "options": [{"label": v, "value": v} for v in dropdown_menu]
                }
            },
            
            sort_action="native",   # Allow user to sort columns
            filter_action="native", # Optional: Allow column filtering
            filter_options={'case':'insensitive'}, 
            row_deletable=True,
            editable=True, 
            #row_addable=True,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left"},#, "whiteSpace": "pre-line"},
            style_data={"whiteSpace": "normal", "height": "auto"}
        ),
])

    if tab == "tab-2d":
        print("Generating figure")
        fig2d = dcc.Graph(id="result-plot-2d", figure = estimapp_generate_plot(decoded_electrodes, processed_annotations))
        
        return f"{name}" if name else "No name provided", table_section, html.Div([ 
                html.Div(fig2d, 
                         style={"width": "auto", "display": "inline-block", "verticalAlign": "top", "margin": "0", "padding": "0", "backgroundColor": "rgba(0,0,0,0)"}),
                html.Img(src='/assets/Legend.png', style={'width': '400px', "margin": "0", "marginBottom": "75px", "padding": "5px", "alignSelf": "flex-end"}) ],
                style={"textAlign": "left", "whiteSpace": "nowrap", "display": "flex", "alignItems": "flex-end", "justifyContent": "flex-start"}), processed_annotations.to_json(date_format="iso", orient="split")
    elif tab == "tab-3d" and mesh:
        fig3d = estimapp_generate_3d_plot(mesh, coordinates_df, processed_annotations)
        return f"{name}" if name else "No name provided", table_section, html.Div([
                html.Div([
                    dcc.Graph(id="result-plot-3d", figure=fig3d, clear_on_unhover=True, style={"width":"1200px","height":"800px"}),
                    html.Div(id="hover-coords", style={
                        "position": "absolute",
                        "bottom": "80px",
                        "left": "20px",
                        "backgroundColor": "rgba(255,255,255,0.85)",
                        "padding": "6px 12px",
                        "borderRadius": "5px",
                        "fontFamily": "monospace",
                        "fontSize": "12px",
                        "zIndex": "1000",
                        "border": "1px solid #ccc",
                        "boxShadow": "0px 2px 4px rgba(0,0,0,0.1)"
                    }),
                    html.Label("Adjust cortex opacity:"),
                    dcc.Slider(id="opacity", min=0, max=1, step=0.1, value=0.8, marks={0: "0", 0.5: "0.5", 1: "1"}, updatemode="drag"),
                ], style={"position": "relative", "display": "inline-block", "verticalAlign": "top"}),
            
                html.Img(src="/assets/Legend.png", style={
                    "width": "400px",
                    "margin": "0 0 0 20px",
                    "padding": "5px",
                    "display": "inline-block",
                    "verticalAlign": "top"
                })
            ], style={"whiteSpace": "nowrap", "textAlign": "left"}), processed_annotations.to_json(date_format="iso", orient="split")
    else:
        return f"{name}" if name else "No name provided", table_section, html.Div("No PLY data uploaded for 3D visualization.", style={'font-family':'verdana'}), processed_annotations.to_json(date_format="iso", orient="split")

# Table callbacks
@app.callback(
    Output("edited-processed-annotations", "data"),
    Input("editable-table", "data")
)
def save_edits(data):
    # Store the edited table in JSON format
    return pd.DataFrame(data).to_json(date_format="iso", orient="split")

@app.callback(
    Output("download-table", "data"),
    Input("download-table-btn", "n_clicks"),
    State("result-name", "children"),
    State("edited-processed-annotations", "data"),
    prevent_initial_call=True
)
def download_table(n_clicks, name, processed_annotations_json):
    if not processed_annotations_json:
        raise dash.exceptions.PreventUpdate
    
    processed_annotations = pd.read_json(processed_annotations_json, orient="split")
    print("download table")

    # return as CSV
    return dcc.send_data_frame(
        processed_annotations.to_csv,
        filename=f"{name}_annotations.csv",
        index=False
    )

# 3D interaction functions
@app.callback(
    Output("result-plot-3d", "figure"),
    Input("opacity", "value"),
    State("result-plot-3d", "figure"),
    State("result-plot-3d","relayoutData"),
    prevent_initial_call=True
)
def update_opacity(opacity, fig, relayoutData):
    if not fig:
        raise dash.exceptions.PreventUpdate

    # Preserve current camera
    camera = None
    if relayoutData and "scene.camera" in relayoutData:
        camera = relayoutData["scene.camera"]

    # Update mesh opacity
    for trace in fig["data"]:
        if trace["type"] == "mesh3d":
            trace["opacity"] = opacity

    # Reapply preserved camera
    if camera:
        fig["layout"]["scene"]["camera"] = camera
    
    return fig

@app.callback(
    Output("hover-coords", "children"),
    Input("result-plot-3d", "hoverData"),
    prevent_initial_call=True
)
def display_hover_coordinates(hoverData):
    if not hoverData or "points" not in hoverData:
        return ""

    point = hoverData["points"][0]
    x, y, z = point.get("x"), point.get("y"), point.get("z")  
    customdata = point.get("customdata")
    electrode_label = customdata if customdata and len(customdata) > 0 else "N/A"

    return html.Div([
        html.Div(f"Electrode: {electrode_label}"),
        html.Div(f"x: {x:.2f}, y: {y:.2f}, z: {z:.2f}")
    ])

# Run app
if __name__ == "__main__":
    app.run(debug=True)