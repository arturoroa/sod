from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Form
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from WebSocketManagerConnection import manager
from contextlib import asynccontextmanager
from pydantic import BaseModel
import uvicorn
import modules.connector
import charts
import aiofiles
import openpyxl
import os
import pathlib
import json
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import sys
import RoleAnalisys
import re
import asyncio
from werkzeug.security import generate_password_hash, check_password_hash
from SODDash import clear, generate_sod_rulset_table, generate_dash_table, generate_dash_tables, create_interactive_dashboard, remove_inactivity_dashboards, generate_dash_table_filter
from Models_and_engine import dynamic_engine, SessionData, insert_logs, create_logs_table, SessionDataFiltered

load_dotenv(pathlib.Path(__file__).parent / '.env')

#####################Errors Code
#   -1.- Not Found
#   -2.- Error on Query
#   -3.- Can not read or write
#
#
#
#
#
#
#
#
#
#
#
#









#####GLOBAL VARS
created_tables=['Merged_Users_to_Permissions',
'Merged_Users_to_Permissions_Filtered',
'Merged_Users_to_Permissions_Filtered_SOA',
'Merged_Users_to_Permissions_SOA',
'Multiple_Role_Analysis',
'Multiple_Role_Analysis_Grouped_by_Name',
'Multiple_Role_Analysis_Grouped_by_Name_SOA',
'Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule',
'Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_SOA',
'Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1',
'Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1_SOA',
'Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2',
'Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2_SOA',
'Multiple_Role_Analysis_SOA',
'Multiple_SOD_Count_Combined',
'Multiple_SOD_Count_Combined_SOA',
'Role_Level_Conflicts',
'Role_Level_Conflicts_Filtered',
'Role_Level_Conflicts_Simplified',
'Role_Level_Conflicts_Filtered_SOA',
'Role_Level_Conflicts_SOA',
'Role_to_Permissions_Filtered_SOA',
'Role_to_Permissions_SOA',
'Role_to_Users_Filtered_SOA',
'Role_to_Users_SOA',
'SOD_Count_Per_Role',
'SOD_Count_Per_Role_SOA',
'SOD_List_Count',
'SOD_List_Count_Multi',
'SOD_List_Count_Multi_SOA',
'SOD_List_Count_SOA',
'SOD_Rules_SOA',
'Single_Role_Analysis',
'Single_Role_Analysis_Grouped_by_Name',
'Single_Role_Analysis_Grouped_by_Name_SOA',
'Single_Role_Analysis_Grouped_by_Name_SOD_Rule',
'Single_Role_Analysis_Grouped_by_Name_SOD_Rule_SOA',
'Single_Role_Analysis_Grouped_by_SOD_Rule_Role',
'Single_Role_Analysis_Grouped_by_SOD_Rule_Role_SOA',
'Single_Role_Analysis_SOA',
'Single_Role_Conflicts',
'Single_Role_Conflicts_Filtered',
'Single_Role_Conflicts_Filtered_SOA',
'Single_Role_Conflicts_SOA',
'Client_Data_Simplified',
'Role_Level_Conflicts_Detailed']




class UserCredentials(BaseModel):
    UserID: str
    Password: str


class VeriTable(BaseModel):
    Table_num: str
    Company: str
    UserID: str

    
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
    
class SessionPlusCredData(BaseModel):
    UserID: str
    Password: str
    Type: str
    Company: str
    Email: str
    Phone: str
    Active: str
 

current = pathlib.Path(".").parent.absolute()

separator =''

if sys.platform.startswith('win'):
    separator = '\\'
else:
    separator='/'

error_message = 'Loading Error'

#############








############# JS FUNCTION#############################


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



#################################################################3








######GLOBAL FUNCTIONS#######################################




def verify_table(user, table_name,DB, WebSocketID):
    db = modules.connector.connect_db(database=DB)
    mycursor = db.cursor()
    query = f"SELECT TABLE_NAME FROM information_schema.tables WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = '{DB}'"
    mycursor.execute(query)
    result = mycursor.fetchone()
    if result:
        insert_logs(user, DB, WebSocketID, "Verify Table", f"{table_name} table found")
        return 1
    else:
        insert_logs(user, DB, WebSocketID, "Verify Table", f"{table_name} table not found")
        return -1



'''def call_role_analysis(company,UserID, WebSocketID, option=True):
    with dynamic_engine(company) as engine:
        if option:
            R_User = f"Role_to_Users_{UserID}"
            R_Permission = f"Role_to_Permissions_{UserID}"
            SOD= f"SOD_Rules"
            output_path = f"{current}{separator}{company}_Role_Conflicts_Details_{UserID}.xlsx"
            df, zipfile = RoleAnalisys.Role_analysis(engine, R_User, R_Permission, SOD, output_path, company, UserID, WebSocketID)
        else:
            R_User = f"Role_to_Users_Filtered_{UserID}"
            R_Permission = f"Role_to_Permissions_Filtered_{UserID}"
            SOD= f"SOD_Rules"
            output_path = f"{current}{separator}{company}_Role_Conflicts_Details_Filtered_{UserID}.xlsx"
            df, zipfile = RoleAnalisys.Role_analysis_filtered(engine, R_User, R_Permission, SOD, output_path, company, UserID, WebSocketID)
    return df, zipfile'''

