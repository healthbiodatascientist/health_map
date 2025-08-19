import numpy as np
from dash import Dash, html, dcc, Input, Output  # pip install dash
import plotly.express as px
import dash_ag_grid as dag
import dash_bootstrap_components as dbc   # pip install dash-bootstrap-components
import pandas as pd     # pip install pandas
import matplotlib      # pip install matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import gunicorn

def table_clean():
    df_hosp_beds = pd.read_csv('https://raw.githubusercontent.com/healthbiodatascientist/Health-Dash/refs/heads/main/beds_by_nhs_board-of-treatment_specialty.csv')
    df_region = pd.read_csv('https://raw.githubusercontent.com/healthbiodatascientist/Health-Dash/refs/heads/main/Health_Boards_(Dec_2020)_Names_and_Codes_in_Scotland.csv')
    df_hosp_beds = df_hosp_beds.set_index('HB')
    df_hb_beds = df_hosp_beds.join(df_region.set_index('HB20CD'), on='HB') # join health board region names
    df_hb_beds = df_hb_beds.filter(items=['FinancialYear', 'SpecialtyName', 'HB20NM', 'PercentageOccupancy', 'AverageAvailableStaffedBeds', 'AllStaffedBeds'])
    return df_hb_beds

df_hb_beds = table_clean()

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    html.H3("Choose a year and a specialty from the list below:", className='mb-2', style={'textAlign':'left'}),
    dbc.Row([dbc.Col([dcc.Dropdown(id='year', value='2023/24', clearable=False, options=np.unique(df_hb_beds['FinancialYear'].values)) ], width=4)]),
    dbc.Row([dbc.Col([dcc.Dropdown(id='specialism', value='All Specialties', clearable=False, options=np.unique(df_hb_beds['SpecialtyName'].values)) ], width=4)]),
    html.H1("Beds Available in Scottish Health Boards", className='mb-2', style={'textAlign':'center'}),
    dbc.Row([dbc.Col([dcc.Dropdown(id='category', value='PercentageOccupancy', clearable=False, options=df_hb_beds.columns[3:6]) ], width=4)]),
    dbc.Row([dbc.Col([html.Img(id='bar-graph-matplotlib')], width=8)]),
    dbc.Row([dbc.Col([dcc.Graph(id='bar-graph-plotly', figure={})], width=8, md=6),
             dbc.Col([dag.AgGrid(id='grid', rowData=df_hb_beds.to_dict("records"), columnDefs=[{"field": i} for i in df_hb_beds.columns], columnSize="sizeToFit",)], width=12, md=6),
             ], className='mt-4'),])
@app.callback(
    Output(component_id='bar-graph-matplotlib', component_property='src'),
    Output('bar-graph-plotly', 'figure'),
    Output('grid', 'defaultColDef'),
    Input('year', 'value'),
    Input('specialism', 'value'),
    Input('category', 'value'),
    
)

def plot_data(year, specialism, selected_yaxis):

    # Build the matplotlib figure
    df_hb_beds = table_clean()
    df_hb_beds = df_hb_beds.loc[df_hb_beds['FinancialYear'].str.startswith(year, na=False)] # filter for year
    df_hb_beds = df_hb_beds.loc[df_hb_beds['SpecialtyName'] == specialism] # filter for specialism
    df_hb_beds = df_hb_beds.filter(items=['HB20NM', 'PercentageOccupancy', 'AverageAvailableStaffedBeds', 'AllStaffedBeds'])
    fig = plt.figure(figsize=(12, 6), constrained_layout=True)
    plt.bar(df_hb_beds['HB20NM'], df_hb_beds[selected_yaxis], color='blue')
    plt.ylabel(selected_yaxis)
    plt.xticks(rotation=90)
    bar_container = plt.bar(df_hb_beds['HB20NM'], df_hb_beds[selected_yaxis])
    plt.bar_label(bar_container, fmt='{:,.0f}')

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    fig_data = base64.b64encode(buf.getbuffer()).decode("ascii")
    fig_bar_matplotlib = f'data:image/png;base64,{fig_data}'

    # Build the Plotly figure
    fig_bar_plotly = px.bar(df_hb_beds, x='HB20NM', y=selected_yaxis).update_xaxes(tickangle=330)

    my_cellStyle = {
        "styleConditions": [
            {
                "condition": f"params.colDef.field == '{selected_yaxis}'",
                "style": {"backgroundColor": "#d3d3d3"},
            },
            {   "condition": f"params.colDef.field != '{selected_yaxis}'",
                "style": {"color": "black"}
            },
        ]
    }

    return fig_bar_matplotlib, fig_bar_plotly, {'cellStyle': my_cellStyle}
if __name__ == '__main__':
    app.run()