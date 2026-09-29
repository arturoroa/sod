import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd

# Load and prepare your data
df = pd.read_excel('./load_data/SOD_RuleSet.xlsx')  # Replace with your actual data source

app = dash.Dash(__name__)

# Custom CSS for black background and yellow text
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: black;
                color: yellow;
            }
            .dash-graph {
                background-color: black;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Function to update graph layout
def update_graph_layout(fig):
    fig.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="yellow",
        title_font_color="yellow"
    )
    fig.update_xaxes(title_font_color="yellow", tickfont_color="yellow", gridcolor="yellow")
    fig.update_yaxes(title_font_color="yellow", tickfont_color="yellow", gridcolor="yellow")
    return fig

app.layout = html.Div([
    html.H1('IMDB Data Analysis Dashboard', style={'color': 'yellow'}),
    
    dcc.Graph(
        id='parental-guide-chart',
        figure=update_graph_layout(px.bar(df, x='Risk Id', y='Risk Level', title='Top Parental Guides'))
    ),
    
    dcc.Graph(
        id='genre-chart',
        figure=update_graph_layout(px.pie(df, names='Risk Id', values='Name', title='Movies by Genre'))
    ),
    
    dcc.Graph(
        id='rating-chart',
        figure=update_graph_layout(px.scatter(df, x='Risk Id', y='Risk Type', color='Enabled', title='Movie Ratings Over Time'))
    ),
    
    dcc.Graph(
        id='votes-chart',
        figure=update_graph_layout(px.box(df, x='Risk Id', y='Business Cycle', title='Votes Distribution by Genre'))
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