def call_role_analysis(company,UserID, WebSocketID, option=True):
    R_User = f"Role_to_Users_{UserID}"
    R_Permission = f"Role_to_Permissions_{UserID}"
    SOD= f"SOD_Rules"
    TMP = f"{current}{separator}Aiver_Default_Ruleset_Processedtmp_{UserID}.xlsx"
    DRS=f"{current}{separator}Aiver_Default_Ruleset_Processed_{UserID}.xlsx"
    output_path = output_path = f"{current}{separator}{company}_Role_Conflicts_Details_{UserID}.xlsx"#f"{current}{separator}IMRX_SOD_Analysis_{UserID}.xlsx"
    output_pdf = f"{current}{separator}Explanation_{UserID}.pdf"
    output_zip = f"{current}{separator}IMRXSOD_{UserID}.zip"
    with dynamic_engine(company) as engine:
        df, zipfile = RoleAnalisys.Role_analysis("Current",engine,R_User,R_Permission,SOD,TMP,DRS,output_path,output_pdf,output_zip,company,UserID, WebSocketID)
    return df, output_zip




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


# Define the list of allowed origins
origins = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ORIGINS',
        'https://localhost:8000,https://localhost:8081,http://localhost:8000,http://localhost:8081',
    ).split(',')
    if origin.strip()
]





##############################Declare THE APP

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('LIFESPAN ACTIVATED')
    asyncio.create_task(cleanup_inactive_dashboards_and_grids())
    yield

app = FastAPI(lifespan=lifespan)


app.include_router(charts.router)


# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

'''@app.get("/test", response_class=HTMLResponse)
async def get_table():
    dash_app = create_dash_app(requests_pathname_prefix="/test/")
    app.mount("/test", WSGIMiddleware(dash_app.server))
    with dynamic_engine('SOA') as engine:
        data = generate_sod_rulset_table(dash_app, engine, 'SOD_Rules_SOA')
    return data

@app.get("/test2", response_class=HTMLResponse)
async def get_table():
    dash_app = create_dash_app(requests_pathname_prefix="/test2/")
    app.mount("/test2", WSGIMiddleware(dash_app.server))
    with dynamic_engine('SOA') as engine:
        data = generate_dash_table(dash_app, engine, 'Role_to_Users_SOA')
    return data
'''

@app.post("/login")
async def login(credentials: UserCredentials):#SessionPlusCredData):
    params = (credentials.UserID,)# credentials.Password)
    db = modules.connector.connect_db(database='sod')
    query = "SELECT * FROM users WHERE UserID = %s;"# AND Password = %s;"
    cursor = db.cursor()
    #print(query)
    cursor.execute(query, params)
    user_results = cursor.fetchone()
    #print(user_results)
    if user_results != None:
        if check_password_hash(user_results[1], credentials.Password):
            company = user_results[3]
            insert_logs(credentials.UserID, company, None, "Login", "Starting Session")
            #createdb = f'CREATE DATABASE IF NOT EXISTS {credentials.Company} CHARACTER SET utf8mb4;'
            insert_logs(credentials.UserID, company, None, "Login", f"Creating {company} database if not exists")
            createdb = f'CREATE DATABASE IF NOT EXISTS {company} CHARACTER SET utf8mb4;'
            db = modules.connector.connect_db(database='')
            cursor = db.cursor()
            result = cursor.execute(createdb)
            db.commit()
            #exist = verify_table(f"SOD_Rules",credentials.Company)
            exist = verify_table(credentials.UserID, f"SOD_Rules", company, None)
            '''
            if exist != -1:
                #db = modules.connector.connect_db(database=credentials.Company)
                db = modules.connector.connect_db(database= company)
                cursor = db.cursor()
                new_query=f"DROP TABLE SOD_Rules"
                cursor.execute(new_query)
                db.commit()
                insert_logs(credentials.UserID, company, None, "Login", f"SOD_Rules table deleted")
            '''
            db = modules.connector.connect_db(database='sod')
            cursor = db.cursor()
            #cursor.execute("USE SOA")
            cursor.execute(f"USE {company}")
            if exist == -1:
                #new_query=f"CREATE TABLE SOA.SOD_Rules AS SELECT * FROM sod.Original_SOD_Rule_Set"
                new_query=f"CREATE TABLE {company}.SOD_Rules AS SELECT * FROM sod.Original_SOD_Rule_Set" 
                cursor.execute(new_query)
                db.commit()
                insert_logs(credentials.UserID, company, None, "Login", f"SOD_Rules table created")
            ########################
            exist = verify_table(credentials.UserID, f'SOD_Rules_{credentials.UserID}', company, None)
            if exist == -1:
                sod_rules_by_company = f"CREATE TABLE {company}.SOD_Rules_{credentials.UserID} AS SELECT * FROM sod.Original_SOD_Rule_Set WHERE 1=0"
                cursor.execute(sod_rules_by_company)
                db.commit()
                insert_logs(credentials.UserID, company, None, "Login", f"SOD_Rules_{company} table created")
            ########################
            cursor.close()
            db.close()
            exist_logs = verify_table(credentials.UserID, "Logs", company, None)
            if exist_logs == -1:
                create_logs_table(company)
            #exists_permissions = verify_table(f"Role_to_Permissions_{credentials.UserID}",credentials.Company)
            exists_permissions = verify_table(credentials.UserID, f"Role_to_Permissions_{credentials.UserID}", company, None)
            #exists_Users = verify_table(f"Role_to_Users_{credentials.UserID}",credentials.Company)
            exists_Users = verify_table(credentials.UserID, f"Role_to_Users_{credentials.UserID}", company, None)
            insert_logs(credentials.UserID, company, None, "Login", "Session started")
            return {'UserID' : user_results[0],'UserType':user_results[2] ,'Company' : user_results[3] ,'Email': user_results[4] ,'Phone': user_results[5] ,'Active': user_results[6]  }
    return {'UserType':-1}
    

