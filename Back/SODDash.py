from Models_and_engine import dynamic_engine, DashResponse, insert_logs_dash
from dash import Input, Output, callback, ctx, dcc, html, no_update
from dash.dependencies import Input, Output, State
from fastapi.middleware.wsgi import WSGIMiddleware
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import text
import dash_ag_grid as dag
import pandas as pd
import flask
import dash
import time
import os

pagination_size = 20
active_dashboards = {}

class DashboardInfo:
    def __init__(self, dash_app, flask_server, last_activity):
        self.dash_app = dash_app
        self.flask_server = flask_server
        self.last_activity = last_activity
        self.timer = None

def get_button_style(option):
    style = {
        "color": "white",
        "padding": "10px 20px",
        "border": "none",
        "border-radius": "5px",
        "cursor": "pointer",
        "margin-right": "10px",
        "font-weight": "bold",
    }
    if option==0:
        style["background-color"] = "#3ED402"
    elif option==1:
        style["background-color"] = "#4666CE"
    else:
        style["background-color"] = "#D20103"
    return style

def remove_inactivity_dashboards(app):
    print('REMOVE INACTIVITY DASHBOARDS STARTED')
    count = 0
    try:
        for key in list(active_dashboards.keys()):
            try:
                if time.time() - active_dashboards[key].last_activity >= 1800:
                    app.router.routes = [route for route in app.router.routes if not f'{route.path}/' in key]
                    del active_dashboards[key]
                    count += 1
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    print(f"INACTIVITY DASHBOARDS REMOVED: {count}")

def clear(app, user_id, company, WebSocketID):
    try:
        insert_logs_dash(user_id, company, WebSocketID, "Data Grid", f"Removing all data grids from the user {user_id}")
        for key in list(active_dashboards.keys()):
            try:
                if user_id in key.split('_')[-1]:
                    app.router.routes = [route for route in app.router.routes if not f'{route.path}/' in key]
                    del active_dashboards[key]
            except Exception as e:
                print(e)
        insert_logs_dash(user_id, company, WebSocketID, "Data Grid", "All data grids have been removed")
    except Exception as e:
        print(e)
        insert_logs_dash(user_id, company, WebSocketID, "Data Grid", f"An error has ocurred: {e}")

def create_dash_app(app, identifier) -> dash.Dash:
    requests_pathname_prefix = f'/{identifier}/'
    if requests_pathname_prefix not in active_dashboards:
        #app.router.routes = [route for route in app.router.routes if not f'{route.path}/' in requests_pathname_prefix]
        #del active_dashboards[requests_pathname_prefix]
        dash_app = dash.Dash(__name__, requests_pathname_prefix=requests_pathname_prefix)
    else:
        dash_app = active_dashboards[requests_pathname_prefix].dash_app
    return dash_app, requests_pathname_prefix

def mount_dash_app(app, dash_app, requests_pathname_prefix, user_id, company, WebSocketID):
    if requests_pathname_prefix not in active_dashboards: 
        active_dashboards[requests_pathname_prefix] = DashboardInfo(dash_app, dash_app.server, time.time())
        app.mount(requests_pathname_prefix, WSGIMiddleware(dash_app.server))
        insert_logs_dash(user_id, company, WebSocketID, "Data Grid", f"Data Grid has been created")
    else:
        active_dashboards[requests_pathname_prefix].dash_app = dash_app
        active_dashboards[requests_pathname_prefix].time = time.time()
        insert_logs_dash(user_id, company, WebSocketID, "Data Grid", f"Data Grid has been refreshed")

def get_df_from_table(Company:str, UserID:str, table_name:str, WebSocketID, flag = True):
    if table_name != 'SOD_Rules' and table_name != f'SOD_Rules_{UserID}':
        new_table_name = f'{table_name}_{UserID}'
    else:
        new_table_name = table_name
    with dynamic_engine(Company) as engine:
        insert_logs_dash(UserID, Company, WebSocketID, "Data Extraction", f"Extracting data from {new_table_name} table", flag)
        df = pd.read_sql(f"Select * from {new_table_name}", engine)
        return df
    
