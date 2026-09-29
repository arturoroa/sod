from jinja2 import Template
from fastapi import APIRouter
import plotly.express as px
import base64
import matplotlib.pyplot as plt
import pandas as pd
import json
from fastapi.responses import HTMLResponse
from io import BytesIO
import pathlib
import modules.connector 
from sqlalchemy import create_engine
from contextlib import contextmanager
from pydantic import BaseModel
from Models_and_engine import dynamic_engine, SessionData, insert_logs


current = pathlib.Path(".").parent.absolute()
#DB= f"{current}\\Data\\SOD.db"


colors = [
    "#00BFFF", "#4B0082", "#8A2BE2", "#FF00FF", "#FF1493", "#FF4500", "#FF6347", "#FF7F00",
    "#FFD700", "#FFFF00", "#ADFF2F", "#00FF00", "#32CD32", "#228B22", "#006400", "#2E8B57",
    "#00CED1", "#20B2AA", "#0000FF", "#4682B4", "#4169E1", "#0000CD", "#00008B", "#000080",
    "#8B4513", "#A0522D", "#D2691E", "#CD5C5C", "#F08080", "#E9967A", "#FA8072", "#FFC0CB",
    "#DDA0DD", "#EE82EE", "#DA70D6", "#C71585", "#DCDCDC", "#C0C0C0", "#A9A9A9"
]

scripts = '''
<script src="https://code.highcharts.com/stock/highstock.js"></script>
<script src="https://code.highcharts.com/maps/modules/map.js"></script>
<script src="https://code.highcharts.com/stock/modules/exporting.js"></script>
<script src="https://code.highcharts.com/stock/modules/accessibility.js"></script>
'''

html_chart = '''
<div id="{{container}}" style="width:100%; height:80%;"></div>
<script>
    document.addEventListener('DOMContentLoaded', function () {
        const chart = Highcharts.chart('{{container}}', {
            chart: {
                type: '{{type}}'
            },
            colors: {{colors}},
            title: {
                text: '{{title}}'
            },
            xAxis: {
                categories: {{categories}},
                min:0,
                max:{{max}},
                scrollbar: {
                    enabled: true
                },
            },
            yAxis: {
                title:{
                    text: '{{y_title}}'
                }
            },
            series: {{data}}
        });
    });
</script>
'''

html_heatmap_chart = '''
<div id="{{container}}" style="width:100%; height:80%;"></div>
<script>
    Highcharts.chart('{{container}}', {
        chart: {
            type: 'heatmap'
        },
        title: {
            text: '{{title}}'
        },
        xAxis: {
            categories: {{x_categories}}
        },
        yAxis: {
            categories: {{y_categories}},
            title: {
                text: '{{y_title}}'
            },
            min:0,
            max:{{max}},
            scrollbar: {
                enabled: true
            },
        },
        colorAxis: {
            min: 0,
            max: 1,
            stops: [
                [0, '#FFFFFF'],
                [1, '#3ec7c9']
            ],
            labels: {
                enabled: false
            }
        },
        tooltip: {
            formatter: function () {
                var text = this.point.value === 1 ? 'Yes' : 'No';
                return this.series.xAxis.categories[this.point.x] + ' is/has <br/>' + 
                this.series.yAxis.categories[this.point.y] + '?<br/>' +
                '<b>'+text+'</b>';
            }
        },
        legend: {
            enabled: false
        },
        series: {{data}}
    });
</script>
'''

def generate_chart(container_name, type, title, y_title, categories, data):
    template = Template(html_chart)
    max = len(categories)-1
    if len(categories)>5:
        max=4
    html_content = template.render(container=container_name, type=type, title=title, y_title=y_title, categories=categories, data=data, max=max, colors=colors)
    return html_content

def generate_heatmap_chart(container_name, title, x_categories, y_categories, y_title, data):
    template = Template(html_heatmap_chart)
    max = len(y_categories)-1
    if len(y_categories)>30:
        max = 29
    html_content = template.render(container=container_name, title=title, x_categories=x_categories, y_categories=y_categories, y_title=y_title, data=data, max=max)
    return html_content