@app.post("/logout")
async def logout(session:SessionData):
    #try:
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Logout", "Colosing Session")
        db = modules.connector.connect_db(database=session.Company)
        for i in created_tables:
            try:
                query = f"Drop table {i}_{session.UserID};"
                cursor = db.cursor()
                cursor.execute(query)
            except:
                pass
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Logout", "Session Tables removed")
        clear(app, session.UserID, session.Company, session.WebSocketID)
        
        files = [f"{current}{separator}{session.Company}_Role_Conflicts_Details_{session.UserID}.xlsx", f"{current}{separator}{session.Company}_Role_Conflicts_Details_Filtered_{session.UserID}.xlsx"]
        for file_path in files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    insert_logs(session.UserID, session.Company, session.WebSocketID, "Logout", f"{file_path.split(separator)[-1]} file has been removed")
                except Exception as e:
                    print(e)
                    insert_logs(session.UserID, session.Company, session.WebSocketID, "Logout", f"An error ocurred while trying to delete the file {file_path.split(separator)[-1]}: {e}")
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Logout", "Session Closed")
        return {"Results": 0 }
    #except Exception as e:
    #    return {'Result':-2}






@app.post("/is_report_active")
async def read_items(session:SessionData):
    exists_Rules = verify_table(session.UserID, f"SOD_Rules",session.Company, session.WebSocketID)
    exist_Permissions = verify_table(session.UserID, f"Role_to_Permissions_{session.UserID}",session.Company, session.WebSocketID)
    exists_user = verify_table(session.UserID, f"Role_to_Users_{session.UserID}",session.Company, session.WebSocketID)
    if exists_Rules != -1 and exist_Permissions != -1 and exists_user != -1:
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Check Report Status", "Active")
        return {"Result" : 1}
    else:
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Check Report Status", "Inactive")
        return {"Result" : -1}

@app.post('/execute_analysis')
async def execute_analysis(session: SessionData):
    try:
        df, output_zip = call_role_analysis(session.Company, session.UserID, session.WebSocketID)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Login", f'First anaysis completed')
    except Exception as e:
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Login", f'An error occurred while executing the initial analysis: {e}')
        raise HTTPException(status_code=500, detail=f'An error occurred while executing the initial analysis: {e}')

@app.post("/get_creation_date")
def get_creation_date(tabledata: VeriTable):
    db = modules.connector.connect_db(database=tabledata.Company)
    mycursor = db.cursor()
    if tabledata.Table_num == "1":
        query = f"SELECT create_time FROM INFORMATION_SCHEMA.TABLES WHERE table_schema = '{tabledata.Company}' AND table_name = 'Role_to_Users_{tabledata.UserID}';"
    else:
        query = f"SELECT create_time FROM INFORMATION_SCHEMA.TABLES WHERE table_schema = '{tabledata.Company}' AND table_name = 'Role_to_Permissions_{tabledata.UserID}';"
    mycursor.execute(query)
    result = mycursor.fetchone()
    if result:
        return result[0]
    else:
        return -1






'''

# Example endpoint for POST request
@app.post("/login")
async def login(credentials: UserCredentials):
    db = modules.connector.connect_db(database='sod')
    query = "SELECT * FROM users WHERE Email = %s AND Password = %s;"
    params = (credentials.userID, credentials.password)
    cursor = db.cursor()
    print(query)
    cursor.execute(query, params)
    result = cursor.fetchone()
    print(result)
    if result != None:
        exist = verify_table(f"SOD_Rules_{result[3]}")
        if exist != -1:
            new_query=f"DROP TABLE SOD_Rules_{result[3]}"
            cursor.execute(new_query)
            db.commit()
        new_query=f"CREATE TABLE SOD_Rules_{result[3]} SELECT * FROM Original_SOD_Rule_Set;" 
        cursor.execute(new_query)
        db.commit()
        cursor.close()
        db.close()
        return {'usertype':result[2] ,'company' : result[3] ,'active': result[6], 'UserID' : result[0] }
    else:
        return {'usertype':-1}

'''
    
  
@app.post("/signup")
async def signupasync(credentials: SessionData):
    db = modules.connector.connect_db(database='sod')
    existing_user = "Select * from users where email = %s"
    if existing_user:
        insert_logs(credentials.UserID, credentials.Company, credentials.WebSocketID, "Signup", "User already registered")
        raise HTTPException(status_code=409, detail="User already registered")
    else:
        insert_logs(credentials.UserID, credentials.Company, credentials.WebSocketID, "Signup", "New user registered")
        pass
    ##########INSERT NEW USER ON ELSE
    #db_user = User(name=user.name, email=user.email, password=user.password)
    #db.add(db_user)
    #db.commit()
    #db.refresh(db_user)
    return db_user