def generate_sod_rulset_table(app, company, user_id, WebSocketID, identifier, table_name_0, table_name_1):
    def update_dashboard():
        df_0 = get_df_from_table(company, user_id, table_name_0, WebSocketID, False)
        df_1 = get_df_from_table(company, user_id, table_name_1, WebSocketID, False)
        dataframes = [df_0, df_1]
        dataframes_columns = []
        for i in range(len(dataframes)):
            dataframes[i]['ENABLED'] = dataframes[i]['ENABLED'].apply(lambda x: True if x==1 else False)
            columns=[]
            for j in dataframes[i].columns:
                column = {}
                column['field'] = j
                column['filter'] = True
                column['wrapText'] = True
                column['autoHeight'] = True
                column['cellStyle'] = {'lineHeight': 'unset', 'paddingBottom': '10px'}
                if j.upper() == 'ENABLED':
                    column['editable'] = True
                    column['cellEditor'] = 'agCheckboxCellEditor'
                else:
                    if i > 0:
                        column['editable'] = True
                if dataframes[i][j].dtype in ['int64', 'float64']:
                    column['Type'] = 'numericColumn'
                columns.append(column)
            dataframes_columns.append(columns)
        return html.Div(
            style={
                'height': '100%',
                'marginTop': '20px',
                'marginBottom': '20px'
            },
            children = [
                html.Button(
                    "Clone Selected Rows",
                    id="btn-row-selection-clone-0",
                    style=get_button_style(1)
                ),
                html.Br(),
                html.Br(),
                dag.AgGrid(
                    id=f'{identifier}-grid-0',
                    rowData=dataframes[0].to_dict('records'),
                    columnDefs=dataframes_columns[0],
                    dashGridOptions={
                        'pagination':True,
                        'paginationPageSize': pagination_size,
                        'rowSelection': 'multiple',
                        'undoRedoCellEditing': True,
                        'undoRedoCellEditingLimit': 20,
                    },
                    columnSize='autoSize',
                ),
                dcc.ConfirmDialog(
                    id='modal-row-selected-clone-0',
                    message='Are you sure you want to clone the selected SOD Rules Set?',
                ),
                html.Div(id=f'{identifier}-hidden-div-0', style={'display': 'none'}),
                html.Br(),
                html.Br(),
                html.Button(
                    "Add Row",
                    id="btn-add_row",
                    style=get_button_style(0)
                ),
                html.Button(
                    "Clone Selected Rows",
                    id="btn-row-selection-clone-1",
                    style=get_button_style(1)
                ),
                html.Button(
                    "Remove Selected Rows",
                    id="btn-row-selection-remove",
                    style=get_button_style(2)
                ),
                html.Br(),
                html.Br(),
                dag.AgGrid(
                    id=f'{identifier}-grid-1',
                    rowData=dataframes[1].to_dict('records'),
                    columnDefs=dataframes_columns[1],
                    dashGridOptions={
                        'pagination':True,
                        'paginationPageSize': pagination_size,
                        'rowSelection': 'multiple',
                        'undoRedoCellEditing': True,
                        'undoRedoCellEditingLimit': 20,
                        'editType': 'fullRow',
                    },
                    columnSize='autoSize',
                ),
                dcc.ConfirmDialog(
                    id='modal-row-selected-remove',
                    message='Are you sure you want to delete the selected SOD Rules Set?',
                ),
                dcc.ConfirmDialog(
                    id='modal-row-selected-clone-1',
                    message='Are you sure you want to clone the selected SOD Rules Set?',
                ),
                html.Div(id=f'{identifier}-hidden-div-1', style={'display': 'none'}),
            ]
        )
    dash_app, requests_pathname_prefix = create_dash_app(app, identifier)
    dash_app.layout = update_dashboard
    @callback(
        Output('modal-row-selected-clone-0', 'displayed'),
        Input('btn-row-selection-clone-0', 'n_clicks'),
        State(f'{identifier}-grid-0', 'selectedRows'),
        prevent_initial_call=True,
    )
    def display_clone_dialog_0(n_clicks, selectedRows):
        if selectedRows and len(selectedRows) > 0:
            return True
        return False
    
    @callback(
        Output('modal-row-selected-clone-1', 'displayed'),
        Input('btn-row-selection-clone-1', 'n_clicks'),
        State(f'{identifier}-grid-1', 'selectedRows'),
        prevent_initial_call=True,
    )
    def display_clone_dialog_1(n_clicks, selectedRows):
        if selectedRows and len(selectedRows) > 0:
            return True
        return False

    @callback(
        Output('modal-row-selected-remove', 'displayed'),
        Input('btn-row-selection-remove', 'n_clicks'),
        State(f'{identifier}-grid-1', 'selectedRows'),
        prevent_initial_call=True,
    )
    def display_delete_dialog(n_clicks, selectedRows):
        if selectedRows and len(selectedRows) > 0:
            return True
        return False

    @callback(
        Output(f'{identifier}-grid-0', 'selectedRows'),
        Output(f'{identifier}-grid-1', 'rowData'),
        Output(f'{identifier}-grid-1', 'selectedRows'),
        Output(f'{identifier}-grid-1', 'deleteSelectedRows'),
        Input('modal-row-selected-clone-0', 'submit_n_clicks'),
        Input('btn-add_row', 'n_clicks'),
        Input('modal-row-selected-clone-1', 'submit_n_clicks'),
        Input('modal-row-selected-remove', 'submit_n_clicks'),
        State(f'{identifier}-grid-0', 'selectedRows'),
        State(f'{identifier}-grid-1', 'selectedRows'),
        State(f'{identifier}-grid-1', 'virtualRowData'),
        State(f'{identifier}-grid-1', 'columnDefs'),
        prevent_initial_call=True,
    )
    def clone_selected_rows(submit_n_clicks_clone_0, n_clicks, submit_n_clicks_clone_1, submit_n_clicks_remove, selectedRows_0, selectedRows_1, data, columns):
        if ctx.triggered_id == 'btn-add_row':
            new_row={}
            for column in columns:
                new_row[column['field']]= False if column['field'] == 'ENABLED' else None
            data.append(new_row)
            insert_logs_dash(user_id, company, WebSocketID, "SOD Rule Set", "Adding a new rule", False)
            return no_update, data, no_update, False
        elif  ctx.triggered_id == 'modal-row-selected-remove':
            insert_logs_dash(user_id, company, WebSocketID, "SOD Rule Set", "Deleting selected rules", False)
            return no_update, no_update, [], True
        elif ctx.triggered_id == 'modal-row-selected-clone-0':
            base_df = pd.DataFrame(data)
            selected_df = pd.DataFrame(selectedRows_0)
            new_df = pd.concat([base_df, selected_df], ignore_index=True)
            insert_logs_dash(user_id, company, WebSocketID, "SOD Rule Set", "Cloning selected rules", False)
            return [], new_df.to_dict('records'), no_update, False 
        else:
            base_df = pd.DataFrame(data)
            selected_df = pd.DataFrame(selectedRows_1)
            new_df = pd.concat([base_df, selected_df], ignore_index=True)
            insert_logs_dash(user_id, company, WebSocketID, "SOD Rule Set", "Cloning selected rules", False)
            return no_update, new_df.to_dict('records'), [], False

    @callback(
        Output(f'{identifier}-hidden-div-0', 'children'),
        Input(f'{identifier}-grid-0', 'cellValueChanged'),
        Input(f'{identifier}-grid-0', 'virtualRowData'),
        prevent_initial_call=True
    )
    def update_0(changed, data):
        try:
            new_df = pd.DataFrame(data)
            new_df['ENABLED'] = new_df['ENABLED'].apply(lambda x: 1 if x==True else 0)
            with dynamic_engine(company) as engine:
                new_df.to_sql(name=table_name_0, con=engine, if_exists="replace", index=False)
            insert_logs_dash(user_id, company, WebSocketID, "SOD Rule Set", "SOD Rules Set changes made", False)
        except Exception as e:
            insert_logs_dash(user_id, company, WebSocketID, "SOD Rule Set", f"SOD Rules Set changes canceled: {e}", False)
            print(e)
    
    @callback(
        Output(f'{identifier}-hidden-div-1', 'children'),
        Input(f'{identifier}-grid-1', 'cellValueChanged'),
        Input(f'{identifier}-grid-1', 'virtualRowData'),
        State(f'{identifier}-grid-1', 'columnDefs'),
        prevent_initial_call=True
    )
    def update_1(changed, data, columns):
        try:
            with dynamic_engine(company) as engine:
                if data is None or len(data) == 0:
                    new_columns = [column['field'] for column in columns]
                    new_df = pd.DataFrame(columns=new_columns)
                else:
                    new_df = pd.DataFrame(data)
                    new_df['ENABLED'] = new_df['ENABLED'].apply(lambda x: 1 if x==True else 0)
                new_df.to_sql(name=table_name_1, con=engine, if_exists="replace", index=False)
            insert_logs_dash(user_id, company, WebSocketID, "SOD Rule Set", "SOD Rules Set changes made", False)
        except Exception as e:
            insert_logs_dash(user_id, company, WebSocketID, "SOD Rule Set", f"SOD Rules Set changes canceled: {e}", False)
            print(e)

    mount_dash_app(app, dash_app, requests_pathname_prefix, user_id, company, WebSocketID)
    return DashResponse(url_complementation=requests_pathname_prefix)


