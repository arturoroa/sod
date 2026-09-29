import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import mysql.connector
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env', override=True)

# Initialize Dash app
app = dash.Dash(__name__)

# MySQL connection parameters
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'dbuser'),
    'password': os.getenv('DB_PASSWORD', 'roandai.1'),
    'database': 'SOA'
}

# Function to fetch data from MySQL
def fetch_data_from_mysql():
    try:
        conn = mysql.connector.connect(**db_config)
        query = "SELECT * FROM Single_Role_Conflicts_Alex"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error connecting to MySQL database: {e}")
        return pd.DataFrame()

# Fetch data once at the start
df = fetch_data_from_mysql()

# Layout of the app
app.layout = html.Div([
    html.H1("AIVER Data Analyzer Version 3", style={'textAlign': 'center'}),

    dcc.Dropdown(
        id="column-dropdown",
        options=[{"label": col, "value": col} for col in df.columns],
        value=df.columns[0] if len(df.columns) > 0 else None,
        style={'width': '50%', 'margin': 'auto', 'marginTop': '20px'}
    ),

    dcc.Graph(id="plotly-chart"),

    html.Div(id="data-table-container", style={'margin': '20px'}),

    html.Div(id="summary-stats", style={'margin': '20px', 'fontSize': '16px'})
])

@app.callback(
    Output("data-table-container", "children"),
    [Input("column-dropdown", "value"),
     Input("plotly-chart", "clickData")]
)
def update_data_table(selected_column, clickData):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Initial load, show full data preview
        table_data = df.head(10)
        title = "Data Preview"
    elif ctx.triggered[0]['prop_id'] == 'plotly-chart.clickData':
        # Drill-down when chart is clicked
        if clickData and selected_column:
            clicked_value = clickData["points"][0]["x"]
            if df[selected_column].dtype in ['int64', 'float64']:
                table_data = df[df.index == clicked_value]
            else:
                table_data = df[df[selected_column] == clicked_value]
            title = f"Drill-Down Details for {selected_column}: {clicked_value}"
        else:
            table_data = df.head(10)
            title = "Data Preview"
    else:
        # Column selection changed, show full data preview
        table_data = df.head(10)
        title = "Data Preview"

    return html.Div([
        html.H4(title),
        dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in table_data.columns],
            data=table_data.to_dict("records"),
            style_table={'overflowX': 'auto'}
        )
    ])

@app.callback(
    Output("summary-stats", "children"),
    [Input("column-dropdown", "value")]
)
def generate_summary_stats(selected_column):
    if selected_column in df.columns:
        stats = df[selected_column].describe().to_frame().reset_index()
        return dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in stats.columns],
            data=stats.to_dict("records"),
            style_table={'overflowX': 'auto'}
        )
    return "No statistics available."

@app.callback(
    Output("plotly-chart", "figure"),
    [Input("column-dropdown", "value")]
)
def update_graph(selected_column):
    if not selected_column:
        return px.scatter(title="No data available")

    if df[selected_column].dtype in ['int64', 'float64']:
        fig = px.line(df, x=df.index, y=selected_column, title=f"{selected_column} Over Time")
    else:
        value_counts = df[selected_column].value_counts().reset_index()
        value_counts.columns = [selected_column, "Count"]
        fig = px.bar(value_counts, x=selected_column, y="Count", title=f"Distribution of {selected_column}")

    fig.update_layout(clickmode='event+select')
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
