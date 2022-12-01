# Bootstrap
# Check correctness of all data
# Check missing values

# Import dependencies and start the app ---------------------------------------
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, State, dash_table
app = Dash(
    __name__,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}]
)

# Read the data and get variables ---------------------------------------------------------
df_raw = pd.read_csv('/Users/kevingiam/Aspera/Home/pcore_clean_2022_11_03.csv')
uq_h_name = np.sort(df_raw['h_name'].unique())
#uq_p_surgery_type = np.sort(df_raw['p_surgery_type'].unique())
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
        dbc.Row([dcc.Checklist()]),

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
@app.callback(
    [Output('id_modal_docs', 'is_open')],
    [Input('id_button_docs_open', 'n_clicks'), Input('id_button_docs_close', 'n_clicks')],
    [State('id_modal_docs', 'is_open')]
)

def toggle_modal_docs(n_open, n_close, is_open):
    if n_open or n_close:
        return [not is_open]
    return [is_open]

# Callback: Hospital length of stay ---------------------------------------------------------

# Callback: Hospital length of stay ---------------------------------------------------------
@app.callback(
    [
        Output('id_graph_h_los', 'figure')
    ],
    [
        Input('id_ck_h_name', 'value'),
        # Input('id_dd_p_surgery_type', 'value'),
        Input('id_dd_p_achi_id', 'value'),
        Input('id_rs_p_asa_ps', 'value'),
        Input('id_ck_p_admission_urgency', 'value')
    ]
)

def update_h_los(input_ck_h_name, input_dd_p_achi_id, input_rs_p_asa_ps, input_ck_p_admission_urgency):  # Component property of input
    # Copy
    df_h_los = df_raw.copy()
    # Filter
    df_h_los = df_h_los[df_h_los['h_name'].isin(input_ck_h_name)]
    # df_h_los = df_h_los[df_h_los['p_surgery_type'].isin(input_dd_p_surgery_type)]
    df_h_los = df_h_los[df_h_los['p_achi_id'].isin(input_dd_p_achi_id)]
    df_h_los = df_h_los[df_h_los['p_asa_ps'].isin(input_rs_p_asa_ps)]
    df_h_los = df_h_los[df_h_los['p_admission_urgency'].isin(input_ck_p_admission_urgency)]
    # Slice
    df_h_los = df_h_los[['h_name', 'p_admission_urgency', 'p_los']]
    # Group
    df_h_los = df_h_los.groupby(['h_name', 'p_admission_urgency']).sum()
    df_h_los = df_h_los.reset_index()
    # Figure
    fig = px.bar(
        df_h_los,
        x='h_name',
        y='p_los',
        color='p_admission_urgency',
        hover_data={}
    )

    return [fig] # Component property of output

# Run the app ---------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
