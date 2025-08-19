#!/usr/bin/env python
# coding: utf-8

# Import libraries/packages

# In[1]:


import pandas as pd
import matplotlib 
matplotlib.use('agg')
from dash import Dash, html, dash_table
import dash_bootstrap_components as dbc
from pyogrio import read_dataframe
import folium


# Import and filter data

# In[2]:


df_hb_beds_filter = pd.read_csv('https://raw.githubusercontent.com/healthbiodatascientist/health_map/refs/heads/main/HealthBoardDataFinal.csv')
def no_geometry():
    df_hb_beds_filter = pd.read_csv('https://raw.githubusercontent.com/healthbiodatascientist/health_map/refs/heads/main/HealthBoardDataFinal.csv')
    df_hb_beds_table = df_hb_beds_filter.drop('geometry', axis=1)
    df_hb_beds_table['Emergency Patients Rate'] = df_hb_beds_table['Emergency Patients Rate'].astype(float)
    df_hb_beds_table['Median Ambulance Turnaround Time (min)'] = df_hb_beds_table['Median Ambulance Turnaround Time (min)'].astype(int)
    df_hb_beds_table['Length Emergency Stays Rate'] = df_hb_beds_table['Length Emergency Stays Rate'].astype(float)
    df_hb_beds_table = df_hb_beds_table.set_index('HBCode')
    return df_hb_beds_table
df_hb_beds_table = no_geometry()
df_numeric_columns = df_hb_beds_table.select_dtypes('number')


# In[3]:


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
app.layout = dbc.Container([
    html.H1("Regional Scottish Health Board Acute Case Data 2023/24", className='mb-2', style={'padding': '10px 10px', 'textAlign':'center'}),
    dbc.Row([dbc.Col(html.Summary("The map below displays the last full set of combined open source data from Public Health Scotland (PHS) and the Scottish Ambulance Service (SAS) for each of the Scottish Health Board Regions. Hover over your Health Board for an insight into the factors affecting the efficiency of acute care:", className='mb-2', style={'padding': '10px 10px', 'list-style': 'none'}))]),
    dbc.Row([dbc.Col(html.Iframe(id='my_output', height=600, width=1000, srcDoc=open('foliummap.html', 'r').read()))]),
    html.Figcaption("Figure 1: Map of the 2023/24 open health data for the Scottish Health Board Regions", className='mb-2', style={'padding': '10px 10px', 'textAlign':'center'}),
    html.H4("SAS, NHS Scotland and Scottish Government Targets for 2023/24", className='mb-2', style={'margin-top': '1em', 'padding': '10px 10px', 'textAlign': 'center'}),
    html.Summary("Percentage Emergencies Conveyed: No specific SAS targets set in 2023/24. However, high volumes of ambulance conveyances to A&E departments can significantly worsen waiting times. This is because increased ambulance arrivals can lead to overcrowding, putting strain on resources and staff, and ultimately resulting in longer waits for all patients, including those who arrive by other means", className='mb-2'),
    html.Summary("Median Ambulance Turnaround Time (min): Target of median turnaround time within 40 minutes set by SAS 2023/24", className='mb-2'),
    html.Summary("Emergency Patients Rate: No specific Scottish Government or NHS targets set in 2023/24. However, high numbers of emergency patients significantly increase waiting times in A&E departments. This is due to increased demand on resources, particularly hospital beds, leading to longer waits for assessment, treatment, and admission", className='mb-2'),
    html.Summary("Percentage Within 4 Hours A&E, Percentage Over 4, 8, and 12 Hours A&E: Target of 95% of people attending A&E should be seen, admitted, discharged, or transferred within 4 hours set by Scottish Government 2010", className='mb-2'),
    html.Summary("Percentage Occupancy Acute Beds: In NHS Scotland, 92% bed occupancy is considered a benchmark, but not an absolute standard. The 2023/24 operational planning guidance set 92% as the maximum for bed occupancy, as high occupancy can negatively impact patient flow, waiting times, and infection control", className='mb-2'),
    html.Summary("Length Emergency Stays Rate: No specific Scottish Government targets set in 2023/24. However, a higher proportion of patients with long lengths of stay in hospitals is directly associated with increased A&E waiting times, particularly for those waiting to be admitted", className='mb-2', style={'margin-bottom': '1em'}),
    html.Figcaption("Table 1: 2023/24 open health data for the Scottish Health Board Regions with the highest 3 column values highlighted in dark blue", className='mb-2', style={'margin-bottom': '1em', 'padding': '10px 10px', 'textAlign':'center'}),
    dbc.Row([dbc.Col(dash_table.DataTable(
    data=df_hb_beds_table.to_dict('records'),
    sort_action='native',
    columns=[{'name': i, 'id': i} for i in df_hb_beds_table.columns],
    style_cell={'textAlign': 'center'},
    fixed_columns={'headers': True, 'data': 1},
    style_table={'minWidth': '100%'},
    style_data_conditional=
    [
            {
                'if': {
                    'filter_query': '{{{}}} > {}'.format(col, value),
                    'column_id': col
                },
                'backgroundColor': '#00008B',
                'color': 'white'
            } for (col, value) in df_numeric_columns.quantile(0.1).items()
        ] +       
        [
            {
                'if': {
                    'filter_query': '{{{}}} <= {}'.format(col, value),
                    'column_id': col
                },
                'backgroundColor': '#65D8EC',
                'color': 'white'
            } for (col, value) in df_numeric_columns.quantile(0.8).items()
        ]
    ))
    ]),
    html.H4("Open Data Links", className='mb-2', style={'margin-top': '1em', 'padding': '10px 10px', 'textAlign': 'center'}),
    html.Summary("Public Health Scotland"),
    html.Link(href="https://www.opendata.nhs.scot/dataset/7e21f62c-64a1-4aa7-b160-60cbdd8a700d/resource/5d55964b-8e45-4c49-bfdd-9ea3e1fb962d/download/beds_by_nhs_board-of-treatment_specialty.csv", rel="stylesheet"),
    html.Link(href="https://www.opendata.nhs.scot/dataset/0d57311a-db66-4eaa-bd6d-cc622b6cbdfa/resource/a5f7ca94-c810-41b5-a7c9-25c18d43e5a4/download/weekly_ae_activity_20250810.csv", rel="stylesheet"),
    html.Link(href="https://publichealthscotland.scot/media/29058/table-3-multiple-emergency-admissions-2023-24.xlsx", rel="stylesheet"),
    html.Summary("Scottish Ambulance Service"),
    html.Link(href="https://www.scottishambulance.com/publications/previous-unscheduled-care-operational-statistics/", rel="stylesheet"),
    html.Link(href="https://www.scottishambulance.com/media/teapv5hp/foi-24-296-service-target-times.pdf", rel="stylesheet"),
    ])
    
def create_map():
    # imports, filters and joins the data and produces the map
    df_hb_beds_filter = table_clean()
    foliummap = folium.Map(location=[55.941457, -3.205744], zoom_start=6)
    mapped = df_hb_beds_filter.explore(m=foliummap, column='HB Name')
    mapped.save('foliummap.html')

    return mapped


# In[4]:


if __name__ == "__main__":
    app.run()