def create_grid(df, identifier):
    columns = []
    for i in df.columns:
        column = {}
        column['field'] = i
        column['filter'] = True
        column['wrapText'] = True
        column['autoHeight'] = True
        column['cellStyle'] = {'lineHeight': 'unset', 'paddingBottom': '10px'}
        if df[i].dtype in ['int64', 'float64']:
            column['Type'] = 'numericColumn'
        columns.append(column)
    return dag.AgGrid(
        id=f'{identifier}-grid',
        rowData=df.to_dict('records'),
        columnDefs=columns,
        dashGridOptions={
            'pagination':True,
            'paginationPageSize': pagination_size,
        },
        columnSize='autoSize',
    )


def generate_dash_table(app, company, user_id, WebSocketID, identifier, table_name):
    df = get_df_from_table(company, user_id, table_name, WebSocketID)
    def update_dashboard():
        return html.Div(
            style={
                'height': '100%'
            },
            children = [
                create_grid(df, identifier),
            ]
        )
    dash_app, requests_pathname_prefix = create_dash_app(app, identifier)
    dash_app.layout = update_dashboard
    mount_dash_app(app, dash_app, requests_pathname_prefix, user_id, company, WebSocketID)
    return DashResponse(url_complementation=requests_pathname_prefix)


def generate_dash_tables(app, company, user_id, WebSocketID, complementation, endpoints):
    def update_dashboard():
        all_tables  = []
        with dynamic_engine(company) as engine:
            for endpoint, title in endpoints.items():
                try:
                    df = pd.read_sql(f"SELECT * FROM {endpoint}_{user_id}", engine)
                    identifier = endpoint
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
                            create_grid(df, identifier),
                            html.Br(),
                            html.Br(),
                            html.Br(),    
                        ]
                    )
                    all_tables.append(table)
                except Exception as e:
                    continue
        if len(all_tables) > 0:
            return html.Div(
                [*all_tables]
            )
        else:
            return None
    dash_app, requests_pathname_prefix = create_dash_app(app, complementation)
    dash_app.layout = update_dashboard
    mount_dash_app(app, dash_app, requests_pathname_prefix, user_id, company, WebSocketID)
    return DashResponse(url_complementation=requests_pathname_prefix)