def generate_bar_chart_html(df):
    try:
        num_unique_values = df.nunique()
        is_numeric = df.applymap(lambda x: isinstance(x, (int, float))).all()
        x_column=""
        y_column=""
        if is_numeric.all():
            if (num_unique_values < len(df) / 2).any():
                x_column = df.columns[0]
                y_column = df.columns[1]
                chart_type = "bar"
            else:
                x_column = df.columns[0]
                y_column = df.columns[1]
                chart_type = "line"
        else:
            if is_numeric.any():
                x_column = df.select_dtypes(include=[int, float]).columns[0]
                y_column = df.select_dtypes(include=[int, float]).columns[1]
                chart_type = "scatter"
            else:
                x_column = df.columns[0]
                y_column = df.columns[1]
                chart_type = "bar"
        #print(x_column)
        #print(y_column)
        plt.figure(figsize=(8, 6))

        if chart_type == "bar":
            plt.bar(df[x_column], df[y_column], color='blue')
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.xticks(rotation=45)
        elif chart_type == "line":
            plt.plot(df[x_column], df[y_column], marker='o')
            plt.xlabel(x_column)
            plt.ylabel(y_column)
        elif chart_type == "scatter":
            plt.scatter(df[x_column], df[y_column])
            plt.xlabel(x_column)
            plt.ylabel(y_column)

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        graphic = base64.b64encode(image_png).decode('utf-8')
        html_graph = f'<img src="data:image/png;base64,{graphic}" alt="Graph">'

        return html_graph

    except Exception as e:
        return f"<h1>Error : {e}</h1>"

def heatmap_data_analysis(df, x_name, y_name):
    x_categories = df[x_name].unique().tolist()
    y_categories = df[y_name].unique().tolist()
    product=[]
    for i in range(len(x_categories)):
        for j in range(len(y_categories)):
            point = [i, j, 0]
            product.append(point)
    for i in range(len(df[x_name])):
        value = [x_categories.index(df[x_name].tolist()[i]), y_categories.index(df[y_name].tolist()[i]), 0]
        if value in product:
            j=product.index(value)
            product[j]=[product[j][0], product[j][1], 1]
    data = [{
        'name':'Values',
        'data':product
    }]
    return x_categories, y_categories, data

def number_data_analysis(df):
    name_columns = df.columns.tolist()
    x_categories=[]
    data=[]
    for i in range(len(df[name_columns[0]])):
        x_categories.append(f'Insertion {i+1}')
    for i in range(len(name_columns)):
        value = {
            'name': name_columns[i],
            'data': df[name_columns[i]].tolist()
        }
        data.append(value)
    return x_categories, data

router = APIRouter(
    prefix="",
    tags=["graphs"],
    responses={404: {"description": "Not found"}},
)

#@router.get("/test_chart")
#async def get_chart():
#    serie = [{
#                'name': 'Jane',
#                'data': [1, 0, 4]
#            }, {
#                'name': 'John',
#                'data': [5, 7, 3]
#            }]
#    html_content = generate_chart('Test', 'column', 'Fruit Consumption', "Fruit eaten", ['Apples', 'Bananas', 'Oranges'], json.dumps(serie))
#    return HTMLResponse(content=html_content, status_code=200)

