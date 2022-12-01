# Import dependencies and start the app ---------------------------------------
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import dash_bootstrap_components as dbc
import dash
from dash import Dash, dcc, html, Input, Output, State, callback, dash_table
app = Dash(
    __name__,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}]
)

# Read the data and get variables ---------------------------------------------------------
df_raw = pd.read_csv('/Users/kevingiam/Aspera/Home/pcore_clean_2022_11_03.csv')
uq_h_name = np.sort(df_raw['h_name'].unique())
uq_p_achi_id = np.sort(df_raw['p_achi_id'].unique())
uq_p_asa_ps = df_raw['p_asa_ps'].unique()
uq_p_admission_urgency = df_raw['p_admission_urgency'].unique()

# Sidebar ---------------------------------------------------------
sidebar = html.Div(
    [
        # Image and heading
        dbc.Row(
            [
                dbc.Col(html.Img(src='assets/SurgiDash.png', height='33px'), width=1),
                dbc.Col(html.H2("SurgiDash"), style={'margin-left': '5px'})
            ]
        ),
        
        dbc.Row([html.Hr()]),

        # Docs
        dbc.Row(
            [
                dbc.Button(id='id_button_docs_open', children='Documentation', n_clicks=0, size='sm'),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle('Documentation')),
                        dbc.ModalBody('content'),
                        dbc.ModalFooter(
                            dbc.Button('Close', id='id_button_docs_close', n_clicks=0, size='sm')
                        )
                    ],
                    id='id_modal_docs',
                    is_open=False,
                )
            ]
        ),

        # Checklist for hospital name
        dbc.Row([dcc.Checklist(
            id='id_ck_h_name',
            options=uq_h_name,
            value=uq_h_name
        )]),

        # Data table for ACHI ID
        dbc.Row(
            [
                dbc.Col(dbc.Button(id='id_button_selectall_p_achi_id', children='Select all', size='sm')),
                dbc.Col(dbc.Button(id='id_button_selectnone_p_achi_id', children='Select none', size='sm'))
            ]
        ),

        dbc.Row(
            dash_table.DataTable(
                id='id_dt_p_achi_id',
                columns=[{'id': 'p_achi_id', 'name': 'p_achi_id', 'type': 'numeric'}],
                data=df_raw[['p_achi_id']].sort_values('p_achi_id').drop_duplicates().to_dict('records'),
                row_selectable='multi',
                sort_action='native',
                filter_action='native',
                page_size=8,
                style_as_list_view=True
            )
        ),

        # Range slider for ASA PS
        dbc.Row([dcc.RangeSlider(
            id='id_rs_p_asa_ps',
            min=1,
            max=5,
            step=1,
            value=[1, 5]
        )]),

        # Checklist for admission urgency
        dbc.Row([dcc.Checklist(
            id='id_ck_p_admission_urgency',
            options=uq_p_admission_urgency,
            value=uq_p_admission_urgency
        )]),

        # Save changes button
        dbc.Row([
            dbc.Button(id='id_button_save_changes', children='Save changes', n_clicks=0, size='sm')
        ]),

        # Store the data frame inside the user's current browser session
        dcc.Store(id='id_df_stored', data=df_raw.copy(deep=True).to_dict('records'), storage_type='memory'),
    ]
)

# Content ---------------------------------------------------------
content = html.Div([
    dbc.Row(
        [dcc.Graph(id='id_graph_h_los', figure={})]
    )
])

# App layout ---------------------------------------------------------
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(sidebar, width=3),
                dbc.Col(content, width=9)
            ]
        )
    ], fluid=True
)

# Callback: Modal ---------------------------------------------------------
@callback(
    [Output('id_modal_docs', 'is_open')],
    [Input('id_button_docs_open', 'n_clicks'), Input('id_button_docs_close', 'n_clicks')],
    [State('id_modal_docs', 'is_open')]
)

def toggle_modal_docs(n_open, n_close, is_open):
    if n_open or n_close:
        return [not is_open]
    return [is_open]

# Callback: ACHI ID data table select all and select none ---------------------------------------------------------
@callback(
    [
        Output('id_dt_p_achi_id', 'selected_rows')
    ],
    [
        Input('id_button_selectall_p_achi_id', 'n_clicks'),
        Input('id_button_selectnone_p_achi_id', 'n_clicks')
    ],
    [
        State('id_dt_p_achi_id', 'derived_virtual_data')
    ]
)

def selectall_p_achi_id(all_clicks, none_clicks, selected_rows):
    if selected_rows is None:
        return [[]]

    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'id_button_selectall_p_achi_id':
        return [[i for i in range(len(selected_rows))]]
    else:
        return [[]]

# Callback: Apply filter ---------------------------------------------------------
@callback(
    Output('id_df_stored', 'data'),
    [
        Input('id_df_stored', 'data')
        Input('id_ck_h_name', 'value'),
        Input('id_rs_p_asa_ps', 'value'),
        Input('id_ck_p_admission_urgency', 'value')
    ]
)

def store_data(data, input_ck_h_name, input_rs_p_asa_ps, input_ck_p_admission_urgency):
    data = data[
        (data['h_name'].isin(input_ck_h_name)) &
        (data['p_asa_ps'].isin(input_rs_p_asa_ps)) &
        (data['p_admission_urgency'].isin(input_ck_p_admission_urgency))
    ]

    return [data]


# Callback: Graph, hospital length of stay ---------------------------------------------------------
@callback(
    Output('id_graph_h_los', 'figure'), 
    Input('id_df_stored', 'data')
)

def update_h_los(data):
    # Slice
    data = data[['h_name', 'p_admission_urgency', 'p_los']]
    # Group
    data = data.groupby(['h_name', 'p_admission_urgency']).sum()
    data = data.reset_index()
    # Figure
    fig = px.bar(
        data,
        x='h_name',
        y='p_los',
        color='p_admission_urgency',
        hover_data={}
    )

    return [fig]

# Run the app ---------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
