import modules.connector
import dash
from dash import dcc
from dash import html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
from dash import Input, Output, callback
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')


db = modules.connector.connect_db(database='SOA')
engine = create_engine(
    f"mysql+mysqlconnector://{os.getenv('DB_USER', 'dbuser')}:{os.getenv('DB_PASSWORD', 'roandai.1')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/SOA",
    echo=False,
)

def fetch_data_from_database():
    cursor = db.cursor()
    query = "SELECT * FROM Merged_Users_to_Permissions_Filtered_a"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data

df = pd.read_sql("SELECT * FROM Merged_Users_to_Permissions_Filtered_a", con=engine)

columns = [{'name': i, 'id': i, 'type': 'numeric' if df[i].dtype in ['int64', 'float64'] else 'text'} for i in df.columns]

app = dash.Dash(__name__)

app.layout = html.Div([
    dash_table.DataTable(
        id='datatable-interactivity',
        columns=columns,
        data=df.to_dict('records'),
        filter_action='native',
        editable=True,
        page_action='native',
        page_size=18
    ),
    html.Button('Add Row', id='add-row-button', n_clicks=0),
    html.Div(id='hidden-div', style={'display': 'none'})
])

@app.callback(
    Output('datatable-interactivity', 'data'),
    Input('add-row-button', 'n_clicks'),
    State('datatable-interactivity', 'data'),
    State('datatable-interactivity', 'columns'),
    prevent_initial_call=True
)
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        new_row = {column['id']: '' for column in columns}
        rows.append(new_row)
        return rows
    else:
        return df.to_dict('records')

@app.callback(
    Output('hidden-div', 'children'),
    Input('datatable-interactivity', 'data'),
    prevent_initial_call=True
)
def display_output(rows):
    if rows is not None:
        df_edited = pd.DataFrame(rows)
        if not df_edited.equals(df): 
            print(df_edited)
            df_edited.to_sql('Merged_Users_to_Permissions_Filtered_SOA_a', con=engine, if_exists='replace', index=False)
    else:
        return "Function executed (This is not shown in the app) just to satisfy the callback"
    print("Executed")

if __name__ == '__main__':
    app.run_server(debug=True)