'''def generate_dash_table_filter(app, company, user_id, WebSocketID, identifier, table_name):
    def update_dashboard():
        df = get_df_from_table(company, user_id, table_name, WebSocketID, False)
        return html.Div(
            style={
                'height': '100%'
            },
            children = [
                dcc.Store(id=f'{identifier}-first-load', data={}, storage_type='session'),
                dcc.Location(id=f'{identifier}-url'),
                create_grid(df, identifier),
                html.Div(id=f'{identifier}-hidden-div', style={'display': 'none'}),
            ]
        )
        
    dash_app, requests_pathname_prefix = create_dash_app(app, identifier)
    dash_app.layout = update_dashboard
    @callback(
        Output(f'{identifier}-grid', 'filterModel'),
        Output(f'{identifier}-first-load', 'data'),
        Input(f'{identifier}-grid', 'filterModel'),
        Input(f'{identifier}-url', 'pathname'),
        State(f'{identifier}-grid', 'virtualRowData'),
        State(f'{identifier}-grid', 'columnDefs'),
        State(f'{identifier}-first-load', 'data'),
        prevent_initial_call=True
    )
    def output_filter(filter, path, virtualData, columns, first_load):
        filtered_table = f'{table_name}_Filtered_{user_id}'
        try:
            with dynamic_engine(company) as engine:
                if filter is not None and ((len(first_load)==0) or (first_load!=filter and len(filter)>0)):
                    if virtualData is None or len(virtualData) == 0:
                        new_columns = [column['field'] for column in columns]
                        df_filtered = pd.DataFrame(columns = new_columns)
                    else:
                        df_filtered = pd.DataFrame(virtualData)
                    df_filtered.to_sql(name=filtered_table, con=engine, if_exists="replace", index=False)  
                    return no_update, filter
                else:
                    print('FILTER: ', first_load)
                    print('FIRST LOAD: ', first_load)
                    if filter is None and len(first_load)>0:
                        print('449')
                        print(first_load, first_load)
                        return first_load, first_load
                    else:
                        if virtualData is None or len(virtualData)==0:
                            new_columns = [column['field'] for column in columns]
                            df_filtered = pd.DataFrame(columns = new_columns)
                        else:
                            df_filtered = pd.DataFrame(virtualData)
                        df_filtered.to_sql(name=filtered_table, con=engine, if_exists="replace", index=False)
                        print(458)
                        print(filter)
                        if filter:
                            return filter, filter
                        else:
                            return no_update, no_update
        except Exception as e:
            print(e)
            insert_logs_dash(user_id, company, WebSocketID, f"Filter Table", f"An error occurred while filtering table {filtered_table}: {e}", False)
    mount_dash_app(app, dash_app, requests_pathname_prefix, user_id, company, WebSocketID)
    return DashResponse(url_complementation=requests_pathname_prefix)'''

def generate_dash_table_filter(app, company, user_id, WebSocketID, identifier, table_name, file_name):
    def update_dashboard():
        df = get_df_from_table(company, user_id, table_name, WebSocketID, False)
        if (table_name == 'Role_Level_Conflicts'):
            df.rename(columns={'Name': 'SOD Rule'}, inplace=True)
            df = df.sort_values(by='Role')
        if (table_name == 'Single_Role_Conflicts'):
            df = df[['Name', 'Email', 'Phone', 'Conflict Details', 'SOD Rule']]
        columns = []
        for i in df.columns:
            column = {}
            column['field'] = i
            column['filter'] = True
            column['wrapText'] = True
            column['autoHeight'] = True
            column['cellStyle'] = {'lineHeight': 'unset', 'paddingBottom': '10px'}
            if df[i].dtype in ['int64', 'float64']:
                column['Type'] = 'numericColumn'
            columns.append(column)
        return html.Div(
            style={
                'height': '100%'
            },
            children = [
                dag.AgGrid(
                    id=f'{identifier}-grid',
                    rowData=df.to_dict('records'),
                    columnDefs=columns,
                    dashGridOptions={
                        'pagination':True,
                        'paginationPageSize': pagination_size,
                    },
                    columnSize='autoSize',
                    csvExportParams={
                        "fileName": file_name,
                    },
                ),
                html.Div(
                    [
                        html.Button(
                            "Download CSV",
                            id=f"{identifier}-btn",
                            style=get_button_style(0)
                        ),
                    ],
                    style={
                        'marginTop': '20px',
                        'width': '100%',
                        'display': 'flex',
                        'justifyContent': 'center'
                    }
                ),
            ]
        )
        
    dash_app, requests_pathname_prefix = create_dash_app(app, identifier)
    dash_app.layout = update_dashboard
    @callback(
        Output(f"{identifier}-grid", "exportDataAsCsv"),
        Input(f"{identifier}-btn", 'n_clicks'),
    )
    def output_filter(n_clicks):
        if n_clicks:
            try:
                insert_logs_dash(user_id, company, WebSocketID, f"Filter Table", f"User {user_id} has downloaded the file {file_name}", False)
                return True
            except Exception as e:
                insert_logs_dash(user_id, company, WebSocketID, f"Filter Table", f"An error occurred while filtering table {table_name}: {e}", False)
                return False
        return False
    mount_dash_app(app, dash_app, requests_pathname_prefix, user_id, company, WebSocketID)
    return DashResponse(url_complementation=requests_pathname_prefix)