@app.post("/get_results")
async def read_items(session:SessionData):
    #try:
        output_zip = f"{current}{separator}{session.Company}_Role_Conflicts_Details_{session.UserID}.xlsx"
        if not os.path.exists(output_zip):
            users = f"Role_to_Users_{session.UserID}"
            permissions = f"Role_to_Permissions_{session.UserID}"
            rules = f"SOD_Rules"
            exists_permissions = verify_table(session.UserID, permissions,session.Company, session.WebSocketID)
            exists_RuleSet = verify_table(session.UserID, rules, session.Company, session.WebSocketID)
            exists_users = verify_table(session.UserID, users,session.Company, session.WebSocketID)
            if exists_permissions != -1 and exists_RuleSet != -1 and exists_users != -1:
                df, output_zip = call_role_analysis(session.Company,session.UserID, session.WebSocketID)
                insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results", "Role analysis completed")
                if df is None:
                    if output_zip >= 0 and output_zip <= 2:
                        if output_zip == 0:
                            table_name = users
                        elif output_zip == 1:
                            table_name = permissions
                        else:
                            table_name = rules
                        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results", f'{table_name} is empty')
                        return {"Result": f'{table_name} is empty'}
                    else:
                        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results", f'Without conficts')
                        return {"Result": "Analysis without conficts"}
            else:
                message = f"No Results for company {session.Company} were found, Have been all the files already uploaded?"
                insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results", message)
                return {"Result" : message}
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results", f"{output_zip.split(separator)[-1]} file returned")
        return FileResponse(output_zip, media_type="application/zip",filename=output_zip.split(separator)[-1], headers={"Access-Control-Expose-Headers": "Content-Disposition"})
    #except Exception as e:
    #    return {"Result" : f"No Results for comapany {company} were found, Have been all the files already uploaded?"}

'''@app.post("/get_results_filtered")
async def read_items(session:SessionData):
    #try:
        users = f"Role_to_Users_Filtered_{session.UserID}"
        permissions = f"Role_to_Permissions_Filtered_{session.UserID}"
        rules = f"SOD_Rules"
        exists_permissions_filtered = verify_table(session.UserID, permissions,session.Company, session.WebSocketID)
        exists_RuleSet = verify_table(session.UserID, rules, session.Company, session.WebSocketID)
        exists_users_filtered = verify_table(session.UserID, users,session.Company, session.WebSocketID)
        if exists_permissions_filtered != -1 and exists_RuleSet != -1 and exists_users_filtered != -1:
            df, output_zip = call_role_analysis(session.Company,session.UserID, session.WebSocketID, False)
            insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results Filtered", "Role analysis completed")
            if df is None:
                if output_zip >= 0 and output_zip <= 2:
                    if output_zip == 0:
                        table_name = users
                    elif output_zip == 1:
                        table_name = permissions
                    else:
                        table_name = rules
                    insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results Filtered", f'{table_name} is empty')
                    return {"Result": f'{table_name} is empty'}
                else:
                    insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results Filtered", f'Without conficts')
                    return {"Result": "Analysis without conficts"}
        else:
            message = f"No Results for company {session.Company} were found, Have been all the files already uploaded?"
            insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results Filtered", message)
            return {"Result" : message}
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results Filtered", f"{output_zip.split(separator)[-1]} file returned")
        return FileResponse(output_zip, media_type="application/zip",filename=output_zip.split(separator)[-1], headers={"Access-Control-Expose-Headers": "Content-Disposition"})
    #except Exception as e:
    #    return {"Result" : f"No Results for comapany {company} were found, Have been all the files already uploaded?"}

'''
'''
@app.get("/get_results/")
async def read_items(company: str):
    #DB= f"{current}\\Data\\SOD.db"
    R_User = f"Role_to_Users_{company}"
    R_Permission = f"Role_to_Permissions_{company}"
    SOD= f"SOD_Rule_Set_{company}"
    TMP = f"{current}{separator}Aiver_Default_Ruleset_Processedtmp.xlsx"
    DRS=f"{current}{separator}Aiver_Default_Ruleset_Processed.xlsx"
    output_path = f"{current}{separator}IMRX_SOD_Analysis.xlsx"
    output_pdf = f"{current}{separator}Explanation.pdf"
    output_zip = f"{current}{separator}IMRXSOD.zip"
    RoleAnalisys.Role_analysis("Current",engine,R_User,R_Permission,SOD,TMP,DRS,output_path,output_pdf,output_zip)
    return FileResponse(output_zip, media_type="application/zip",filename=output_zip.split("\\")[-1])

'''

 
#### UPLOADING FUNCTIONS ############################################################    
    
