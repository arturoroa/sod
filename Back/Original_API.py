from fastapi import FastAPI, File, UploadFile, HTTPException
import os
from sqlalchemy import create_engine, Column, Integer, String
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import declarative_base
import os
import pathlib
import json
import aiofiles
import openpyxl
import pandas as pd
import sqlite3
import uvicorn
import RoleAnalysis
import numpy as np

from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, Response
from openpyxl.styles import Font
from starlette.responses import FileResponse
from typing import List
from pretty_html_table import build_table
import re
import charts


app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(charts.router)

current = pathlib.Path(".").parent.absolute()
SQLALCHEMY_DATABASE_URL = f"sqlite:///{current}/DATA/SOD.db"
SECRET_KEY = "mysecretkey"


engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserData(BaseModel):
    Name: str
    Level: str
    Role: str


class PermissionData(BaseModel):
    Role: str
    Name: str
    Level: str
    SOD: str

class SODData(BaseModel):
    Name: str
    Role: str
    Level: str
    Rule: str
    Conflict: str

@app.post("/signup")
async def signup(user: UserCreate):
    db = SessionLocal()
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    db_user = User(name=user.name, email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

class UserLogin(BaseModel):
    email: str
    password: str

@app.post("/login")
async def login(user: UserLogin):
    #print("login")
    #print(user.email)
    db = SessionLocal()
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user is None or user.password != db_user.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return db_user



js_sort_function='''<Head><style>
table {
  border-spacing: 0;
  width: 100%;
  border: 1px solid #ddd;
  font-family: 'Century Gothic', sans-serif;
}

th {
  cursor: pointer;
  width: auto;
  font-weight: bold;
  background-color: white;
  color: darkblue;
  border: 2px solid #ccc;
  text-align: left;
  border-bottom-color: darkblue;
  padding: 1;
}

td {
  text-align: left;
  border: None;
  padding: 1;
}

thead tr:first-child th { position: sticky; top: 0; }


tr:nth-child(odd) {
  background-color: lightblue;
}

tr:nth-child(even) {
  background-color: white;
}

input {
  background-image: url('/css/searchicon.png');
  background-position: 10px 10px;
  background-repeat: no-repeat;
  width: 100%;
  font-size: 16px;
  padding: 12px 20px 12px 40px;
  border: 1px solid #ddd;
  margin-bottom: 12px;
}




</style>


<script>
function sort(n, tableName){
    var table = document.getElementById(tableName);
    let originalRows = table.getElementsByTagName("tbody").item("childre");
    let rows = table.rows;
    let normalrows = Array.from(rows)
    normalrows.shift()
    temp =  normalrows.slice()
    //Filtrado de forma ascendente
    normalrows.sort(function (a, b) {
        return a.getElementsByTagName("TD")[n].innerText.localeCompare(b.getElementsByTagName("TD")[n].innerText);
    });
    dir = "dsc"
    for(const key in temp){
        if (temp[key]!=normalrows[key]){
            dir="asc"
        }
    }
    if(dir=="dsc"){
        normalrows.reverse()
    }
    while(originalRows.children.length>0){
        originalRows.removeChild(originalRows.children[0])
    }
    for (let i = 0; i<normalrows.length; i++){
        originalRows.appendChild(normalrows[i])
    }
}

function sortTable(n, tableName) {
  var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
  table = document.getElementById(tableName);
  switching = true;
  // Set the sorting direction to ascending:
  dir = "asc";
  /* Make a loop that will continue until
  no switching has been done: */
  while (switching) {
    // Start by saying: no switching is done:
    switching = false;
    rows = table.rows;
    /* Loop through all table rows (except the
    first, which contains table headers): */
    for (i = 1; i < (rows.length - 1); i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
      one from current row and one from the next: */
      x = rows[i].getElementsByTagName("TD")[n];
      y = rows[i + 1].getElementsByTagName("TD")[n];
      /* Check if the two rows should switch place,
      based on the direction, asc or desc: */
      if (dir == "asc") {
        if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
          // If so, mark as a switch and break the loop:
          shouldSwitch = true;
          break;
        }
      } else if (dir == "desc") {
        if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
          // If so, mark as a switch and break the loop:
          shouldSwitch = true;
          break;
        }
      }
    }
    if (shouldSwitch) {
      /* If a switch has been marked, make the switch
      and mark that a switch has been done: */
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      // Each time a switch is done, increase this count by 1:
      switchcount ++;
    } else {
      /* If no switching has been done AND the direction is "asc",
      set the direction to "desc" and run the while loop again. */
      if (switchcount == 0 && dir == "asc") {
        dir = "desc";
        switching = true;
      }
    }
  }
}



function myFunction(inputFiltered, tableName) {
  var input, filter, table, tr, td, i, txtValue;
  input = document.getElementById(inputFiltered);
  filter = input.value.toUpperCase();
  table = document.getElementById(tableName);
  tr = table.getElementsByTagName("tr");
  for (i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[0];
    if (td) {
      txtValue = td.textContent || td.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }       
  }
}
</script>
</Head>'''


current = pathlib.Path(".").parent.absolute()
output_path = f"{current}\\Data\\IMRX SOD Analysis.xlsx"
output_zip = f"{current}\\Data\\IMRXSOD.zip"
output_path_Filtered = f"{current}\\Data\\IMRX SOD Analysis_Filtered.xlsx"
R_User = f"{current}\\Data\\IMRX Role to User.xlsx"
R_Permission = f"{current}\\Data\\IMRX Role to Permission.xlsx"
SOD= f"{current}\\Data\\IMRX SOD.xlsx"
DB= f"{current}\\Data\\SOD.db"
#print(f"DB is {DB}")

#This is with pretty html table
#def generate_table(df, identifier):
#    html_table_blue_light = build_table(df, 'blue_light')
#    the_table=f'''<input type="text" id="{identifier}Input" onkeyup="myFunction('{identifier}Input','{identifier}')" placeholder="Search for:" title="Type in a name">'''
#    count = -1
#    split_lines = html_table_blue_light.split(">")
#    for i in split_lines:
#        line = i.upper()
#        line = line.replace('<TABLE',f'<TABLE ID="{identifier}" ')
#        if "<TH " in line:
#            count+=1
#            line = line.replace("<TH ", f'''<TH onclick="sort({count},'{identifier}')"''')
#        the_table+=f"{line}>"
#    if count != -1:
#        html_table_blue_light = f"{js_sort_function}{the_table}<br><br>"
#    else:
#        html_table_blue_light = f"{the_table}<br><br>"
#    return html_table_blue_light



def generate_table(df, identifier):
    html_table_blue_light = df.to_html()#build_table(df, 'blue_light')
    the_table=f'''<input type="text" id="{identifier}Input" onkeyup="myFunction('{identifier}Input','{identifier}')" placeholder="Search for:" title="Type in a name">'''
    count = -1
    split_lines = html_table_blue_light.split("\n")
    for i in split_lines:
        line = i.upper()
        line = line.replace('<TABLE',f'<TABLE ID="{identifier}" ')
        line = re.sub(r'<TH>\d+</TH>', '', line)
        line = re.sub(r'<TH></TH>', '', line)
        if "<TH>" in line: 
            count+=1
            line = line.replace("<TH>", f'''<TH onclick="sort({count},'{identifier}')">''')
        the_table+=f"{line}\n"
    if count != -1:
        html_table_blue_light = f"{js_sort_function}{the_table}<br><br>"
    else:
        html_table_blue_light = f"{the_table}<br><br>"
    return html_table_blue_light


@app.post("/upload_user")
async def upload_single_file(file: UploadFile = File(...)):
    destination_file_path = f"{R_User}"
    #print(f"Saving {destination_file_path}")# location to store file
    try:
        async with aiofiles.open(destination_file_path, 'wb') as out_file:
            while content := await file.read(1024):  # async read file chunk
                await out_file.write(content)  # async write file chunk
        #xlsx_file = pd.read_excel(R_User, sheet_name="Role to Users", engine='openpyxl')
        xlsx_file = pd.read_excel(R_User, sheet_name=0, engine='openpyxl')
        xlsx_file.to_sql(name="Role_to_Users", con= sqlite3.connect(DB), if_exists="replace", index=False)
        xlsx_file.to_sql(name="Role_to_Users_Filtered", con= sqlite3.connect(DB), if_exists="replace", index=False)
        return {"Result": "OK"}
    except Exception as e:
        return HTMLResponse(content=f"<h1>Errors occured while saving data <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/get_user_html")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Role_to_Users", sqlite3.connect(DB))
        identifier = "Role_to_Users"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.post("/upload_permission")
async def upload_single_file(file: UploadFile = File(...)):
    destination_file_path =  f"{R_Permission}" # location to store file
    try:
        async with aiofiles.open(destination_file_path, 'wb') as out_file:
            while content := await file.read(1024):  # async read file chunk
                await out_file.write(content)  # async write file chunk
        #xlsx_file = pd.read_excel(R_Permission, sheet_name="Role to Permissions", engine='openpyxl')
        df = pd.read_excel(destination_file_path,sheet_name=0)
        column_len = len([col for col in df.columns])
        print(column_len)
        if column_len >4:
            transformed_data = []
            roles = [col for col in df.columns if col not in ['Category', 'Permission']]
            for index, row in df.iterrows():
                category = row['Category']
                permission = row['Permission']
                for role in roles:
                    level = row[role]
                    #print(row[role])
                    if level != None and level != 'None' and level != 'nan' and level != np.nan and not pd.isna(level):
                        transformed_data.append({"Category": category,"Permission": permission,"Level": level,"Role": role})
                        #print('adding')
            pd.DataFrame(transformed_data).to_excel(R_Permission,index=False)
        xlsx_file = pd.read_excel(R_Permission, sheet_name=0, engine='openpyxl')
        xlsx_file = xlsx_file[['Role', 'Permission', 'Level', 'Category']]
        xlsx_file.to_sql(name="Role_to_Permissions", con=sqlite3.connect(DB), if_exists="replace", index=False)
        xlsx_file.to_sql(name="Role_to_Permissions_Filtered", con=sqlite3.connect(DB), if_exists="replace", index=False)
        return {"Result": "OK"}
    except Exception as e:
        return HTMLResponse(content=f"<h1>Errors occured while saving data <br></h1> <br> <h3>{e}<h3/>", status_code=200)

@app.get("/get_permission_html")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Role_to_Permissions", sqlite3.connect(DB))
        identifier = "Role_to_Permissions"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.post("/upload_SOD")
async def upload_single_file(file: UploadFile = File(...)):
    destination_file_path = f"{SOD}" # location to store file
    #try:
    async with aiofiles.open(destination_file_path, 'wb') as out_file:
        while content := await file.read(1024):  # async read file chunk
            await out_file.write(content)  # async write file chunk
    xlsx_file = pd.read_excel(SOD, sheet_name=0, engine='openpyxl')
    #role_analysis = RoleAnalysis.Role_analysis()
    #role_analysis.to_sql('Role_Analysis', sqlite3.connect(DB), if_exists='replace', index=False)
    xlsx_file = pd.read_excel(SOD, sheet_name=0, engine='openpyxl')
    xlsx_file.to_sql(name="SOD_Rules", con=sqlite3.connect(DB), if_exists="replace", index=False)
    xlsx_file.to_sql(name="SOD_Rules_Filtered", con=sqlite3.connect(DB), if_exists="replace", index=False)
    return {"Result": "OK"}
    #except Exception as e:
    #    return HTMLResponse(content=f"<h1>Errors occured while saving data <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/get_SOD_html")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from SOD_Rules", sqlite3.connect(DB))
        identifier = "SOD_Rules"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

@app.get("/get_single_role_conflicts")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Single_Role_Conflicts", sqlite3.connect(DB))
        identifier = "Single_Role_Conflicts"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

@app.get("/get_multiple_role_conflicts")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Multiple_Role_Conflicts", sqlite3.connect(DB))
        identifier = "multipleRole"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)