#@router.get("/graph_get_single_role_conflicts")
def graph_get_single_role_conflicts(company, userID, engine):
    try:
        #Select * from Single_Role_Conflicts
        df = pd.read_sql(f"SELECT Name, Role FROM Single_Role_Conflicts_{userID} GROUP BY Name, Role", engine)
        x_categories, y_categories, data = heatmap_data_analysis(df, 'Name', 'Role')
        html_table_blue_light = generate_heatmap_chart('number1',f'Single Role Conflicts_{company}', x_categories, y_categories, 'Roles', json.dumps(data))
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_multiple_role_conflicts")#check with BP1 and BP2 PENDIENTE
def graph_get_multiple_role_conflicts(company, userID, engine):
    try:
        #"Select * from Multiple_Role_Conflicts"
        #'SELECT Name, "SOD Rule" FROM Multiple_Role_Conflicts GROUP BY Name, "SOD Rule"'
        #df = pd.read_sql('''SELECT Name, "Role (BP1)" || ' & ' || "Role (BP2)" as Roles FROM Multiple_Role_Conflicts group by Name, "Role (BP1)", "Role (BP2)"''', engine)
        df = pd.read_sql(f'''SELECT Name_x, "Permission 1" || ' & ' || "Permission 2" as Roles FROM Merged_Users_to_Permissions_{userID} group by Name_x, "Permission 1", "Permission 2 1"''', engine)
        
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, y_categories, data = heatmap_data_analysis(df, 'Name', 'Roles')
        html_table_blue_light = generate_heatmap_chart('number2',f'Multiple Role Conflicts_{company}', x_categories, y_categories, 'Multiple Role', json.dumps(data))
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_single_merged_users_to_permissions")
def graph_get_single_merged_users_to_permissions(company, userID, engine):
    try:
        #Select * from Merged_Users_to_Permissions
        df = pd.read_sql(f"SELECT Name_x, 'Bussines Cycle' FROM Merged_Users_to_Permissions_{userID} GROUP BY Name_x, 'Bussines Cycle'", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, y_categories, data = heatmap_data_analysis(df, 'Name', 'Permission')
        html_table_blue_light = generate_heatmap_chart('number3', f'Merged Users to Permissions_{company}', x_categories, y_categories, 'Permission', json.dumps(data))
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_single_role_analysis")
def graph_get_single_role_analysis(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Single_Role_Analysis_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"SELECT Role FROM SOD_Count_Per_Role_{userID}", engine)
        x_categories = df['Role'].tolist()
        html_table_blue_light = generate_chart('number4','column', f'Single Role Analysis_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_Single_Role_Analysis_Grouped_by_Name")
def graph_get_Single_Role_Analysis_Grouped_by_Name(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Single_Role_Analysis_Grouped_by_Name_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        #SELECT Name FROM Role_to_Users GROUP BY Name
        df = pd.read_sql(f"Select * From Single_Role_Analysis_{userID} Limit 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('number5','column', f'Single Role Analysis Grouped By Name_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        #html_table_blue_light += js_sort_function
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_single_SOD_Count_Per_Role")
def graph_get_single_SOD_Count_Per_Role(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from SOD_Count_Per_Role_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        html_table_blue_light = generate_chart('number6','column', f'SOD Count Per Role_{company}', 'Count Per Role', df['Role'].tolist(), json.dumps([{'data':df['SOD Rule'].tolist()}]))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_Single_Role_Analysis_Grouped_by_Name_SOD_Rule")
def graph_get_Single_Role_Analysis_Grouped_by_Name_SOD_Rule(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Single_Role_Analysis_Grouped_by_Name_SOD_Rule_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        #SELECT Name FROM Role_to_Users GROUP BY Name
        df = pd.read_sql(f"Select * From Single_Role_Analysis_{userID} Limit 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('number7', 'column', f'Single Role Analysis Grouped By Name SOD Rule_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_Single_Role_Analysis_Grouped_by_SOD_Rule_Role")
def graph_get_Single_Role_Analysis_Grouped_by_SOD_Rule_Role(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Single_Role_Analysis_Grouped_by_SOD_Rule_Role_{userID}", engine)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"Select * from Single_Role_Analysis_Grouped_by_Name_SOD_Rule_{userID} LIMIT 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('number8','column', f'Single Role Analysis Grouped By SOD Rule Role_{company}', 'Value', x_categories, json.dumps(data))
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_SOD_List_Count")
def graph_get_SOD_List_Count(comapny, userID, engine):
    try:
        df = pd.read_sql(f"Select * from SOD_List_Count_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        html_table_blue_light = generate_chart('number9','column', f'SOD List Count_{comapny}', 'Count', df['SOD Rule'].tolist(), json.dumps([{'data':df['Count'].tolist()}]))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)



#@router.get("/graph_get_multiple_role_analysis")
def graph_get_multiple_role_analysis(company, userID, engine):
    try:
        #df = pd.read_sql(f"Select * from Multiple_Role_Analysis", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        #x_categories, data = number_data_analysis(df)
        #df = pd.read_sql('SELECT "Combined Role" FROM SOD_Count_Combined', engine)
        #x_categories = df['Combined Role'].tolist()
        #html_table_blue_light = generate_chart('number10','column', 'Multiple Role Analysis', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        #return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
        return HTMLResponse(content="", status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_multiple_Role_Analysis_Grouped_by_Name")
def graph_get_multiple_Role_Analysis_Grouped_by_Name(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_Name_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"SELECT * FROM Multiple_Role_Analysis_{userID} LIMIT 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('number11', 'column', f'Multiple Role Analysis Grouped By Name_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_multiple_SOD_Count_Combined")
def graph_get_multiple_SOD_Count_Combined(company, userID, engine):
    try:
        #df = pd.read_sql(f"Select * from SOD_Count_Combined", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        #html_table_blue_light = generate_chart('number12','column', 'SOD Count Combined', 'Count Combined', df['Combined Role'].tolist(), json.dumps([{'data':df['SOD Rule'].tolist()}]))
        #html_table_blue_light += "<br><br>"
        return HTMLResponse(content="", status_code=200)
        #return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule")
def graph_get_Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"SELECT * FROM Multiple_Role_Analysis_{userID} LIMIT 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('columns13', 'column', f'Multiple Role Analysis Grouped By Name SOD Rule_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1")
def graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_{userID} LIMIT 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('number14', 'column', f'Multiple Role Analysis Grouped By SOD Rule Role BP1_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_SOD_List_Count_Multi")
def graph_get_SOD_List_Count_Multi(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from SOD_List_Count_Multi_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        html_table_blue_light = generate_chart('number15','column', f'SOD List Count Multi_{company}', 'Count', df['SOD Rule'].tolist(), json.dumps([{'data':df['Count'].tolist()}]))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2")
def graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_{userID} LIMIT 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('number16','column', f'Multiple Role Analysis Grouped By SOD Rule Role BP2_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_overall_analysis")
def graph_get_overall_analysis(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Overall_Analysis_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"SELECT Role FROM SOD_Count_Per_Role_{userID}", engine)
        x_categories = df['Role'].tolist()
        html_table_blue_light = generate_chart('number17','column', f'Overall Analysis_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_Overall_Analysis_Grouped_by_SOD_Rule_Role")#check
def graph_get_Overall_Analysis_Grouped_by_SOD_Rule_Role(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Overall_Analysis_Grouped_by_SOD_Rule_Role_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f'SELECT "SOD Rule" FROM SOD_List_Count_Overall_{userID} ORDER BY "SOD Rule" ASC', engine)
        x_categories = df["SOD Rule"].tolist()
        html_table_blue_light = generate_chart('number18','column', f'Overall Analysis Grouped By SOD Rule Role_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_SOD_List_Count_Overall")
def graph_get_SOD_List_Count_Overall(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from SOD_List_Count_Overall_{userID}", engine)
        html_table_blue_light = generate_bar_chart_html(df)
        #html_table_set_permission_filtersblue_light += "<br><br>"
        html_table_blue_light = generate_chart('number19','column', f'SOD List Count Overall_{company}', 'Count Overall', df['SOD Rule'].tolist(), json.dumps([{'data':df['Count'].tolist()}]))
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_overall_conflicts")#check
#async def read_user_items():
#    try:
        #Select * from Overall_Conflicts
#        df = pd.read_sql('SELECT Name, count(Role), count("Combined Role") FROM Overall_Conflicts GROUP BY Name, Role, "Combined Role"', engine)
        #html_table_blue_light = generate_bar_chart_html(df)
#        data=[]
#        names = df['Name'].unique().tolist()
#        for i in range(len(names)):  
#            a=0
#            b=0
#            for j in range(len(df['Name'])):
#                if df['count(Role)'].tolist()[j]!=0 and df['Name'].tolist()[j]==names[i]:
#                    a += 1
#                if df['count("Combined Role")'].tolist()[j]!=0 and df['Name'].tolist()[j]==names[i]:
#                    b += 1
#            value = {
#                'name':names[i],
#                'data':[a, b]
#            }
#            data.append(value)
#        html_table_blue_light = generate_chart('number20','column', 'Overall Conflicts', 'Value', ['Role', 'Combined Role'], json.dumps(data))
#        return HTMLResponse(content=html_table_blue_light, status_code=200)
#    except Exception as e:
#        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)
@router.post("/graph_get_data")
async def read_user_item(session: SessionData):
    Company = session.Company
    UserID = session.UserID
    WebSocketID = session.WebSocketID
    with dynamic_engine(Company) as engine:
        text = scripts
        text += f'<div>{graph_get_single_role_conflicts(Company, UserID, engine)}</div><br><br>'
        #text = text.replace("'Name'",'')
        #text += f'<div>{graph_get_multiple_role_conflicts()}</div><br><br>'
        #text += f'<div>{graph_get_single_merged_users_to_permissions()}</div><br><br>'
        text += f'<div>{graph_get_single_role_analysis(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Single_Role_Analysis_Grouped_by_Name(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_single_SOD_Count_Per_Role(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Single_Role_Analysis_Grouped_by_Name_SOD_Rule(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Single_Role_Analysis_Grouped_by_SOD_Rule_Role(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_SOD_List_Count(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_multiple_role_analysis(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_multiple_Role_Analysis_Grouped_by_Name(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_multiple_SOD_Count_Combined(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_SOD_List_Count_Multi(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2(Company, UserID, engine)}</div><br><br>'
        #text += f'<div>{graph_get_overall_analysis()}</div><br><br>'
        #text += f'<div>{graph_get_Overall_Analysis_Grouped_by_SOD_Rule_Role()}</div><br><br>'
        #text += f'<div>{graph_get_SOD_List_Count_Overall()}</div><br><br>'
    insert_logs(UserID, Company, WebSocketID, "Get Graphs Data", f"All Graphs Data returned")
    return HTMLResponse(content=text, status_code=200) 
    
    
### FILTERED ###


#@router.get("/graph_get_single_role_conflicts_filtered")
def graph_get_single_role_conflicts_filtered(company, userID, engine):
    try:
        #Select * from Single_Role_Conflicts
        df = pd.read_sql(f"SELECT Name, Role FROM Single_Role_Conflicts_Filtered_{userID} GROUP BY Name, Role", engine)
        x_categories, y_categories, data = heatmap_data_analysis(df, 'Name', 'Role')
        html_table_blue_light = generate_heatmap_chart('fnumber1',f'Single Role Conflicts Filtered_{company}', x_categories, y_categories, 'Roles', json.dumps(data))
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_multiple_role_conflicts_filtered")#check with BP1 and BP2 PENDIENTE
def graph_get_multiple_role_conflicts_filtered(company, userID, engine):
    try:
        #"Select * from Multiple_Role_Conflicts"
        #'SELECT Name, "SOD Rule" FROM Multiple_Role_Conflicts_Filtered GROUP BY Name, "SOD Rule"'
        df = pd.read_sql(f'''SELECT Name, "Role (BP1)" || ' & ' || "Role (BP2)" as Roles FROM Multiple_Role_Conflicts_Filtered_{userID} group by Name, "Role (BP1)", "Role (BP2)"''', engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, y_categories, data = heatmap_data_analysis(df, 'Name', 'Roles')
        html_table_blue_light = generate_heatmap_chart('fnumber2',f'Multiple Role Conflicts Filtered_{company}', x_categories, y_categories, 'Multiple Role', json.dumps(data))
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_single_merged_users_to_permissions_filtered")
def graph_get_single_merged_users_to_permissions_filtered(company, userID, engine):
    try:
        #Select * from Merged_Users_to_Permissions
        df = pd.read_sql(f"SELECT Name, Permission FROM Merged_Users_to_Permissions_Filtered_{userID} GROUP BY Name, Permission", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, y_categories, data = heatmap_data_analysis(df, 'Name', 'Permission')
        html_table_blue_light = generate_heatmap_chart('fnumber3', f'Merged Users to Permissions Filtered_{company}', x_categories, y_categories, 'Permission', json.dumps(data))
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_single_role_analysis_filtered")
def graph_get_single_role_analysis_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Single_Role_Analysis_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"SELECT Role FROM SOD_Count_Per_Role_Filtered_{userID}", engine)
        x_categories = df['Role'].tolist()
        html_table_blue_light = generate_chart('fnumber4','column', f'Single Role Analysis Filtered_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_Single_Role_Analysis_Grouped_by_Name_filtered")
def graph_get_Single_Role_Analysis_Grouped_by_Name_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Single_Role_Analysis_Grouped_by_Name_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        #SELECT Name FROM Role_to_Users_Filtered GROUP BY Name
        df = pd.read_sql(f"Select * From Single_Role_Analysis_Filtered_{userID} Limit 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('fnumber5','column', f'Single Role Analysis Grouped By Name Filtered_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        #html_table_blue_light += js_sort_function
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_single_SOD_Count_Per_Role_filtered")
def graph_get_single_SOD_Count_Per_Role_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from SOD_Count_Per_Role_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        html_table_blue_light = generate_chart('fnumber6','column', f'SOD Count Per Role Filtered_{company}', 'Count Per Role', df['Role'].tolist(), json.dumps([{'data':df['SOD Rule'].tolist()}]))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_Single_Role_Analysis_Grouped_by_Name_SOD_Rule_filtered")
def graph_get_Single_Role_Analysis_Grouped_by_Name_SOD_Rule_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Single_Role_Analysis_Grouped_by_Name_SOD_Rule_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        #SELECT Name FROM Role_to_Users_Filtered GROUP BY Name
        df = pd.read_sql(f"Select * From Single_Role_Analysis_Filtered_{userID} Limit 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('fnumber7', 'column', f'Single Role Analysis Grouped By Name SOD Rule Filtered_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_Single_Role_Analysis_Grouped_by_SOD_Rule_Role_filtered")
def graph_get_Single_Role_Analysis_Grouped_by_SOD_Rule_Role_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Single_Role_Analysis_Grouped_by_SOD_Rule_Role_Filtered_{userID}", engine)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"Select * from Single_Role_Analysis_Grouped_by_Name_SOD_Rule_Filtered_{userID} LIMIT 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('fnumber8','column', f'Single Role Analysis Grouped By SOD Rule Role Filtered_{company}', 'Value', x_categories, json.dumps(data))
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_SOD_List_Count_filtered")
def graph_get_SOD_List_Count_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from SOD_List_Count_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        html_table_blue_light = generate_chart('fnumber9','column', f'SOD List Count Filtered_{company}', 'Count', df['SOD Rule'].tolist(), json.dumps([{'data':df['Count'].tolist()}]))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_multiple_role_analysis_filtered")
def graph_get_multiple_role_analysis_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f'SELECT "Combined Role" FROM SOD_Count_Combined_Filtered_{userID}', engine)
        x_categories = df['Combined Role'].tolist()
        html_table_blue_light = generate_chart('fnumber10','column', f'Multiple Role Analysis Filtered_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_multiple_Role_Analysis_Grouped_by_Name_filtered")
def graph_get_multiple_Role_Analysis_Grouped_by_Name_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_Name_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"SELECT * FROM Multiple_Role_Analysis_Filtered_{userID} LIMIT 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('fnumber11', 'column', f'Multiple Role Analysis Grouped By Name Filtered_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_multiple_SOD_Count_Combined_filtered")
def graph_get_multiple_SOD_Count_Combined_filtered(company, userID, engine):
    try:
        #df = pd.read_sql(f"Select * from SOD_Count_Combined_Filtered", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        #html_table_blue_light = generate_chart('fnumber12','column', 'SOD Count Combined Filtered', 'Count Combined', df['Combined Role'].tolist(), json.dumps([{'data':df['SOD Rule'].tolist()}]))
        #html_table_blue_light += "<br><br>"
        return HTMLResponse(content="<BR>", status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_filtered")
def graph_get_Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"SELECT * FROM Multiple_Role_Analysis_Filtered_{userID} LIMIT 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('fcolumns13', 'column', f'Multiple Role Analysis Grouped By Name SOD Rule Filtered_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1_filtered")
def graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1_filtered(comapny, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_Filtered_{userID} LIMIT 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('fnumber14', 'column', f'Multiple Role Analysis Grouped By SOD Rule Role BP1 Filtered_{comapny}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_SOD_List_Count_Multi_filtered")
def graph_get_SOD_List_Count_Multi_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from SOD_List_Count_Multi_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        html_table_blue_light = generate_chart('fnumber15','column', f'SOD List Count Multi Filtered_{company}', 'Count', df['SOD Rule'].tolist(), json.dumps([{'data':df['Count'].tolist()}]))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2_filtered")
def graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"Select * from Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_Filtered_{userID} LIMIT 1", engine)
        x_categories = df.columns.tolist()
        html_table_blue_light = generate_chart('fnumber16','column', f'Multiple Role Analysis Grouped By SOD Rule Role BP2 Filtered_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_overall_analysis_filtered")
def graph_get_overall_analysis_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Overall_Analysis_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f"SELECT Role FROM SOD_Count_Per_Role_Filtered_{userID}", engine)
        x_categories = df['Role'].tolist()
        html_table_blue_light = generate_chart('fnumber17','column', f'Overall Analysis Filtered_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_Overall_Analysis_Grouped_by_SOD_Rule_Role_filtered")#check
def graph_get_Overall_Analysis_Grouped_by_SOD_Rule_Role_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from Overall_Analysis_Grouped_by_SOD_Rule_Role_Filtered_{userID}", engine)
        #html_table_blue_light = generate_bar_chart_html(df)
        x_categories, data = number_data_analysis(df)
        df = pd.read_sql(f'SELECT "SOD Rule" FROM SOD_List_Count_Overall_Filtered_{userID} ORDER BY "SOD Rule" ASC', engine)
        x_categories = df["SOD Rule"].tolist()
        html_table_blue_light = generate_chart('fnumber18','column', f'Overall Analysis Grouped By SOD Rule Role Filtered_{company}', 'Value', x_categories, json.dumps(data))
        #html_table_blue_light += "<br><br>"
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


#@router.get("/graph_get_SOD_List_Count_Overall_filtered")
def graph_get_SOD_List_Count_Overall_filtered(company, userID, engine):
    try:
        df = pd.read_sql(f"Select * from SOD_List_Count_Overall_Filtered_{userID}", engine)
        html_table_blue_light = generate_bar_chart_html(df)
        #html_table_set_permission_filtersblue_light += "<br><br>"
        html_table_blue_light = generate_chart('fnumber19','column', f'SOD List Count Overall Filtered_{company}', 'Count Overall', df['SOD Rule'].tolist(), json.dumps([{'data':df['Count'].tolist()}]))
        return html_table_blue_light#HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return e#HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#@router.get("/graph_get_overall_conflicts_filtered")#check
#async def read_user_items():
#    try:
        #Select * from Overall_Conflicts
#        df = pd.read_sql('SELECT Name, count(Role), count("Combined Role") FROM Overall_Conflicts_filtered GROUP BY Name, Role, "Combined Role"', engine)
        #html_table_blue_light = generate_bar_chart_html(df)
#        data=[]
#        names = df['Name'].unique().tolist()
#        for i in range(len(names)):  
#            a=0
#            b=0
#            for j in range(len(df['Name'])):
#                if df['count(Role)'].tolist()[j]!=0 and df['Name'].tolist()[j]==names[i]:
#                    a += 1
#                if df['count("Combined Role")'].tolist()[j]!=0 and df['Name'].tolist()[j]==names[i]:
#                    b += 1
#            value = {
#                'name':names[i],
#                'data':[a, b]
#            }
#            data.append(value)
#        html_table_blue_light = generate_chart('fnumber20','column', 'Overall Conflicts Filtered', 'Value', ['Role', 'Combined Role'], json.dumps(data))
#        return HTMLResponse(content=html_table_blue_light, status_code=200)
#    except Exception as e:
#        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)
@router.post("/graph_get_filtered")
async def read_user_item(session: SessionData):
    Company = session.Company
    UserID = session.UserID
    WebSocketID = session.WebSocketID
    with dynamic_engine(Company) as engine:
        text = scripts
        text += f'<div>{graph_get_single_role_conflicts_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_multiple_role_conflicts_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_single_merged_users_to_permissions_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_single_role_analysis_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Single_Role_Analysis_Grouped_by_Name_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_single_SOD_Count_Per_Role_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Single_Role_Analysis_Grouped_by_Name_SOD_Rule_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Single_Role_Analysis_Grouped_by_SOD_Rule_Role_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_SOD_List_Count_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_multiple_role_analysis_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_multiple_Role_Analysis_Grouped_by_Name_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_multiple_SOD_Count_Combined_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_SOD_List_Count_Multi_filtered(Company, UserID, engine)}</div><br><br>'
        text += f'<div>{graph_get_Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2_filtered(Company, UserID, engine)}</div><br><br>'
        #text += f'<div>{graph_get_overall_analysis_filtered()}</div><br><br>'
        #text += f'<div>{graph_get_Overall_Analysis_Grouped_by_SOD_Rule_Role_filtered()}</div><br><br>'
        #text += f'<div>{graph_get_SOD_List_Count_Overall_filtered()}</div><br><br>'
    insert_logs(UserID, Company, WebSocketID, "Get Graphs Filtered", f"All Graphs Filtered returned")
    return HTMLResponse(content=text, status_code=200)