@app.post("/upload_user")
async def upload_single_file(session: str = Form(...), file: UploadFile = File(...)):
    #print(f"Saving {destination_file_path}")# location to store file
    session_data = json.loads(session)
    UserID = session_data.get('UserID', '')
    Company = session_data.get('Company', '')
    WebSocketID = session_data.get('WebSocketID', '')
    insert_logs(UserID, Company, WebSocketID, "Upload Users", "Upload Users process started")
    exists_permissions = verify_table(UserID, f"Role_to_Permissions_{UserID}", Company, WebSocketID)
    exists_RuleSet = verify_table(UserID, f"SOD_Rules", Company, WebSocketID)
    filename= file.filename
    file_extension = os.path.splitext(filename)[1]
    print(f"file extension {file_extension}\n")
    destination_file_path = f"{current}{separator}Users_{UserID}{file_extension}"
    print(destination_file_path)
    #try:
    async with aiofiles.open(destination_file_path, 'wb') as out_file:
        while content := await file.read(1024):  # async read file chunk
            await out_file.write(content)  # async write file chunk
    #xlsx_file = pd.read_excel(R_User, sheet_name="Role to Users", engine='openpyxl')
    with dynamic_engine(Company) as engine:
        if file_extension == '.xlsx':
            insert_logs(UserID, Company, WebSocketID, "Upload Users", "Reading xlsx file")
            xlsx_file = pd.read_excel(destination_file_path, sheet_name=0, engine='openpyxl')
        elif file_extension == '.csv':
            insert_logs(UserID, Company, WebSocketID, "Upload Users", "Reading csv file")
            xlsx_file = pd.read_csv(destination_file_path, sheet_name=0, engine='openpyxl')
        else:
            insert_logs(UserID, Company, WebSocketID, "Upload Users", "Invalid File Type")
            return {"Result" : -2}
        try:
            insert_logs(UserID, Company, WebSocketID, "Upload Users", "Cleaning Data")
            xlsx_file = xlsx_file.map(lambda x: x.strip() if isinstance(x, str) else x)
        except:
            pass
        xlsx_file.to_sql(name=f"Role_to_Users_{UserID}", con= engine, if_exists="replace", index=False)
        insert_logs(UserID, Company, WebSocketID, "Upload Users", f"Role_to_Users_{UserID} table created")
        xlsx_file.to_sql(name=f"Role_to_Users_Filtered_{UserID}", con= engine, if_exists="replace", index=False)
        insert_logs(UserID, Company, WebSocketID, "Upload Users", f"Role_to_Users_Filtered_{UserID} table created")
        if exists_permissions != -1 and exists_RuleSet != -1:
            df , zipfile = call_role_analysis(Company, UserID, WebSocketID)
        insert_logs(UserID, Company, WebSocketID, "Upload Users", "Upload Users process completed")
        return {"Result": "OK"}
    #except Exception as e:
    #    return {"Result":-3}'''


@app.post("/get_user_html")
async def read_user_items(session:SessionData):
    try:
        identifier = f"Role_to_Users_{session.UserID}"
        table_name = 'Role_to_Users'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get user html", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/upload_permission/")
async def upload_single_file(session: str = Form(...) ,file: UploadFile = File(...)):
    #print(f"Saving {destination_file_path}")# location to store file
    session_data = json.loads(session)
    UserID = session_data.get('UserID', '')
    Company = session_data.get('Company', '')
    WebSocketID = session_data.get('WebSocketID', '')
    insert_logs(UserID, Company, WebSocketID, "Upload Permissions", "Upload Permissions process started")
    exist_user = verify_table(UserID, f"Role_to_Users_{UserID}", Company, WebSocketID)
    exists_RuleSet = verify_table(UserID, f"SOD_Rules", Company, WebSocketID)
    filename= file.filename
    file_extension = os.path.splitext(filename)[1]
    destination_file_path =  f"{current}{separator}Permission_{UserID}{file_extension}"
    destination_file_path2 =  f"{current}{separator}Permission_{UserID }2{file_extension}"
    print(destination_file_path, destination_file_path2)
    #try:
    async with aiofiles.open(destination_file_path, 'wb') as out_file:
        while content := await file.read(1024):  # async read file chunk
            await out_file.write(content)  # async write file chunk
    #xlsx_file = pd.read_excel(R_Permission, sheet_name="Role to Permissions", engine='openpyxl')
    with dynamic_engine(Company) as engine:
        if file_extension == '.xlsx':
            insert_logs(UserID, Company, WebSocketID, "Upload Permissions", "Reading xlsx file")
            df = pd.read_excel(destination_file_path,sheet_name=0,engine='openpyxl')
        elif file_extension == '.csv':
            insert_logs(UserID, Company, WebSocketID, "Upload Permissions", "Reading csv file")
            df = pd.read_csv(destination_file_path,sheet_name=0,engine='openpyxl')
        else:
            insert_logs(UserID, Company, WebSocketID, "Upload Permissions", "Invalid File Type")
            return {"Result" : -3}
        if 'Name' in df.columns:
            df = df.rename(columns={'Name': 'Role'})
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
            pd.DataFrame(transformed_data).to_excel(destination_file_path2,index=False)
            insert_logs(UserID, Company, WebSocketID, "Upload Permissions", "Reading xlsx file")
            xlsx_file = pd.read_excel(f'{destination_file_path2}', sheet_name=0, engine='openpyxl')
        else:
            xlsx_file = df
        xlsx_file = xlsx_file[['Role', 'Permission', 'Level', 'Category']]
        xlsx_file.to_sql(name=f"Role_to_Permissions_{UserID}", con=engine, if_exists="replace", index=False)
        insert_logs(UserID, Company, WebSocketID, "Upload Permissions", f"Role_to_Permissions_{UserID} table created")
        xlsx_file.to_sql(name=f"Role_to_Permissions_Filtered_{UserID}", con=engine, if_exists="replace", index=False)
        insert_logs(UserID, Company, WebSocketID, "Upload Permissions", f"Role_to_Permissions_Filtered_{UserID} table created")
        if exist_user != -1 and exists_RuleSet != -1:
            df , zipfile = call_role_analysis(Company, UserID, WebSocketID)
        insert_logs(UserID, Company, WebSocketID, "Upload Permissions", "Upload Permissions process completed")
        return {"Result": "OK"}
    #except Exception as e:
    #    return {"Result" : -1}