#Revisar
@app.get("/get_single_merged_role_to_permissions")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Merged_Users_to_Permissions", sqlite3.connect(DB))
        identifier = "mergedUsers"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

@app.get("/get_single_role_analysis")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Single_Role_Analysis", sqlite3.connect(DB))
        identifier = "singleRole"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

@app.get("/get_Single_Role_Analysis_Grouped_by_Name")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Single_Role_Analysis_Grouped_by_Name", sqlite3.connect(DB))
        identifier = "singleRoleG"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

@app.get("/SOD_Count_Per_Role")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from SOD_Count_Per_Role", sqlite3.connect(DB))
        identifier = "SODCPR"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/Single_Role_Analysis_Grouped_by_Name_SOD_Rule")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Single_Role_Analysis_Grouped_by_Name_SOD_Rule", sqlite3.connect(DB))
        identifier = "singleRoleAnalysisGN"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

@app.get("/Single_Role_Analysis_Grouped_by_SOD_Rule_Role")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Single_Role_Analysis_Grouped_by_SOD_Rule_Role", sqlite3.connect(DB))
        identifier = "singleRoleAnalysisGR"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/SOD_List_Count")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from SOD_List_Count", sqlite3.connect(DB))
        identifier = "SODLC"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/get_multiple_role_analysis")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Multiple_Role_Analysis", sqlite3.connect(DB))
        identifier = "multipleRoleAnalysis"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/Single_Role_Analysis_Grouped_by_Name")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Single_Role_Analysis_Grouped_by_Name", sqlite3.connect(DB))
        identifier = "singleRoleAGN"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/SOD_Count_Combined")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from SOD_Count_Combined", sqlite3.connect(DB))
        identifier = "SODCC"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule", sqlite3.connect(DB))
        identifier = "multipleRoleAnalysisGR"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1", sqlite3.connect(DB))
        identifier = "multipleRole"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/SOD_List_Count_Multi")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from SOD_List_Count_Multi", sqlite3.connect(DB))
        identifier = "sodLCM"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