#################################### DASHBOARDS ##############################################

def fetch_data_from_database(DB, Table, Columns, condition, grouping, engine):
    column_query = ', '.join(Columns) if Columns != ["*"] else "*"
    query = text(f"SELECT {column_query} FROM {DB}.{Table} {condition} {grouping}")
    print("THIS IS THE QUERY", query)
    return pd.read_sql(query, engine)

def create_dashboard(app, company, user_id, WebSocketID, identifier):
    insert_logs_dash(user_id, company, WebSocketID, "Dashboard", f"Genereting dashboard")
    def update_dashboard():
        figs = []
        with dynamic_engine(company) as engine:
            table=f"Merged_Users_to_Permissions_{user_id}"
            df = fetch_data_from_database(company, table, ["Name","LENGTH(Name)","COUNT(*) AS counter"], "", "group BY 'Name',LENGTH(Name) ORDER BY counter DESC", engine)
            #df = df.head(9)  # Get top 9 rows
            df=df[0:9]
            if len(df.columns) > 1:
                fig = px.pie(df, names=df.columns[0], values=df.columns[1])
                fig.update_layout(
                    title={"text" : f"Users with the most conflicts",'x': 0.5,'xanchor': 'center'},
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='black'
                )
                figs.append(fig)
    
            table = f"Single_Role_Conflicts_{user_id}"
            df = fetch_data_from_database(company, table, ["DISTINCT Name","Role"],"", "ORDER BY 'Name', Role", engine)
            #df = df.head(35)  # Get top 9 rows
            df = df[df["Role"] != "None"]
            df=df[0:60]
            #print(df)
            df_pivot = df.pivot_table(index='Name', columns='Role', aggfunc='size', fill_value=0)
            if len(df.columns) > 1:
                fig = go.Figure(data=go.Heatmap(
                    z=df_pivot.values,
                    x=df_pivot.columns,
                    y=df_pivot.index,
                    colorscale='YlOrRd'
                ))
                fig.update_layout(
                    title={'text': 'First 60 Users/Roles Confilcts','x': 0.5,'xanchor': 'center'},
                    xaxis_title='Roles',
                    yaxis_title='Employees',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='black'
                )
                figs.append(fig)
    
            table = f"Multiple_SOD_Count_Combined_{user_id}"
            df = fetch_data_from_database(company, table, ["*"], "", "ORDER BY 'SOD Rule' DESC", engine)
            #df = df.head(9)  # Get top 9 rows
            df=df[0:9]
            if len(df.columns) > 1:
                fig = px.pie(df, names=df.columns[0], values=df.columns[1])
                fig.update_layout(
                    title={"text":f"Top 10 Roles with the most conflicts",'x': 0.5,'xanchor': 'center'},
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='black'
                )
                figs.append(fig)
        
            table = f"SOD_List_Count_{user_id}"
            df = fetch_data_from_database(company, table, ["*"], "", "ORDER BY 'SOD Rule' DESC", engine)
            #df = df.head(9)  # Get top 9 rows
            df=df[0:9]
            if len(df.columns) > 1:
                fig = px.pie(df, names=df.columns[0], values=df.columns[1])
                fig.update_layout(
                    title={"text":f"Top 10 Conflict Names with the most conflicts",'x': 0.5,'xanchor': 'center'},
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='black'
                )
            figs.append(fig)
        return html.Div(
            [
                # Header with gradient background and modern styling
                html.Header(
                    [
                        html.H1(f"{user_id} @ {company}", 
                            style={
                                'color': 'white', 
                                'textAlign': 'center', 
                                'padding': '20px', 
                                'background': 'linear-gradient(135deg, #6a11cb 0%, #2575fc 100%)',
                                'borderRadius': '0 0 10px 10px',
                                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                            }
                        )
                    ]
                ),
                # First row of graphs with responsive grid layout
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Graph(
                                    id=f'graph-{i+1}', 
                                    figure=fig,
                                    style={'height': '400px'}
                                )
                            ],
                            style={
                                'width': '50%', 
                                'padding': '10px', 
                                'boxSizing': 'border-box',
                                'borderRadius': '10px',
                                'background': 'rgba(255,255,255,0.8)',
                                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                            }
                        ) for i, fig in enumerate(figs[:2])
                    ],
                    style={
                        'display': 'flex', 
                        'justifyContent': 'space-between', 
                        'width': '100%', 
                        'marginBottom': '20px'
                    }
                ),
                # Second row of graphs with responsive grid layout
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Graph(
                                    id=f'graph-{i+4}', 
                                    figure=fig,
                                    style={'height': '400px'}
                                )
                            ],
                            style={
                                'width': '50%', 
                                'padding': '10px', 
                                'boxSizing': 'border-box',
                                'borderRadius': '10px',
                                'background': 'rgba(255,255,255,0.8)',
                                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                            }
                        ) for i, fig in enumerate(figs[2:])
                    ],
                    style={
                        'display': 'flex', 
                        'justifyContent': 'space-between', 
                        'width': '100%'
                    }
                )
            ],
            style={
                'backgroundColor': '#f0f4f8',  # Soft blue-gray background
                'padding': '20px', 
                'fontFamily': 'Arial, sans-serif',
                'maxWidth': '1200px',
                'margin': '0 auto',
                'borderRadius': '15px',
                'boxShadow': '0 10px 25px rgba(0,0,0,0.1)'
            }
        )
    dash_app, requests_pathname_prefix = create_dash_app(app, identifier)
    dash_app.layout = update_dashboard
    mount_dash_app(app, dash_app, requests_pathname_prefix, user_id, company, WebSocketID)
    return DashResponse(url_complementation=requests_pathname_prefix)


