import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
from dash import Input, Output, callback, ctx
import flask
import pandas as pd
import os
from Models_and_engine import dynamic_engine, DashResponse
from fastapi.middleware.wsgi import WSGIMiddleware
import time

style_cell = {
    'textAlign': 'left',
    'whiteSpace': 'normal',
    'height': 'auto',
    'padding': 5,
    'width': 100,
}

style_header = {
    'font-weight': 'bold',
    'color': 'darkblue',
    'border': '2px solid #ccc',
    'borderBottom': '2px solid darkblue',
}

style_data = {
    'height': '60px',
}

style_cell_conditional = [
    {
        'if': {'column_id': 'DESCRIPTION'},
        'width': 200,
    }
]

style_data_conditional = [
    {
        "if": {"row_index": "odd"},
        "backgroundColor": "lightblue",
    },
    {
        "if": {"row_index": "even"},
        "backgroundColor": "white",
    },
]

fixed_rows = {'headers': True}

style_table = {'height': '100%'}

active_dashboards = {}

class DashboardInfo:
    def __init__(self, dash_app, flask_server, last_activity):
        self.dash_app = dash_app
        self.flask_server = flask_server
        self.last_activity = last_activity
        self.timer = None

def clear(app, user_id):
    try:
        cleaned = []
        for key in list(active_dashboards.keys()):
            if user_id in key.split('_')[-1]:
                cleaned.append(key)
                del active_dashboards[key]
        app.router.routes = [route for route in app.router.routes if not f'{route.path}/' in cleaned]
    except Exception as e:
        print(e)

def create_dash_app(app, identifier) -> dash.Dash:
    #server = flask.Flask(__name__)
    requests_pathname_prefix = f'/{identifier}/'
    if requests_pathname_prefix in active_dashboards:
        app.router.routes = [route for route in app.router.routes if not route.path in requests_pathname_prefix]
        del active_dashboards[requests_pathname_prefix]
    dash_app = dash.Dash(__name__, requests_pathname_prefix=requests_pathname_prefix)
    return dash_app, requests_pathname_prefix

def mount_dash_app(app, dash_app, requests_pathname_prefix):
    active_dashboards[requests_pathname_prefix] = DashboardInfo(dash_app, dash_app.server, time.time())
    app.mount(requests_pathname_prefix, WSGIMiddleware(dash_app.server))

def generate_sod_rulset_table(app, df, company, table_name, identifier):
    dash_app, requests_pathname_prefix = create_dash_app(app, identifier)
    columns = []
    for i in df.columns:
        column = {}
        column['name'] = i
        column['id'] = i
        column['type'] = 'numeric' if df[i].dtype in ['int64', 'float64'] else 'text'
        if i == 'ENABLED':
            column['editable']= False
        columns.append(column)
    start_selected_rows = []
    for i in range(len(df)):
        if df.iloc[i, 3] == 1:
            start_selected_rows.append(i)
    dash_app.layout = html.Div(
        style={
            'height': '100%'
        },
        children = [
            dash_table.DataTable(
                id=f'{identifier}-datatable-interactivity',
                columns=columns,
                data=df.to_dict('records'),
                filter_action='native',
                sort_action='native',
                row_selectable='multi',
                editable=True,
                page_action='native',
                page_size=20,
                selected_rows=start_selected_rows,
                style_cell=style_cell,
                style_header = style_header,
                style_data=style_data,
                style_cell_conditional = style_cell_conditional,
                style_data_conditional=style_data_conditional,
                fixed_rows=fixed_rows,
                style_table=style_table,
            ),
            html.Button('Add Row', id=f'{identifier}-add-row-button', n_clicks=0),
            html.Div(id=f'{identifier}-hidden-div', style={'display': 'none'}),    
        ]
    )

    @dash_app.callback(
        Output(f'{identifier}-datatable-interactivity', 'data'),
        Output(f'{identifier}-datatable-interactivity', 'selected_rows'),
        Input(f'{identifier}-add-row-button', 'n_clicks'),
        Input(f'{identifier}-datatable-interactivity', "selected_rows"),
        State(f'{identifier}-datatable-interactivity', "derived_virtual_data"),
        State(f'{identifier}-datatable-interactivity', 'data'),
        State(f'{identifier}-datatable-interactivity', 'columns'),
        prevent_initial_call=True
    )
    def update_graph(n_clicks, selected_rows, data, rows, columns):
        triggered_id = ctx.triggered_id
        if triggered_id == f'{identifier}-datatable-interactivity':
            return update_graphs(rows, selected_rows)
        else:
            return add_row(n_clicks, rows, columns, selected_rows)

    def add_row(n_clicks, rows, columns, selected_rows):
        if n_clicks > 0:
            new_row = {column['id']: '' for column in columns}
            rows.append(new_row)
            return rows, selected_rows
        else:
            return df.to_dict('records'), selected_rows

    @dash_app.callback(
        Output(f'{identifier}-hidden-div', 'children'),
        Input(f'{identifier}-datatable-interactivity', 'data'),
        prevent_initial_call=True
    )
    def display_output(rows):
        if rows is not None:
            df_edited = pd.DataFrame(rows)
            if not df_edited.equals(df): 
                #print(df_edited)
                with dynamic_engine(company) as engine:
                    df_edited.to_sql(name=table_name, con= engine, if_exists="replace", index=False)
        else:
            return "Function executed (This is not shown in the app) just to satisfy the callback"
        print("Executed")
    
    def update_graphs(rows, selected_rows):
        temp_rows = rows
        try:
            if len(selected_rows)>0:
                for i in range(len(rows)):
                    if i in selected_rows:
                        rows[i]['ENABLED']=1
                    else:
                        rows[i]['ENABLED']=0
            df_edited = pd.DataFrame(rows)
            with dynamic_engine(company) as engine:
                df_edited.to_sql(name=table_name, con= engine, if_exists="replace", index=False)
        except:
            for i in range(len(temp_rows)):
                if temp_rows[i]['ENABLED']==0:
                    if i in selected_rows:
                        selected_rows.remove(i)
            rows=temp_rows
        return rows, selected_rows
    mount_dash_app(app, dash_app, requests_pathname_prefix)
    return DashResponse(url_complementation=requests_pathname_prefix)