#Revisar
@app.get("/Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2", sqlite3.connect(DB))
        #html_table_blue_light += "<br><br>"
        #df = pd.read_sql("Select * from SOD_List_Count_Multi", sqlite3.connect(DB))
        #html_table_blue_light += build_table(df, 'blue_light')
        identifier = "multipleRAGR"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)



@app.get("/get_overall_analysis")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Overall_Analysis", sqlite3.connect(DB))
        identifier = "overallAnalisys"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

@app.get("/Overall_Analysis_Grouped_by_SOD_Rule_Role")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Overall_Analysis_Grouped_by_SOD_Rule_Role", sqlite3.connect(DB))
        identifier = "overalAnalysisGR"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)

@app.get("/SOD_List_Count_Overall")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from SOD_List_Count_Overall", sqlite3.connect(DB))
        identifier = "sodLCO"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/get_overall_conflicts")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Overall_Conflicts", sqlite3.connect(DB))
        identifier = "overallConflicts"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/get_data")
async def get_data():
    try:
        endpoints = {
            "Single_Role_Conflicts": "Single Role Conflicts",
            "Multiple_Role_Conflicts": "Multiple Role Conflicts",
            "Merged_Users_to_Permissions": "Merged Users to Permissions",
            "Single_Role_Analysis": "Single Role Analysis",
            "Single_Role_Analysis_Grouped_by_Name": "Single Role Analysis Grouped by Name",
            "SOD_Count_Per_Role": "SOD Count Per Role",
            "Single_Role_Analysis_Grouped_by_Name_SOD_Rule": "Single Role Analysis Grouped by Name SOD Rule",
            "Single_Role_Analysis_Grouped_by_SOD_Rule_Role": "Single Role Analysis Grouped by SOD Rule Role",
            "SOD_List_Count": "SOD List Count",
            "Multiple_Role_Analysis": "Multiple Role Analysis",
            "Multiple_Role_Analysis_Grouped_by_Name": "Multiple Role Analysis Grouped by Name",
            "SOD_Count_Combined": "Multiple SOD Count Combined",
            "Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule": "Multiple Role Analysis Grouped by Name SOD Rule",
            "Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1": "Multiple Role Analysis Grouped by SOD Rule Role BP1",
            "SOD_List_Count_Multi": "SOD List Count Multi",
            "Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2": "Multiple Role Analysis Grouped by SOD Rule Role BP2"
        }
        html_tables = ""
        #print(endpoints.items())
        for endpoint, title in endpoints.items():
            #print(f'Trying {endpoint}')
            try:
                
                df = pd.read_sql(f"SELECT * FROM {endpoint}", sqlite3.connect(DB))
                identifier = endpoint
                html_table_blue_light = generate_table(df, identifier)

                # Agregar estilo CSS para hacer que el contenido sea desplazable verticalmente
                html_table_blue_light = f"<div style='overflow-y: auto; max-height: 300px;'>{html_table_blue_light}</div>"

                html_tables += f"<div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px;'><h2 style='color: #111; font-weight: bold;'>{title}</h2></div>"
                html_tables += html_table_blue_light
            except Exception as e:
                continue
        #print(html_tables)
        if html_tables:
            return HTMLResponse(content=html_tables, status_code=200)
        else:
            raise HTTPException(status_code=404, detail="No data in the database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_results")