######### STACK FUNCTIONS #######

def create_stack_bar(title, df, x_index, y_index, count_index, labels = None):
    fig = go.Figure()
    x_list = df[x_index].unique().tolist()
    y_list = df[y_index].unique().tolist() if labels is None else labels
    for y_label in y_list:
        filtered_df = df[df[y_index]==y_label]
        values = [0 for x_label in x_list]
        for x_label, value in zip(filtered_df[x_index], filtered_df[count_index]):
            try:
                index = x_list.index(x_label)
                values[index] = value
            except:
                pass
        if len(values) == 0:
            values = [0]
            x_list = ['']
        fig.update_layout(title = {"text": title, 'x': 0.5, 'xanchor': 'center'},)
        fig.add_trace(go.Bar(x=x_list, y=values, name=y_label))
    fig.update_layout(barmode='stack')
    if not df.empty:
        labels_in_fig = df[y_index].unique().tolist()
        labels_not_found = [label for label in y_list if label not in labels_in_fig]
        for i in range(len(fig['data'])):
            if fig['data'][i]['name'] in labels_not_found:
                fig['data'][i]['visible'] = 'legendonly'
            else:
                fig['data'][i]['visible'] = True
    else:
        for i in range(len(fig['data'])):
            fig['data'][i]['visible'] = 'legendonly'
    return fig

def display_legend_click_stack(restyleData, fig, column_filter, df, pie=None, x_index=None):
    if restyleData is not None and len(restyleData) > 0:
        if 'visible' in restyleData[0]:
            removed = []
            count = 0
            if len(restyleData[0]['visible']) > 1:
                for value in restyleData[0]['visible']:
                    if value is True:
                        count += 1
            if count < len(df[column_filter].unique().tolist()):
                for label in fig['data']:
                    if 'visible' in label and label['visible']=='legendonly':
                        removed.append(label['name'])
            df_filtered = df[~df[column_filter].isin(removed)]
            if pie is not None:
                if 'hiddenlabels' in pie['layout']:
                    pie_hiddenlabels = pie['layout']['hiddenlabels']
                    df_filtered = df_filtered[~df_filtered[x_index].isin(pie_hiddenlabels)]
            return df_filtered.to_dict('records')
    else:
        return no_update

def output_filter_stack(virtualRowData, columns, fig, column_filter, df, title, x_index, count_index):
    if virtualRowData is None or len(virtualRowData) == 0:
        new_columns = [column['field'] for column in columns]
        df_filtered = pd.DataFrame(columns = new_columns)
    else:
        df_filtered = pd.DataFrame(virtualRowData)
    all_labels = df[column_filter].unique().tolist()
    new_figure = create_stack_bar(title, df_filtered, x_index, column_filter, count_index, all_labels)
    return new_figure


########### PIE CHART ##########################################

def create_pie_chart(title, df, x_index):
    new_df = df.groupby([x_index]).size().reset_index(name='Count')
    fig = px.pie(new_df, names=new_df.columns[0], values=new_df.columns[1])
    fig.update_layout(
        title = {"text": title, 'x': 0.5, 'xanchor': 'center'},
        plot_bgcolor = 'rgba(0,0,0,0)',
        paper_bgcolor = 'rgba(0,0,0,0)',
        font_color = 'black',
        uniformtext_minsize = 10,
        uniformtext_mode = 'hide'
    )
    fig.update_traces(textinfo='value', textposition='inside')
    return fig

def update_pie_chart(table, virtualRowData, x_index, fig):
    all_labels = table['dataframe'][x_index].unique().tolist()
    if virtualRowData is None or len(virtualRowData) == 0:
        hiddenlabels = all_labels
    else:
        df = pd.DataFrame(virtualRowData)
        labels = df[x_index].unique().tolist()
        hiddenlabels = [label for label in all_labels if label not in labels]
        new_data = df.groupby([x_index]).size().reset_index(name='Count')
        for label, count in zip(new_data[x_index], new_data['Count']):
            try:
                index = fig['data'][0]['labels'].index(label)
                fig['data'][0]['values'][index] = count
            except:
                pass
    fig['layout']['hiddenlabels'] = hiddenlabels    
    return fig