def generate_dash_table(app, df, identifier):
    dash_app, requests_pathname_prefix = create_dash_app(app, identifier)
    columns = [{'name': i, 'id': i, 'type': 'numeric' if df[i].dtype in ['int64', 'float64'] else 'text'} for i in df.columns]
    dash_app.layout = html.Div(
        style={
            'height': '100%'
        },
        children = [
            dash_table.DataTable(
                id=f'{identifier}-datatable-interactivity',
                columns=columns,
                data=df.to_dict('records'),
                filter_action='native',
                sort_action='native',
                editable=False,
                page_action='native',
                page_size=20,
                style_cell = style_cell,
                style_header = style_header,
                style_data = style_data,
                style_cell_conditional = style_cell_conditional,
                style_data_conditional = style_data_conditional,
                fixed_rows = fixed_rows,
                style_table = style_table
            ),
            html.Div(id=f'{identifier}-hidden-div', style={'display': 'none'}),    
        ]
    )
    mount_dash_app(app, dash_app, requests_pathname_prefix)
    return DashResponse(url_complementation=requests_pathname_prefix)

def generate_dash_tables(app, all_data, endpoint):
    dash_app, requests_pathname_prefix = create_dash_app(app, endpoint)
    all_headers = []
    for df in all_data.get('dataframes', []):
        columns = [{'name': i, 'id': i, 'type': 'numeric' if df[i].dtype in ['int64', 'float64'] else 'text'} for i in df.columns]
        all_headers.append(columns)
    all_tables = []
    for i in range(len(all_headers)):
        df = all_data.get('dataframes')[i]
        columns = all_headers[i]
        identifier = all_data.get('identifiers')[i]
        title = all_data.get('titles')[i]
        table = html.Div(
            style={
                'height': '100%'
            },
            children = [
                html.Div(
                    html.H2(title),
                    style={
                        'backgroundColor':'#f0f0f0',
                        'padding': '10px',
                        'margin-bottom': '10px',
                        'border-radius': '5px',
                    }
                ),
                dash_table.DataTable(
                    id=f'{identifier}-datatable-interactivity',
                    columns=columns,
                    data=df.to_dict('records'),
                    filter_action='native',
                    sort_action='native',
                    editable=False,
                    page_action='native',
                    page_size=20,
                    style_cell = style_cell,
                    style_header = style_header,
                    style_data = style_data,
                    style_cell_conditional = style_cell_conditional,
                    style_data_conditional = style_data_conditional,
                    fixed_rows = fixed_rows,
                    style_table = style_table
                ),
                html.Div(id=f'{identifier}-hidden-div', style={'display': 'none'}),
                html.Br(),
                html.Br(),
                html.Br(),    
            ]
        )
        all_tables.append(table)
    dash_app.layout = html.Div(
        [*all_tables]
    )
    mount_dash_app(app, dash_app, requests_pathname_prefix)
    return DashResponse(url_complementation=requests_pathname_prefix)
