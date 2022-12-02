# Import dependencies and start the app ---------------------------------------
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import dash_bootstrap_components as dbc
import dash
from dash import Dash, dcc, html, Input, Output, State, callback, dash_table
from datetime import datetime

app = Dash(
    __name__,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}]
)

# UDF
def valid_date(start_date, end_date):
    days = (end_date - start_date).days
    return True if days >= 0 else False

# Variable and abbreviations ---------------------------------------------------------
date_columns = ['p_birth_date', 'p_admission_date', 'p_surgery_date', 'p_separation_date', 'p_death_date']

abbvs_dict = {
    'record_id': 'Record ID',
    'data_access_group': 'Data Access Group',
    'h_name': 'Hospital Name',
    'h_public_private': 'Hospital public/private',
    'h_postcode': 'Hospital postcode',
    'h_sla2': 'Hospital Statistical Level Area 2 (SLA2)',
    'p_id': 'Registry Participant ID',
    'p_birth_date': 'Date of Birth',
    'p_sex': 'Sex',
    'p_postcode': 'Australian Postcode',
    'p_sla2': 'Statistical Area level 2 Code',
    'p_atsi': 'ATSI Status',
    'p_election': 'Patient Election Status',
    'p_admission_date': 'Date of Admission',
    'p_admission_urgency': 'Admission Urgency',
    'p_surgery_date': 'Date of Surgery',
    'p_surgery_age': 'Age at Date of Surgery',
    'p_surgery_urgency': 'Surgical Urgency',
    'p_surgery_type': 'Type of Surgery',
    'p_procedure_name': 'Name of Procedure',
    'p_procedure_code': 'Procedure Code',
    'p_principal_diagnosis_code': 'Principal Diagnosis Code',
    'p_asa_ps': 'ASA-PS',
    'p_clinical_frailty_scale': 'Clinical Frailty Scale',
    'p_albumin': 'Albumin',
    'p_cancer': 'Cancer Status',
    'p_additional_diagnosis_code': 'Additional Diagnosis Codes',
    'p_critical_care_bed_request': 'Critical Care Bed Request',
    'p_critical_care_admission_status': 'Critical Care Admission Status',
    'p_icu_identifier': 'ICU Adult Patient Database Identifier',
    'p_critical_care_hours_los': 'Critical Care Length of Stay (Hours)',
    'p_critical_care_hours_ventilated_invasive': 'Critical Care Ventilated Hours - Invasive',
    'p_critical_care_hours_ventilated_non_invasive': 'Critical Care Ventilated Hours - Non-Invasive',
    'p_separation_date': 'Separation Date',
    'p_separation_mode': 'Separation Mode',
    'p_death_date': 'Date of Death',
    'p_postoperative_days_los': 'Postoperative Length of Stay',
    'complete_status': 'Complete?',
    'p_los': 'Patient Length of Stay (Days)'
}

# Read the data and get variables ---------------------------------------------------------
df_raw = pd.read_csv('/Users/kevingiam/Aspera/Home/pcore_clean_2022_11_03.csv', parse_dates=date_columns)
uq_h_name = np.sort(df_raw['h_name'].unique())
uq_p_achi_id = df_raw[['p_achi_id']].sort_values('p_achi_id').drop_duplicates()
uq_p_asa_ps = df_raw['p_asa_ps'].unique()
uq_p_admission_urgency = df_raw['p_admission_urgency'].unique()
date_min_p_admission_date = df_raw['p_admission_date'].min().date()
date_max_p_admission_date = df_raw['p_admission_date'].max().date()