@app.post("/get_permission_html")
async def read_user_items(session:SessionData):
    try:
        identifier = f"Role_to_Permissions_{session.UserID}"
        table_name = 'Role_to_Permissions'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get permission html", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)

'''
@app.post("/upload_SOD/")
async def upload_single_file(file: UploadFile = File(...)):
    file_type = file.content_type
    filename = file.filename,
    file_type = file_type,
    company = company
    destination_file_path = f"SOD_{company}.{file_type}" # location to store file
    try:
        async with aiofiles.open(destination_file_path, 'wb') as out_file:
            while content := await file.read(1024):  # async read file chunk
                await out_file.write(content)  # async write file chunk
        xlsx_file = pd.read_excel(f'destination_file_path', sheet_name=0, engine='openpyxl')
        #role_analysis = RoleAnalysis.Role_analysis()
        #role_analysis.to_sql('Role_Analysis', engine, if_exists='replace', index=False)
        #xlsx_file = pd.read_excel(SOD, sheet_name=0, engine='openpyxl')
        xlsx_file.to_sql(name=f"SOD_Rules_{company}", con= engine, if_exists="replace", index=False)
        xlsx_file.to_sql(name="SOD_Rules_Filtered_{company}", con= engine, if_exists="replace", index=False)
        return {"Result": "OK"}
    except Exception as e:
        return {"Result" : -1}
'''

@app.post("/get_SOD_html")
async def read_user_items(session:SessionData):
    try:
        table_name_0 = "SOD_Rules"
        table_name_1 = f"SOD_Rules_{session.UserID}"
        identifier = f"SOD_Rules_{session.UserID}"
        html_table_blue_light = generate_sod_rulset_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name_0, table_name_1)#generate_table(df, identifier)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get SOD html", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)
    
    
    

# You don't need a separate OPTIONS handler if you're using CORSMiddleware correctly
# The CORSMiddleware will handle OPTIONS requests automatically
#































































@app.post("/get_single_role_conflicts")
async def read_user_items(session:SessionData):
    try:
        identifier = f"Single_Role_Conflicts_{session.UserID}"
        table_name = 'Single_Role_Conflicts'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get single role conflicts", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


'''
@app.get("/get_multiple_role_conflicts/")
async def read_user_items(company: str):
    try:
        df = pd.read_sql(f"Select * from Multiple_Role_Conflicts_{company}", engine)
        identifier = f"multipleRole_{company}"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)
#Revisar
'''


@app.post("/get_single_merged_role_to_permissions/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"mergedUsers_{session.UserID}"
        table_name = 'Merged_Users_to_Permissions'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get single merged role to permissions", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/get_single_role_analysis/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"singleRole_{session.UserID}"
        table_name = 'Single_Role_Analysis'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get single role analysis", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/get_Single_Role_Analysis_Grouped_by_Name/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"singleRoleG_{session.UserID}"
        table_name = 'Single_Role_Analysis_Grouped_by_Name'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get single role analysis grouped by name", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/SOD_Count_Per_Role/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"SODCPR_{session.UserID}"
        table_name = 'SOD_Count_Per_Role'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "SOD count per role", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/Single_Role_Analysis_Grouped_by_Name_SOD_Rule/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"singleRoleAnalysisGN_{session.UserID}"
        table_name = 'Single_Role_Analysis_Grouped_by_Name_SOD_Rule'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Single role analysis grouped by name sod rules", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/Single_Role_Analysis_Grouped_by_SOD_Rule_Role/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"singleRoleAnalysisGR_{session.UserID}"
        table_name = 'Single_Role_Analysis_Grouped_by_SOD_Rule_Role'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get single role analysis grouped by SOD rule role", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/SOD_List_Count/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"SODLC_{session.UserID}"
        table_name = 'SOD_List_Count'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "SOD list count", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/get_multiple_role_analysis/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"multipleRoleAnalysis_{session.UserID}"
        table_name = 'Multiple_Role_Analysis'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get multiple role analysis", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/Single_Role_Analysis_Grouped_by_Name/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"singleRoleAGN_{session.UserID}"
        table_name = 'Single_Role_Analysis_Grouped_by_Name'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Single role analysis grouped by name", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/Multiple_SOD_Count_Combined/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"SODCC_{session.UserID}"
        table_name = 'Multiple_SOD_Count_Combined'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Multiple SOD count combined", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"multipleRoleAnalysisGR_{session.UserID}"
        table_name = 'Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Multiple role analysis grouped by name SOD rule", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"multipleRole_AGSR_{session.UserID}"
        table_name = 'Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Multiple role analysis grouped by SOD rule role BP1", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/SOD_List_Count_Multi/")
async def read_user_items(session: SessionData):
    try:
        identifier = f"sodLCM_{session.UserID}"
        table_name = 'SOD_List_Count_Multi'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "SOD list count multi", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)

#Revisar
@app.post("/Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2/")
async def read_user_items(session: SessionData):
    try:
        #html_table_blue_light += "<br><br>"
        #df = pd.read_sql(f"Select * from SOD_List_Count_Multi", engine)
        #html_table_blue_light += build_table(df, 'blue_light')
        identifier = f"multipleRAGR_{session.UserID}"
        table_name = 'Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Multiple role analyis grouped by SOD rule role BP2", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