def display_legend_click_pie(relayoutData, df, x_index, columnDefs):
    if relayoutData and 'hiddenlabels' in relayoutData:
        hiddenlabels = relayoutData['hiddenlabels']
        df = df[~df[x_index].isin(hiddenlabels)]
        return df.to_dict('records')
    return no_update


########### GENERAL CALLBACK ###################################

def general_callback(table, x_index, y_index, count_index):
    @callback(
        Output(f'{table["identifier"]}-grid', 'rowData'),
        Output(f'{table["identifier"]}-stack', 'figure'),
        Input(f'{table["identifier"]}-grid', 'virtualRowData'),
        Input(f'{table["identifier"]}-stack', 'restyleData'),
        Input(f'{table["identifier"]}-pie', 'relayoutData'),
        State(f'{table["identifier"]}-grid', 'columnDefs'),
        State(f'{table["identifier"]}-stack', 'figure'),
        State(f'{table["identifier"]}-pie', 'figure'),
        prevent_initial_call=True
    )
    def stack_chart_function(virtualRowData, restyleData, relayoutData, columnDefs, figure, figure2):
        if ctx.triggered_id == f'{table["identifier"]}-grid':
            return no_update, output_filter_stack(virtualRowData, columnDefs, figure, y_index, table['dataframe'], table['title'], x_index, count_index)
        elif ctx.triggered_id == f'{table["identifier"]}-stack':
            return display_legend_click_stack(restyleData, figure, y_index, table['dataframe'], figure2, x_index), no_update
        else:
            return display_legend_click_pie(relayoutData, table['dataframe'], x_index, columnDefs), no_update


########### GENERAL DIVs ############################

def create_div_chart(type, identifier, args):
    if type == 'stack':
        fig = create_stack_bar(*args)
    else:
        fig = create_pie_chart(*args)
    return html.Div(
        [
            dcc.Graph(
                id=identifier, 
                figure=fig,
                style={'height': '400px'}
            )
        ],
        style={
            'flex': '1',
            'max-width': '100%',
            'min-width': '500px',
            'padding': '10px', 
            'boxSizing': 'border-box',
            'borderRadius': '10px',
            'background': 'rgba(255,255,255,0.8)',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
        }
    )

def create_div_grid(df, identifier):
    return html.Div(
        [
            html.Div(
                [
                    create_grid(df, identifier),
                ],
                style={'width':'90%', 'marginBottom': '10px'}
            ),
        ],
        style={
            'flex': '1',
            'min-width': '500px',
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center',
            'marginTop': '10px',
        }
    )

div_style = {
    'display': 'flex', 
    'justifyContent': 'space-between', 
    'width': '100%',
    'marginBottom': '10px',
    'flexWrap': 'wrap',
}

def create_component(table, x_index, y_index, count_index):
    return html.Div(
        [
            html.Div(
                [
                    create_div_chart('pie', f'{table["identifier"]}-pie', [table['title'], table['dataframe'], x_index]),
                    create_div_grid(table['dataframe'], table['identifier']),
                ],
                style=div_style
            ),
            create_div_chart(table['chartType'], f'{table["identifier"]}-{table["chartType"]}', [table['title'], table['dataframe'], x_index, y_index, count_index]),
        ],
        style={
            'marginBottom': '50px',
        }
    )


################ INTERACTIVE DASHBOARD ##############################