# Sidebar ---------------------------------------------------------
sidebar = html.Div(
    [
        # Image and heading
        html.Div(
            [
                html.Img(src='assets/SurgiDash.png', height='33px'),
                html.H2("SurgiDash")
            ],
            className='mt-4 d-flex justify-content-center'
        ),
        
        # Documentation
        html.Div(
            [html.P(children='Welcome to surgical dashboard. Click on the documentation for more details.', className='mb-1'),],
            className='mx-3'
        ),
        html.Div(
            [html.P(id='id_button_docs_open', children='Documentation', n_clicks=0, className='page-link col-5')],
            className='d-flex justify-content-center'
        ),
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
        ),
        
        # Horizontal rule
        html.Hr(className='mx-3 mt-0'),

        # Checklist for hospital name
        dbc.Row([html.H5('Select Hospital Name')], className='mx-3'),
        dbc.Row([dbc.Col(dcc.Checklist(id='id_ck_h_name', options=uq_h_name, value=uq_h_name, labelStyle = dict(display='block')))], className='mx-3'),
        html.Br(),

        # Date picker for admission date
        dbc.Row([html.H5('Select Admission Date')], className='mx-3'),
        dbc.Row([dcc.DatePickerRange(
            id='id_dp_p_admission_date',
            start_date=date_min_p_admission_date,
            end_date=date_max_p_admission_date,
            min_date_allowed=date_min_p_admission_date,
            max_date_allowed=date_max_p_admission_date,
            initial_visible_month=date_min_p_admission_date,
            display_format='D MMM YYYY',
            clearable=True,
        )], className='mx-3'),
        html.Br(),

        # Checklist for admission urgency
        dbc.Row([html.H5('Select Admission Urgency')], className='mx-3'),
        dbc.Row([dbc.Col(dcc.Checklist(
            id='id_ck_p_admission_urgency', 
            options=uq_p_admission_urgency, 
            value=uq_p_admission_urgency, 
            labelStyle = dict(display='block'),
        ))], className='mx-3'),
        html.Br(),

        # Range slider for ASA PS
        dbc.Row([html.H5('Select ASA-PS')], className='mx-3'),
        dbc.Row([dcc.RangeSlider(id='id_rs_p_asa_ps', min=1, max=5, step=1, value=[1, 5])], className='mx-3'),
        html.Br(),

        # Data table for ACHI ID
        dbc.Row([html.H5('Select ACHI ID')], className='mx-3'),        
        dbc.Row(
            dash_table.DataTable(
                id='id_dt_p_achi_id',
                columns=[{'id': 'p_achi_id', 'name': 'p_achi_id', 'type': 'numeric'}],
                data=uq_p_achi_id.to_dict('records'),
                selected_rows=np.arange(uq_p_achi_id.shape[0]),
                row_selectable='multi',
                sort_action='native',
                filter_action='native',
                page_size=8,
                style_as_list_view=True
            ),
            className='mx-3'
        ),
        html.Div(
            [
                html.Button(id='id_button_selectall_p_achi_id', children='Select all', className='btn-light w-50 me-2 fs-6'),
                html.Button(id='id_button_selectnone_p_achi_id', children='Select none', className='btn-light w-50 fs-6'),
            ], 
            className='d-flex justify-content-center mx-5'
        ),
        html.Br(),

        # Save changes button
        dbc.Row([
            html.Button(id='id_button_save_changes', children='Save changes', n_clicks=0, className='btn-primary fs-6')
        ], className='d-flex justify-content-center mx-3'),

        # Error modal
        dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle('Error')),
                        dbc.ModalBody('Error'),
                    ],
                    id='id_modal_error',
                    is_open=False,
                ),

        # Store the data frame inside the user's current browser session
        dcc.Store(id='id_df_stored', data=df_raw.copy(deep=True).to_dict('records'), storage_type='memory'),
    ],
    className='sidebar-right'
)

# Content ---------------------------------------------------------
content = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id='id_graph_p_los', figure={})),
                dbc.Col(dcc.Graph(id='id_graph_p_critical_care_admission_status', figure={})),
            ],
        ),

        html.Br(),

        dbc.Row(
            [
                dbc.Col(dcc.Graph(id='id_graph_p_critical_care_hours_los', figure={})),
                dbc.Col(dcc.Graph(id='', figure={})),
            ]
        )
    ],
)


# App layout ---------------------------------------------------------
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(content, width=9),
                dbc.Col(sidebar),
            ],
            className='my-3'
        )
    ], fluid=True
)