'''
@app.post("/get_overall_analysis/")
async def read_user_items(session: SessionData):
    try:
        df = pd.read_sql(f"Select * from Overall_Analysis_{company}", engine)
        identifier = f"overallAnalisys_{company}"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.post("/Overall_Analysis_Grouped_by_SOD_Rule_Role/")
async def read_user_items(session: SessionData):
    try:
        df = pd.read_sql(f"Select * from Overall_Analysis_Grouped_by_SOD_Rule_Role_{company}", engine)
        identifier = f"overalAnalysisGR_{company}"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.post("/SOD_List_Count_Overall/")
async def read_user_items(session: SessionData):
    try:
        df = pd.read_sql(f"Select * from SOD_List_Count_Overall_{company}", engine)
        identifier = f"sodLCO_{company}"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.post("/get_overall_conflicts/")
async def read_user_items(session: SessionData):
    try:
        df = pd.read_sql(f"Select * from Overall_Conflicts_{company}", engine)
        identifier = f"overallConflicts_{company}"
        html_table_blue_light = generate_table(df, identifier)
        return HTMLResponse(content=html_table_blue_light, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)
'''
@app.post("/get_data")
async def get_data(session: SessionData):
    try:
        endpoints = {
            f"Single_Role_Conflicts": "Single Role Conflicts",
            #f"Multiple_Role_Conflicts_{company}": "Multiple Role Conflicts",
            f"Merged_Users_to_Permissions": "Merged Users to Permissions",
            f"Single_Role_Analysis": "Single Role Analysis",
            f"Single_Role_Analysis_Grouped_by_Name": "Single Role Analysis Grouped by Name",
            f"SOD_Count_Per_Role": "SOD Count Per Role",
            f"Single_Role_Analysis_Grouped_by_Name_SOD_Rule": "Single Role Analysis Grouped by Name SOD Rule",
            f"Single_Role_Analysis_Grouped_by_SOD_Rule_Role": "Single Role Analysis Grouped by SOD Rule Role",
            f"SOD_List_Count": "SOD List Count",
            f"Multiple_Role_Analysis": "Multiple Role Analysis",
            f"Multiple_Role_Analysis_Grouped_by_Name": "Multiple Role Analysis Grouped by Name",
            f"Multiple_SOD_Count_Combined": "Multiple SOD Count Combined",
            f"Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule": "Multiple Role Analysis Grouped by Name SOD Rule",
            f"Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1": "Multiple Role Analysis Grouped by SOD Rule Role BP1",
            f"SOD_List_Count_Multi": "SOD List Count Multi",
            f"Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2": "Multiple Role Analysis Grouped by SOD Rule Role BP2"
        }
        identifier = f'get_data_{session.UserID}'
        html_tables = generate_dash_tables(app, session.Company, session.UserID, session.WebSocketID, identifier, endpoints)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Data", "Data tables returned")
        return html_tables
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Data", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail='Loading Error')















































































































@app.post("/get_users_name_array/")
async def read_user_items(session: SessionData):
    try:
        df = get_df_from_table(session.Company, session.UserID, 'Role_Level_Conflicts')
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



@app.post("/set_user_filters/")
async def set_user_filters(userdata: UserData, session: SessionData):
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
    with dynamic_engine(session.Company) as engine:
        try:
            df = pd.read_sql(f"Select * from Role_Level_Conflicts_{session.UserID} where 1 {adding_string}", engine)
            df.to_sql(name=f"Role_Level_Conflicts_Filtered_{session.UserID}", con=engine, if_exists="replace", index=False)
            return {"Result": "OK"}
        except Exception as e:
            return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)


@app.post("/get_permission_arrays/")
async def read_permission_items(session: SessionData):
    #try:
    df = get_df_from_table(session.Company, session.UserID, 'Merged_Users_to_Permissions')
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






@app.post("/set_permission_filters/")
async def set_user_filters(permissiondata: PermissionData,session: SessionData):
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
    with dynamic_engine(session.Company) as engine:
        df = pd.read_sql(f"Select * from Single_Role_Conflicts_{session.UserID}  where 1 {adding_string}", engine)
        df.to_sql(name=f"Single_Role_Conflicts_Filtered_{session.UserID}", con=engine, if_exists="replace", index=False)
        return {"Result": "OK"}
    #except Exception as e:
    #    return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)




@app.post("/get_SOD_arrays/")
async def read_sod_items(session: SessionData):
    try:
        df = get_df_from_table(session.Company, session.UserID, 'Merged_Users_to_Permissions')
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






@app.post("/set_SOD_filters/")
async def set_user_filters(soddata: SODData,    session: SessionData):
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
    sql= f"Select * from Merged_Users_to_Permissions_{session.UserID} where 1 {adding_string}"
    #print(sql)    
    #try:
    with dynamic_engine(session.Company) as engine:
        df = pd.read_sql(f"{sql}", engine)
        df.to_sql(name=f"{session.Company}.Merged_Users_to_Permissions_Filtered_{session.UserID}", con=engine, if_exists="replace", index=False)
        return {"Result": "OK"}
    #except Exception as e:
    #    return HTMLResponse(content=f"<h1>No data in the database <br></h1> <br> <h3>{e}<h3/>", status_code=200)