def create_interactive_dashboard(app, company, user_id, WebSocketID, identifier):
    insert_logs_dash(user_id, company, WebSocketID, "Dashboard", f"Genereting dashboard")
    tables = [
        {
            "title": "Top 10 Max Business Cycle Per Role",
            "chartType": "stack",
            "query": f'''WITH Top_10 AS (
                            SELECT `Role`, COUNT(*) AS `Count`
                            FROM(
                                SELECT `Role`, `Business Cycle`
                                FROM `Role_Level_Conflicts_{user_id}`
                                GROUP BY `Role`, `Business Cycle`
                            ) AS `Simplified`
                            GROUP BY `Role`
                            ORDER BY `Count` DESC
                            LIMIT 10
                        )
                        SELECT s1.`Role`, s1.`Business Cycle`, COUNT(*) AS `Count`
                        FROM `Role_Level_Conflicts_{user_id}` AS s1
                        INNER JOIN `Top_10` AS s2 ON s1.`Role`=s2.`Role`
                        GROUP BY `Role`, `Business Cycle`;''',
            "identifier": f"{user_id}-0"
        },
        {
            "title": "Top 10 SOD Rule Count by Business Process",
            "chartType": "stack",
            "query": f'''WITH Top_10 AS (
                            SELECT `Business Process`, COUNT(*) AS `Count`
                            FROM(
                                SELECT `Business Process`, `Name` AS `SOD Rule`
                                FROM `Role_Level_Conflicts_{user_id}`
                                GROUP BY `Business Process`, `SOD Rule`
                            ) AS `Simplified`
                            GROUP BY `Business Process`
                            ORDER BY `Count` DESC
                            LIMIT 10
                        )
                        SELECT s1.`Business Process`, s1.`Name` AS `SOD Rule`, COUNT(*) AS `Count`
                        FROM `Role_Level_Conflicts_{user_id}` AS s1
                        INNER JOIN `Top_10` AS s2 ON s1.`Business Process`=s2.`Business Process`
                        GROUP BY `Business Process`, `SOD Rule`;''',
            "identifier": f"{user_id}-1"
        },
        {
            "title": "Top 10 Total Users by Business Process",
            "chartType": "stack",
            "query": f'''WITH Top_10 AS (
                            SELECT `Business Process`, COUNT(*) AS `Count`
                            FROM(
                                SELECT `Business Process`, `Name` AS `User`
                                FROM `Single_Role_Conflicts_{user_id}`
                                GROUP BY `Business Process`, `User`
                            ) AS `Simplified`
                            GROUP BY `Business Process`
                            ORDER BY `Count` DESC
                            LIMIT 10
                        )
                        SELECT s1.`Business Process`, s1.`Name` AS `User`, COUNT(*) AS `Count`
                        FROM `Single_Role_Conflicts_{user_id}` AS s1
                        INNER JOIN `Top_10` AS s2 ON s1.`Business Process`=s2.`Business Process`
                        GROUP BY `Business Process`, `User`;''',
            "identifier": f"{user_id}-2"
        },
        {
            "title": "Top 10 Users with more conflicts",
            "chartType": "stack",
            "query": f'''WITH Top_10 AS (
                            SELECT `User`, COUNT(*) AS `Count`
                            FROM(
                                SELECT `Name` AS `User`, `SOD Rule`
                                FROM `Single_Role_Conflicts_{user_id}`
                                GROUP BY `Name`, `SOD Rule`
                            ) AS `Simplified`
                            GROUP BY `User`
                            ORDER BY `Count` DESC
                            LIMIT 10
                        )
                        SELECT s1.`Name` AS `User`, s1.`SOD Rule`, COUNT(*) AS `Count`
                        FROM `Single_Role_Conflicts_{user_id}` AS s1
                        INNER JOIN `Top_10` AS s2 ON s1.`Name`=s2.`User`
                        GROUP BY `Name`, `SOD Rule`;''',
            "identifier": f"{user_id}-3"
        },
    ]
    def update_dashboard():
        dashboards = []
        with dynamic_engine(company) as engine:
            for i in range(len(tables)):
                try:
                    df = pd.read_sql(tables[i]['query'], engine)
                    tables[i]['dataframe'] = df
                except Exception as e:
                    insert_logs_dash(user_id, company, WebSocketID, f"Dashboard", f"An error has occurred: {e}", False)
        
        ######## FIRST COMPONENT #########
        if 'dataframe' in tables[0] and tables[0]['dataframe'].empty == False:
            div = create_component(tables[0], 'Role', 'Business Cycle', 'Count')
            dashboards.append(div)

        ####### SECOND COMPONENT #########
        if 'dataframe' in tables[1] and tables[1]['dataframe'].empty == False:
            div = create_component(tables[1], 'Business Process', 'SOD Rule', 'Count')
            dashboards.append(div)

        ####### THIRD COMPONENT #########
        if 'dataframe' in tables[2] and tables[2]['dataframe'].empty == False:
            div = create_component(tables[2], 'Business Process', 'User', 'Count')
            dashboards.append(div)

        ####### FOURTH COMPONENT #########
        if 'dataframe' in tables[3] and tables[3]['dataframe'].empty == False:
            div = create_component(tables[3], 'User', 'SOD Rule', 'Count')
            dashboards.append(div)

        ###### PRINCIPAL COMPONENT ########
        return html.Div(
            [
                # Header with gradient background and modern styling
                html.Header(
                    [
                        html.H1(f"{user_id} @ {company}", 
                            style={
                                'color': 'white', 
                                'textAlign': 'center', 
                                'padding': '20px', 
                                'background': 'linear-gradient(135deg, #6a11cb 0%, #2575fc 100%)',
                                'borderRadius': '0 0 10px 10px',
                                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                            }
                        )
                    ]
                ),
                html.Div(
                    [*dashboards]
                )
            ],
            style={
                #'backgroundColor': '#f0f4f8',  # Soft blue-gray background
                'padding': '20px', 
                'fontFamily': 'Arial, sans-serif',
                'maxWidth': '1200px',
                'margin': '0 auto',
                'borderRadius': '15px',
                'boxShadow': '0 10px 25px rgba(0,0,0,0.1)'
            }
        )

    dash_app, requests_pathname_prefix = create_dash_app(app, identifier)
    dash_app.layout = update_dashboard
    
    ####### CALLBACKS ######
    if 'dataframe' in tables[0] and tables[0]['dataframe'].empty == False:
        general_callback(tables[0], 'Role', 'Business Cycle', 'Count')
    if 'dataframe' in tables[1] and tables[1]['dataframe'].empty == False:
        general_callback(tables[1], 'Business Process', 'SOD Rule', 'Count')
    if 'dataframe' in tables[2] and tables[2]['dataframe'].empty == False:
        general_callback(tables[2], 'Business Process', 'User', 'Count')
    if 'dataframe' in tables[3] and tables[3]['dataframe'].empty == False:
        general_callback(tables[3], 'User', 'SOD Rule', 'Count')
    
    mount_dash_app(app, dash_app, requests_pathname_prefix, user_id, company, WebSocketID)
    return DashResponse(url_complementation=requests_pathname_prefix)
    