# Callback: Documentation modal ---------------------------------------------------------
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
        Output('id_dt_p_achi_id', 'selected_rows'),
        Output('id_button_selectall_p_achi_id', 'n_clicks'),
        Output('id_button_selectnone_p_achi_id', 'n_clicks')
    ],
    [
        Input('id_button_selectall_p_achi_id', 'n_clicks'),
        Input('id_button_selectnone_p_achi_id', 'n_clicks')
    ],
)

def selectall_p_achi_id(selectall_clicked, selectnone_clicked):
    if selectall_clicked:
        return [np.arange(uq_p_achi_id.shape[0]), 0, 0]
    if selectnone_clicked:
        return [[], 0, 0]
    return [np.arange(uq_p_achi_id.shape[0]), 0, 0]

# Callback: Apply filter ---------------------------------------------------------
@callback(
    [
        Output('id_df_stored', 'data'),
        Output('id_modal_error', 'is_open')
    ],
    [
        Input('id_button_save_changes', 'n_clicks')
    ],
    [
        State('id_ck_h_name', 'value'),
        State('id_dt_p_achi_id', 'data'),
        State('id_dt_p_achi_id', 'selected_rows'),
        State('id_rs_p_asa_ps', 'value'),
        State('id_ck_p_admission_urgency', 'value'),
        State('id_dp_p_admission_date', 'start_date'),
        State('id_dp_p_admission_date', 'end_date')
    ]
)

def store_data(
    n_clicks, 
    input_ck_h_name, 
    input_dt_p_achi_id_data, 
    input_dt_p_achi_id_selectedrows, 
    input_rs_p_asa_ps, 
    input_ck_p_admission_urgency, 
    input_dp_p_admission_date_start, 
    input_dp_p_admission_date_end
):
    # Get the raw data frame
    data = df_raw.copy(deep=True)

    # Flag for modal
    is_open = True

    # Check if any filter is empty
    filter_input = [input_ck_h_name, input_dt_p_achi_id_selectedrows, input_rs_p_asa_ps, input_ck_p_admission_urgency]
    filter_not_empty = all(map(lambda val: bool(val), filter_input))

    # Check if any dates is invalid
    input_dp_p_admission_date_start = datetime.strptime(input_dp_p_admission_date_start, '%Y-%m-%d')
    input_dp_p_admission_date_end = datetime.strptime(input_dp_p_admission_date_end, '%Y-%m-%d')
    p_admission_date_is_valid = valid_date(input_dp_p_admission_date_start, input_dp_p_admission_date_end)

    # If filter is not empty
    if filter_not_empty and p_admission_date_is_valid:
        # Get selected p_achi_id
        dt_p_achi_id_values = [input_dt_p_achi_id_data[i]['p_achi_id'] for i in input_dt_p_achi_id_selectedrows]
        # Apply filter
        data = data[
            # Hospital name
            (data['h_name'].isin(input_ck_h_name)) &
            # ACHI ID
            (data['p_achi_id'].isin(dt_p_achi_id_values)) &
            # ASA PS
            (data['p_asa_ps'].isin(input_rs_p_asa_ps)) &
            # Admission urgency
            (data['p_admission_urgency'].isin(input_ck_p_admission_urgency)) &
            # Admission date
            (data['p_admission_date'] > input_dp_p_admission_date_start) & 
            (data['p_admission_date'] < input_dp_p_admission_date_end)
        ]
        print(data.shape)
        is_open = False
    
    return data.to_dict('records'), is_open

# Callback: Graph, hospital length of stay ---------------------------------------------------------
@callback(
    Output('id_graph_p_los', 'figure'), 
    Input('id_df_stored', 'data')
)

def update_p_los(data):
    # Get data
    data = pd.DataFrame(data)
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
    fig.update_layout(
        title="Total Patient Length of Stay per Hospital",
        xaxis_title=abbvs_dict['h_name'],
        yaxis_title=abbvs_dict['p_los'],
        legend=dict(
            y= -0.15,
            yanchor='top',
            title=abbvs_dict['p_admission_urgency'],
            orientation="h",
        )
    )
    return fig

# Run the app ---------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
