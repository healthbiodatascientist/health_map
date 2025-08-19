#!/usr/bin/env python
# coding: utf-8

# Import libraries/packages

# In[1]:


import pandas as pd
import matplotlib 
matplotlib.use('agg')
from dash import Dash, html, dash_table
import dash_bootstrap_components as dbc
import geopandas as gpd
from pyogrio import read_dataframe
import folium


# Import and filter data

# In[2]:


def table_clean():
    df_hosp_beds = pd.read_csv('https://raw.githubusercontent.com/healthbiodatascientist/Health-Dash/refs/heads/main/beds_by_nhs_board-of-treatment_specialty.csv') # Open Public Health Scotland Hospital Beds Data
    df_map = read_dataframe('https://github.com/healthbiodatascientist/Health-Dash/raw/refs/heads/main/SG_NHS_HealthBoards_2019.shp') # Scottish Health Board Region Names and Geometries
    df_ae = pd.read_csv('https://raw.githubusercontent.com/healthbiodatascientist/Health-Dash/refs/heads/main/weekly_ae_activity_20250615.csv') # Public Health Scotland's A&E data 2015-2025
    df_emerge = pd.read_csv('https://raw.githubusercontent.com/healthbiodatascientist/Health-Dash/refs/heads/main/table-3-multiple-emergency-admissions-2023-24.csv', dtype = 'str') # Public Health Scotland Emergency Admissions data 2023-24
    df_amb_turnaround = pd.read_csv('https://raw.githubusercontent.com/healthbiodatascientist/Health-Dash/refs/heads/main/median_ambulance_turnaround_times_2023_24.csv') # Scottish Ambulance Service data on turnaround times
    df_amb_demand = pd.read_csv('https://raw.githubusercontent.com/healthbiodatascientist/Health-Dash/refs/heads/main/percentage_unscheduled_emergencies_attended_conveyed.csv')
    df_ae['WeekEndingDate'] = df_ae['WeekEndingDate'].astype(str) # change WeekEndingDate to string for filtering later
    df_hb_beds = df_hosp_beds.filter(items=['HB', 'FinancialYear', 'SpecialtyName', 'PercentageOccupancy', 'AverageAvailableStaffedBeds', 'AllStaffedBeds']) # filter
    df_map = df_map.filter(items=['HBCode', 'HBName', 'geometry']) # filter for the columns we need
    df_map = df_map.set_index('HBCode') # set the index to the Health Board Code
    df_hb_beds_map = df_map.join(df_hb_beds.set_index('HB'), on='HBCode') # Join the tables
    df_hb_beds_map = df_hb_beds_map.filter(items=['FinancialYear', 'SpecialtyName', 'HBName', 'PercentageOccupancy', 'AverageAvailableStaffedBeds', 'AllStaffedBeds', 'geometry']) 
    df_hb_beds_filter = df_hb_beds_map.loc[df_hb_beds_map['FinancialYear'].str.startswith('2023', na=False)] # filter for year
    df_hb_beds_filter = df_hb_beds_filter.loc[df_hb_beds_filter['SpecialtyName'] == 'All Acute Specialties']
    df_ae = df_ae.loc[df_ae['AttendanceCategory'] == 'All'] # filter for 'All' attendances only
    mask = (df_ae['WeekEndingDate'] > '20230402') & (df_ae['WeekEndingDate'] <= '20240331')
    df_filter_year = df_ae.loc[mask] # filter for year
    df_filternumber = df_filter_year.filter(items=['HBT', 'NumberOfAttendancesEpisode', 'NumberWithin4HoursEpisode', 'NumberOver4HoursEpisode', 'NumberOver8HoursEpisode', 'NumberOver12HoursEpisode']) # filter for numbers which can be summed only
    df_hb = df_filternumber.groupby('HBT').sum() # group by health board
    df_hb['PercentageWithin4HoursEpisode'] = df_hb['NumberWithin4HoursEpisode']/df_hb['NumberOfAttendancesEpisode']*100 # add in columns for percentages
    df_hb['PercentageOver4HoursA&E'] = df_hb['NumberOver4HoursEpisode']/df_hb['NumberOfAttendancesEpisode']*100
    df_hb['PercentageOver8HoursA&E'] = df_hb['NumberOver8HoursEpisode']/df_hb['NumberOfAttendancesEpisode']*100
    df_hb['PercentageOver12HoursA&E'] = df_hb['NumberOver12HoursEpisode']/df_hb['NumberOfAttendancesEpisode']*100
    df_hb_beds_filter = df_hb_beds_filter.join(df_hb, on=df_hb.index) # Join the tables
    df_hb_beds_filter = df_hb_beds_filter.round(2)
    df_hb_beds_filter = df_hb_beds_filter.filter(items=['HBName','PercentageOccupancy', 'PercentageWithin4HoursEpisode', 'PercentageOver4HoursA&E', 'PercentageOver8HoursA&E', 'PercentageOver12HoursA&E', 'geometry'])
    df_hb_beds_filter.columns = ['HB Name','Percentage Occupancy Acute Beds', 'Percentage Within 4 Hours A&E', 'Percentage Over 4 Hours A&E', 'Percentage Over 8 Hours A&E', 'Percentage Over 12 Hours A&E', 'geometry']
    df_emerge_NHS = df_emerge.loc[df_emerge['lookup'].str.contains('NHS')] # filter for NHS Boards
    df_emerge_NHS = df_emerge_NHS.loc[df_emerge_NHS['lookup'].str.contains('All Sexes - All AgesTotal')] # filter for all sexes and ages totals
    df_emerge_NHS = df_emerge_NHS.loc[df_emerge_NHS['lookup'].str.startswith('2023')] # filter for 2023/24
    df_emerge_NHS = df_emerge_NHS.reset_index(drop=True)
    df_emerge_NHS_region = df_emerge_NHS['lookup'].str.split('NHS', expand=True)
    df_emerge_NHS_region_final = df_emerge_NHS_region[2].str.split('All Sexes', expand=True)
    df_emerge_NHS_region_final = df_emerge_NHS_region_final[0]
    df_emerge_NHS_region_final = pd.DataFrame(df_emerge_NHS_region_final)
    df_emerge_NHS['lookup'] = df_emerge_NHS_region_final
    df_emerge_NHS = df_emerge_NHS.dropna()
    df_emerge_NHS = df_emerge_NHS.filter(items = ['lookup', 'patients_Rate', 'stays_Rate', 'los_stays_Rate'])
    df_emerge_NHS.columns = ['region', 'Emergency Patients Rate', 'Emergency Stays Rate', 'Length Emergency Stays Rate']
    df_emerge_NHS['region'] = df_emerge_NHS['region'].str.replace('&', 'and')
    df_hb_beds_filter = df_hb_beds_filter.sort_values(by='HB Name')
    df_emerge_NHS = df_emerge_NHS.set_index(df_hb_beds_filter.index)
    df_hb_beds_filter = df_hb_beds_filter.join(df_emerge_NHS, on=df_hb_beds_filter.index)
    df_hb_beds_filter = df_hb_beds_filter.filter(items=['HB Name','Percentage Occupancy Acute Beds', 'Percentage Within 4 Hours A&E', 'Percentage Over 4 Hours A&E', 'Percentage Over 8 Hours A&E', 'Percentage Over 12 Hours A&E', 'Emergency Patients Rate', 'Emergency Stays Rate', 'Length Emergency Stays Rate', 'geometry'])
    df_amb_turnaround['2023_24_median_turnaround_time_(hh:mm:ss)'] = df_amb_turnaround['2023_24_median_turnaround_time_(hh:mm:ss)'].astype(str)
    df_amb_turnaround['2023_24_median_turnaround_time_(hh:mm:ss)'] = df_amb_turnaround['2023_24_median_turnaround_time_(hh:mm:ss)'].str.split(':', expand=True)[1]
    df_amb_turnaround.columns = ['HealthBoard', 'Median Ambulance Turnaround Time (min)']
    df_amb_turnaround = df_amb_turnaround.set_index(df_hb_beds_filter.index)
    df_hb_beds_filter = df_hb_beds_filter.join(df_amb_turnaround, on=df_hb_beds_filter.index)
    df_hb_beds_filter = df_hb_beds_filter.filter(items=['HB Name','Percentage Occupancy Acute Beds', 'Percentage Within 4 Hours A&E', 'Percentage Over 4 Hours A&E', 'Percentage Over 8 Hours A&E', 'Percentage Over 12 Hours A&E', 'Emergency Patients Rate', 'Emergency Stays Rate', 'Length Emergency Stays Rate', 'Median Ambulance Turnaround Time (min)', 'geometry'])
    df_amb_demand.columns = ['HealthBoard', 'NumEmergencies', 'EmergeciesAttended', 'EmergenciesConveyed', 'Percentage Emergencies Attended', 'Percentage Emergencies Conveyed']
    df_amb_demand = df_amb_demand.set_index(df_hb_beds_filter.index)
    df_hb_beds_filter = df_hb_beds_filter.join(df_amb_demand, on=df_hb_beds_filter.index)
    df_hb_beds_filter = df_hb_beds_filter.filter(items=['HB Name', 'Percentage Emergencies Conveyed', 'Median Ambulance Turnaround Time (min)', 'Emergency Patients Rate', 'Percentage Within 4 Hours A&E', 'Percentage Over 4 Hours A&E', 'Percentage Over 8 Hours A&E', 'Percentage Over 12 Hours A&E', 'Percentage Occupancy Acute Beds', 'Length Emergency Stays Rate', 'geometry'])
    df_hb_beds_filter.to_csv('HealthBoardDataFinal.csv')
    return df_hb_beds_filter
df_hb_beds_filter = table_clean()


# In[6]:


def no_geometry():
    df_hb_beds_filter = table_clean()
    df_hb_beds_table = df_hb_beds_filter.drop('geometry', axis=1)
    df_hb_beds_table['Emergency Patients Rate'] = df_hb_beds_table['Emergency Patients Rate'].astype(float)
    df_hb_beds_table['Median Ambulance Turnaround Time (min)'] = df_hb_beds_table['Median Ambulance Turnaround Time (min)'].astype(int)
    df_hb_beds_table['Length Emergency Stays Rate'] = df_hb_beds_table['Length Emergency Stays Rate'].astype(float)
    return df_hb_beds_table
df_hb_beds_table = no_geometry()
df_numeric_columns = df_hb_beds_table.select_dtypes('number')
def create_map():
    # imports, filters and joins the data and produces the map
    df_hb_beds_filter = table_clean()
    foliummap = folium.Map(location=[55.941457, -3.205744], zoom_start=6)
    mapped = df_hb_beds_filter.explore(m=foliummap, column='HB Name')
    mapped.save('foliummap.html')

    return mapped
create_map()


# In[7]:


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


# In[8]:


if __name__ == "__main__":
    app.run()

