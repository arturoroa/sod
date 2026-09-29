from fastapi import FastAPI, APIRouter
from fastapi.middleware.wsgi import WSGIMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import dash
from fastapi.middleware.cors import CORSMiddleware
from dash import html, dcc
import plotly.express as px
import pandas as pd
import asyncio
from contextlib import contextmanager
import time
from threading import Timer
import plotly.graph_objects as go
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

# Database connection
def dynamic_engine(database:str):
    return create_engine(
        f"mysql+mysqlconnector://{os.getenv('DB_USER', 'dbuser')}:{os.getenv('DB_PASSWORD', 'roandai.1')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{database}",
        echo=False,
    )

app = FastAPI()

class DashboardRequest(BaseModel):
    UserID: str
    Company: str

origins = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ORIGINS',
        'https://localhost:8000,https://localhost:8081,http://localhost:8000,http://localhost:8081',
    ).split(',')
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DashboardInfo:
    def __init__(self, dash_app, flask_server, last_activity):
        self.dash_app = dash_app
        self.flask_server = flask_server
        self.last_activity = last_activity
        self.timer = None

# Dictionary to store active dashboards
active_dashboards = {}

def fetch_data_from_database(DB, Table, Columns, condition, grouping):
    engine = dynamic_engine(DB)
    column_query = ', '.join(Columns) if Columns != ["*"] else "*"
    query = text(f"SELECT {column_query} FROM {DB}.{Table} {condition} {grouping}")
    print("THIS IS THE QUERY", query)
    return pd.read_sql(query, engine)