@app.post("/get_user_html_filtered")
async def read_user_items(session:SessionData):
    try:
        identifier = f"roleUsersFiltered_{session.UserID}"
        table_name = 'Role_Level_Conflicts_Filtered'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get user html filtered", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/get_permission_html_filtered")
async def read_user_items(session:SessionData):
    try:
        identifier = f"rolePermissionsFiltered_{session.UserID}" 
        table_name = 'Single_Role_Conflicts_Filtered'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get permission html filtered", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/get_SOD_html_filtered")
async def read_user_items(session:SessionData):
    try:
        identifier = f"sodRulesFiltered_{session.UserID}"
        table_name = 'Merged_Users_to_Permissions_Filtered'
        html_table_blue_light = generate_dash_table(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name)
        return html_table_blue_light
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get SOD html filtered", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)
    

@app.post("/get_filtered/")
async def get_filtered(session: SessionData):
    try:
        endpoints = {
            "Role_Level_Conflicts_Filtered": "Role Level Conflicts",
            "Single_Role_Conflicts_Filtered": "Single Role Conflicts",
            "Merged_Users_to_Permissions_Filtered": "Merged Users to Permissions",
        }
        identifier = f'get_filtered_{session.UserID}'
        html_tables = generate_dash_tables(app, session.Company, session.UserID, session.WebSocketID, identifier, endpoints)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Filtered", "Data tables returned")
        return html_tables
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Filtered", f"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


########## DASHBOARD #############

@app.post("/dashboard")
async def get_dashboard(session: SessionData):
    try:
        identifier = f'get_dashboard_{session.UserID}'
        html_dashboard = create_interactive_dashboard(app, session.Company, session.UserID, session.WebSocketID, identifier)
        return html_dashboard
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Dashboard", F"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)

async def cleanup_inactive_dashboards_and_grids():
    while True:
        await asyncio.sleep(3600)
        dashboards_removed = remove_inactivity_dashboards(app)

#This is deprecated
'''@app.on_event("startup")
async def start_cleanup_task():
    asyncio.create_task(cleanup_inactive_dashboards_and_grids())'''


########## WEBSOCKETS ############

@app.websocket("/ws/{identifier}")
async def websocket_endpoint(websocket: WebSocket, identifier:str):
    await manager.connect(websocket, identifier)
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
    except WebSocketDisconnect:
        manager.disconnect(identifier)
        print(f'Websocket id: {identifier} disconnected')

'''@app.get('/send_message')
async def send_message(message:str, identifier:str):
    manager.send_personal_message(message, identifier)'''


########################## FILTER ######################################

@app.post("/filter_table")
async def test_filter(session: SessionDataFiltered):
    if session.Option == 0:
        #table_name = 'Role_to_Users'
        table_name = 'Role_Level_Conflicts'
        file_name = 'Role_Level_Conflicts_Detailed.csv'
    elif session.Option == 1:
        #table_name = 'Role_to_Permissions'
        table_name = 'Role_Level_Conflicts_Simplified'
        file_name = 'Role_Level_Conflicts_Simplified.csv'
    elif session.Option == 2:
        table_name = 'Merged_Users_to_Permissions'
        file_name = 'Client_Data.csv'
    elif session.Option == 3:
        table_name = 'Single_Role_Conflicts'
        file_name = 'Client_Data_Simplified.csv'
    else:
        raise HTTPException(status_code=409, detail='Invalid Option')
    try:
        identifier = f'get_{table_name}_Filtered_{session.UserID}'
        html_dashboard = generate_dash_table_filter(app, session.Company, session.UserID, session.WebSocketID, identifier, table_name, file_name)
        return html_dashboard
    except Exception as e:
        print(e)
        insert_logs(session.UserID, session.Company, session.WebSocketID, "Filter Table", F"An error has ocurred: {e}")
        raise HTTPException(status_code=500, detail=error_message)


######### TEST ############
@app.post("/Role_Level_Conflicts")
async def get_JSON(session: SessionData):
    try:
        with dynamic_engine(session.Company) as engine:
            query = f'''WITH Top_10 AS (
                            SELECT `Role`, COUNT(*) AS `Count`
                            FROM(
                                SELECT `Role`, `Business Cycle`
                                FROM `Role_Level_Conflicts_{session.UserID}`
                                GROUP BY `Role`, `Business Cycle`
                            ) AS `Simplified`
                            GROUP BY `Role`
                            ORDER BY `Count` DESC
                            LIMIT 10
                        )
                        SELECT s1.`Role`, s1.`Business Cycle`, COUNT(*) AS `Count`
                        FROM `Role_Level_Conflicts_{session.UserID}` AS s1
                        INNER JOIN `Top_10` AS s2 ON s1.`Role`=s2.`Role`
                        GROUP BY `Role`, `Business Cycle`;'''
            df = pd.read_sql(query, engine)
            columns = df.columns.tolist()
            response = {
                "columns": columns
            }
            for column in df.columns:
                response[column]=df[column].tolist()
            return response
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)






























if __name__ == "__main__":
    print(f"################################# THIS IS THE PID {os.getpid()} ##################################################" )
    uvicorn.run("API:app", host="0.0.0.0",  port=5678, reload=False, ssl_keyfile="/storage/certs/privkey.pem", ssl_certfile="/storage/certs/fullchain.pem")