async def read_items():
    DB= f"{current}\\Data\\SOD.db"
    output_zip = f"{current}\\Data\\IMRXSOD.zip"
    R_User = f"{current}\\Data\\IMRX Role to User.xlsx"
    R_Permission = f"{current}\\Data\\IMRX Role to Permission.xlsx"
    SOD= f"{current}\\Data\\IMRX SOD.xlsx"
    TMP = f"{current}\\Data\\Aiver_Default_Ruleset_Processedtmp.xlsx"
    DRS=f"{current}\\SOD_Rule_Set.xlsx"
    output_path = f"{current}\\Data\\IMRX_SOD_Analysis.xlsx"
    output_pdf = f"{current}\\Data\\Explanation.pdf"
    output_zip = f"{current}\\Data\\IMRXSOD.zip"
    RoleAnalysis.Role_analysis("Current",DB,R_User,R_Permission,SOD,TMP,DRS,output_path,output_pdf,output_zip)
    return FileResponse(output_zip, media_type="application/zip",filename=output_zip.split("\\")[-1])






@app.get("/get_users_name_array")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Role_Level_Conflicts", sqlite3.connect(DB))
        names   =  df['Name'].drop_duplicates().dropna()
        emails  =  df['Risk Level'].drop_duplicates().dropna()
        roles   =  df['Role'].drop_duplicates().dropna()
        #print(names)
        #print(emails)
        #print(roles) 
        dictionary={}
        dictionary["Name"] = names.tolist()
        dictionary["Email"] = emails.tolist()
        dictionary["Role"] = roles.tolist()
        json_string = json.dumps(dictionary)
        return HTMLResponse(content=json_string, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)