def create_dashboard(user_id, company):
    print(f"Creating dashboard for {user_id}")
    
    tables = [
        "Multiple_SOD_Count_Combined_a",
        "SOD_List_Count_a",
        "Multiple_SOD_Count_Combined_a",
        "Multiple_SOD_Count_Combined_a",
        "Multiple_SOD_Count_Combined_a",
        "Multiple_SOD_Count_Combined_a"
    ]
    
    figs = []
    
    table="Merged_Users_to_Permissions_a"
    df = fetch_data_from_database(company, table, ["Name_x","LENGTH(Name_x)","COUNT(*) AS counter"], "", "group BY 'Name_x',LENGTH(Name_x) ORDER BY counter DESC")
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
    

    
    table = "Single_Role_Conflicts_a"
    
    df = fetch_data_from_database(company, table, ["DISTINCT Name","Role"],"", "ORDER BY 'Name_x', Role")
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
                colorscale='YlOrRd'))

        fig.update_layout(
                title={'text': 'First 60 Users/Roles Confilcts','x': 0.5,'xanchor': 'center'},
                xaxis_title='Roles',
                yaxis_title='Employees',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='black'
                )

        figs.append(fig)
    
    
    
    
    
    
    
    
    
    table="Multiple_SOD_Count_Combined_a"
    df = fetch_data_from_database(company, table, ["*"], "", "ORDER BY 'SOD Rule' DESC")
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
        
    table="SOD_List_Count_a"
    df = fetch_data_from_database(company, table, ["*"], "", "ORDER BY 'SOD Rule' DESC")
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
    
    
    '''
    for table in tables:
        df = fetch_data_from_database(company, table, ["*"], "", "ORDER BY 'SOD Rule' DESC")
        df = df.head(9)  # Get top 9 rows
        
        if len(df.columns) > 1:
            fig = px.pie(df, names=df.columns[0], values=df.columns[1], title=f"Chart for {table}")
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='black'
            )
            figs.append(fig)
    '''

    dash_app = dash.Dash(__name__, requests_pathname_prefix=f"/dash/{user_id}/")
    dash_app.layout = html.Div([
        html.H1(f"{user_id} @ {company}", style={'color': 'black', 'textAlign': 'center','backgroundColor': '#0000FD','height': '75%'}),
        html.Div([
            html.Div([dcc.Graph(id=f'graph-{i+1}', figure=fig)], 
                     style={'width': '50%', 'display': 'inline-block','height': '75%'})
            for i, fig in enumerate(figs[:2])
        ], style={'display': 'inline-block', 'justifyContent': 'space-between', 'width': '90%', 'height': '75%'}),#'marginBottom': '20px','marginLeft': '10px','marginRight': '20px',
        html.Div([
            html.Div([dcc.Graph(id=f'graph-{i+4}', figure=fig)], 
                     style={'display': 'inline-block', 'width': '40%','height': '75%'})
            for i, fig in enumerate(figs[2:])
        ], style={'width': '100%', 'font_color': 'black','height': '75%'}),
        html.Div([
        #    html.Hr(style={'border': 'none','borderTop': '2px solid black','width': '70%','margin': '10px 0'})
        #        ], style={'color': 'black', 'textAlign': 'center', 'backgroundColor': '#0000FD','height': '75%'}) 
    #], style={'backgroundColor': '#82EEFD', 'padding': '20px', 'color': 'black', 'height': '75%',  'overflow': 'hidden'})
    return DashboardInfo(dash_app, dash_app.server, time.time())

def stop_and_remove_dashboard(user_id):
    if user_id in active_dashboards:
        dashboard_info = active_dashboards[user_id]
        # Cancel the timer if it exists
        if dashboard_info.timer:
            dashboard_info.timer.cancel()
        
        # Unmount the Dash application from FastAPI
        app.router.routes = [route for route in app.router.routes if not route.path.startswith(f"/dash/{user_id}")]
        
        # Remove the dashboard from the dictionary
        del active_dashboards[user_id]
        
        print(f"Dashboard for {user_id} stopped and removed")
    else:
        print(f"No active dashboard found for {user_id}")

def check_inactivity(user_id):
    if user_id in active_dashboards:
        dashboard_info = active_dashboards[user_id]
        if time.time() - dashboard_info.last_activity > 300:  # 5 minutes of inactivity
            stop_and_remove_dashboard(user_id)
        else:
            # Schedule the next check
            dashboard_info.timer = Timer(60, check_inactivity, args=[user_id])
            dashboard_info.timer.start()

@app.post("/dashboard")
async def get_dashboard(request: DashboardRequest):
    user_id = request.UserID
    company = request.Company
    print(f"Received request for {user_id}, {company}")

    # Check if a dashboard already exists for this user
    if user_id in active_dashboards:
        print(f"Removing existing dashboard for {user_id}")
        stop_and_remove_dashboard(user_id)

    # Create a new dashboard
    dashboard_info = create_dashboard(user_id, company)
    active_dashboards[user_id] = dashboard_info

    print(f"Mounting new dashboard for {user_id}")
    app.mount(f"/dash/{user_id}", WSGIMiddleware(dashboard_info.flask_server))

    # Start the timer to check for inactivity
    dashboard_info.timer = Timer(60, check_inactivity, args=[user_id])
    dashboard_info.timer.start()

    dashboard_url = f"http://localhost:8000/dash/{user_id}/"
    return {"dashboard_url": dashboard_url}

@app.post("/update_activity")
async def update_activity(request: DashboardRequest):
    user_id = request.UserID
    if user_id in active_dashboards:
        active_dashboards[user_id].last_activity = time.time()
        return {"message": f"Activity updated for {user_id}"}
    return {"message": f"No active dashboard found for {user_id}"}

@app.post("/stop_dashboard")
async def stop_dashboard(request: DashboardRequest):
    user_id = request.UserID
    stop_and_remove_dashboard(user_id)
    return {"message": f"Dashboard for {user_id} stopped and removed"}

async def cleanup_inactive_dashboards():
    while True:
        await asyncio.sleep(3600)  # Wait for 1 hour
        for user_id in list(active_dashboards.keys()):
            # Here you can add logic to determine if a dashboard is inactive
            stop_and_remove_dashboard(user_id)

@app.on_event("startup")
async def start_cleanup_task():
    asyncio.create_task(cleanup_inactive_dashboards())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("TestFast:app", host="0.0.0.0", port=8000,reload=False)
