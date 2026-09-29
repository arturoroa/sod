from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.responses import RedirectResponse
import dash
import modules.connector
from dash import html, dash_table, dcc
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
from dash import Input, Output, callback
from pydantic import BaseModel
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')


db = modules.connector.connect_db(database='SOA')
engine = create_engine(
    f"mysql+mysqlconnector://{os.getenv('DB_USER', 'dbuser')}:{os.getenv('DB_PASSWORD', 'roandai.1')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/sod",
    echo=False,
)


class SessionData(BaseModel):
    UserID: str
    Type: str
    Company: str
    Email: str
    Phone: str
    Active: str

def fetch_data_from_database(DB,Table,Columns):
    cursor = db.cursor()
    colum_query=''
    for column in Columns:
        colum_query+=f"{column},"
    query_db=f"use {DB}"
    print(query_db)
    cursor.execute(query_db)
    query = f"SELECT {colum_query[:-1]} FROM  {DB}.{Table} "
    print(query)
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data







table= "Multiple_SOD_Count_Combined_a"
company = "SOA"
data = fetch_data_from_database(company,table,["*"])
df_top1 = pd.DataFrame(data)
df_top2 = pd.DataFrame(data)
df_top3 = pd.DataFrame(data)
df_bottom1 = pd.DataFrame(data)
df_bottom2 = pd.DataFrame(data)
df_bottom3= pd.DataFrame(data)

fig_top1=px.pie(df_top1, names=0, values=1)
fig_top2=px.pie(df_top1, names=0, values=1)
fig_top3=px.pie(df_top1, names=0, values=1)
fig_bottom1=px.pie(df_top1, names=0, values=1)
fig_bottom2=px.pie(df_top1, names=0, values=1)
fig_bottom3=px.pie(df_top1, names=0, values=1)


app = dash.Dash(__name__)
app.layout = html.Div(
children=[
    html.Div(
        children=[
            html.Div(
                children=[dcc.Graph(id='graph-top1', figure=fig_top1)],
                style={'display': 'inline-block', 'width': '33%'}
            ),
            html.Div(
                children=[dcc.Graph(id='graph-top2', figure=fig_top2)],
                style={'display': 'inline-block', 'width': '33%'}
            ),
            html.Div(
                children=[dcc.Graph(id='graph-top3', figure=fig_top3)],
                style={'display': 'inline-block', 'width': '33%'}
            ),
        ],
        style={'width': '100%'}
    ),
    # Bottom row with 3 graphs
    html.Div(
        children=[
            html.Div(
                children=[dcc.Graph(id='graph-bottom1', figure=fig_bottom1)],
                style={'display': 'inline-block', 'width': '33%'}
            ),
            html.Div(
                children=[dcc.Graph(id='graph-bottom2', figure=fig_bottom2)],
                style={'display': 'inline-block', 'width': '33%'}
            ),
            html.Div(
                children=[dcc.Graph(id='graph-bottom3', figure=fig_bottom3)],
                style={'display': 'inline-block', 'width': '33%'}
            ),
        ],
        style={'width': '100%'}
    ),
    ]
    )

if __name__ == '__main__':
    app.run_server(debug=True)