@app.post("/set_user_filters")
async def set_user_filters(userdata: UserData):
    #print(userdata.Name,userdata.Role,userdata.Email)
    adding_string = ""
    #print("filtering users")
    if userdata.Name != "":
        adding_string += f" and Name like '%{userdata.Name}%'"
    if userdata.Role != "":
        adding_string += f" and Role like '%{userdata.Role}%'"
    if userdata.Level != "":
        adding_string += f' and  "Risk Level" like "%{userdata.Level}%"'
    #print(adding_string)
    #print(f"Select * from Role_Level_Conflicts where 1 {adding_string}")
    try:
        df = pd.read_sql(f"Select * from Role_Level_Conflicts where 1 {adding_string}", sqlite3.connect(DB))
        df.to_sql(name="Role_Level_Conflicts_Filtered", con=sqlite3.connect(DB), if_exists="replace", index=False)
        return {"Result": "OK"}
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/get_permission_arrays")
async def read_permission_items():
    #try:
    df = pd.read_sql("SELECT * FROM Merged_Users_to_Permissions", sqlite3.connect(DB))
    roles = df['Role'].drop_duplicates().dropna()
    permissions = df['Risk Level'].drop_duplicates().dropna()
    levels = df['Bussiness Process 1'].drop_duplicates().dropna()
    categories = df['Bussiness Process 1'].drop_duplicates().dropna()

    dictionary = {
        "Role": roles.tolist(),
        "Permission": permissions.tolist(),
        "Level": levels.tolist(),
        "Category": categories.tolist()
    }

    json_string = json.dumps(dictionary)
    #print(json_string)


    return HTMLResponse(content=json_string, status_code=200)
    #except Exception as e:
    #    return HTMLResponse(content=f"[No data in the database {e}]", status_code=200)






@app.post("/set_permission_filters")
async def set_user_filters(permissiondata: PermissionData):
    adding_string = ""
    if permissiondata.Role != "":
        adding_string += f" and Role like '%{permissiondata.Role}%'"
    if permissiondata.Name != "":
        adding_string += f' and "Risk Level" like "%{permissiondata.Name}%"'
    if permissiondata.Level != "":
        adding_string += f' and "Bussiness Process 1" like "%{permissiondata.Level}%"'
    if permissiondata.SOD != "":
        adding_string += f' and "Bussiness Process 2" like "%{permissiondata.SOD}%"'
    #print(adding_string)
    #print(f"Select * from Single_Role_Conflicts  where 1 {adding_string}")
    #try:
    df = pd.read_sql(f"Select * from Single_Role_Conflicts  where 1 {adding_string}", sqlite3.connect(DB))
    df.to_sql(name="Single_Role_Conflicts_Filtered", con=sqlite3.connect(DB), if_exists="replace", index=False)
    return {"Result": "OK"}
    #except Exception as e:
    #    return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)




@app.get("/get_SOD_arrays")
async def read_sod_items():
    try:
        df = pd.read_sql("SELECT * FROM Merged_Users_to_Permissions", sqlite3.connect(DB))
        #print(df)
        cycles = df['Name_x'].drop_duplicates().dropna()
        rules = df['Name_y'].drop_duplicates().dropna()
        conflicts = df['Conflict Details'].drop_duplicates().dropna()
        business1 = df['Risk Level'].drop_duplicates().dropna()
        business2 = df['Role'].drop_duplicates().dropna()

        dictionary = {
            "Cycle": cycles.tolist(),
            "Rule": rules.tolist(),
            "Conflict": conflicts.tolist(),
            "BusinessProcess1": business1.tolist(),
            "BusinessProcess2": business2.tolist()
        }

        json_string = json.dumps(dictionary)
        #print(json_string)

        return HTMLResponse(content=json_string, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"[No data in the database {e}]", status_code=200)






@app.post("/set_SOD_filters")
async def set_user_filters(soddata: SODData):
    adding_string = ""
    if soddata.Name != "":
        adding_string += f' and "Name_x" like "%{soddata.Name}%"'
    if soddata.Role != "":
        adding_string += f' and "Role" like "%{soddata.Role}%"'
    if soddata.Level != "":
        adding_string += f' and "Risk Level" like "%{soddata.Level}%"'
    if soddata.Rule != "":
        adding_string += f' and "Name_y" like "%{soddata.Rule}%"'
    if soddata.Conflict != "":
        adding_string += f' and "Conflict Details" like "%{soddata.Conflict}%"'
    sql= f"Select * from Merged_Users_to_Permissions where 1 {adding_string}"
    #print(sql)    
    #try:
    df = pd.read_sql(f"{sql}", sqlite3.connect(DB))
    df.to_sql(name="Merged_Users_to_Permissions_Filtered", con=sqlite3.connect(DB), if_exists="replace", index=False)
    return {"Result": "OK"}
    #except Exception as e:
    #    return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)













@app.get("/get_user_html_filtered")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Role_Level_Conflicts_Filtered", sqlite3.connect(DB))
        identifier = "roleUsersFiltered"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/get_permission_html_filtered")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Single_Role_Conflicts_Filtered", sqlite3.connect(DB))
        identifier = "rolePermissionsFiltered" 
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)



@app.get("/get_SOD_html_filtered")
async def read_user_items():
    try:
        df = pd.read_sql("Select * from Merged_Users_to_Permissions_Filtered", sqlite3.connect(DB))
        identifier = "sodRulesFiltered"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.get("/get_filtered")
async def get_data():
    try:
        endpoints = {
            "Role_Level_Conflicts_Filtered": "Role Level Conflicts",
            "Single_Role_Conflicts_Filtered": "Single Role Conflicts",
            "Merged_Users_to_Permissions_Filtered": "Merged Users to Permissions",
           }
        html_tables = ""
        for endpoint, title in endpoints.items():
            try:
                #print(f'Trying {endpoint}')
                df = pd.read_sql(f"SELECT * FROM {endpoint}", sqlite3.connect(DB))
                identifier = endpoint 
                html_table_blue_light = generate_table(df, identifier)

                # Agregar estilo CSS para hacer que el contenido sea desplazable verticalmente
                html_table_blue_light = f"<div style='overflow-y: auto; max-height: 300px;'>{html_table_blue_light}</div>"

                html_tables += f"<div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px;'><h2 style='color: #111; font-weight: bold;'>{title}</h2></div>"
                html_tables += html_table_blue_light
            except Exception as e:
                continue
        if html_tables:
            return HTMLResponse(content=html_tables, status_code=200)
        else:
            raise HTTPException(status_code=404, detail="No data in the database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001)#, workers=10)




###DATA FROM DASHBOARD_GRAPHIC

"""

,1,1,1,1
,
"graph_get_overall_conflicts",
"graph_get_overall_analysis",
"graph_get_Overall_Analysis_Grouped_by_SOD_Rule_Role",
"graph_get_SOD_List_Count_Overall"
"""