from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Form
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from WebSocketManagerConnection import manager
import logging
from contextlib import asynccontextmanager
from pydantic import BaseModel
import uvicorn
import modules.connector
import charts
import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

env_file_path = Path(__file__).parent / '.env'
load_dotenv(env_file_path, override=True)
import aiofiles
import openpyxl
import os
import pathlib
import json
import datetime
import pandas as pd
import numpy as np
import sys
import RoleAnalisys
import re
import asyncio
from werkzeug.security import generate_password_hash, check_password_hash
from SODDash import clear, generate_sod_rulset_table, generate_dash_table, generate_dash_tables, create_interactive_dashboard, remove_inactivity_dashboards, generate_dash_table_filter
from Models_and_engine import dynamic_engine, SessionData, SessionDataFilter, UpdateSODRuleSet, RemoveSODRules, insert_logs, create_logs_table, SessionDataFiltered, dynamic_connection
from load_data import decompress_file, start_load_data
import numpy as np
import threading

try:
    import websockets
except ImportError:
    websockets = None

try:
    import wsproto
except ImportError:
    wsproto = None

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
created_tables=[
    'All_Role_Risk',
    'children_permissions',
    'employees',
    'employee_global_permissions',
    'employee_roles',
    'global_permissions',
    #'Individual_Role_Risk',
    #'Individual_Role_Risk_Detailed',
    'roles',
    'role_permissions',
    'role_subsidiaries',
    'Role_To_Permissions_Union',
    'SOD_Rules_cleaned',
    'subsidiaries',
    #'user_risk_final',
    #'user_risk_detailed',
    #'user_risk_detailed_final',
    'user_subsidiary_role_permissions',
    'user_subsidiary_role_permissions_global',
    'user_subsidiary_role_permissions_global_union',
    'user_subsidiary_role_permissions_global_union_final'
]

ANALYSIS_CONTEXT_TABLES = {
    "Single_Role_Conflicts": "Single Role Conflicts",
    "Merged_Users_to_Permissions": "Merged Users to Permissions",
    "Single_Role_Analysis": "Single Role Analysis",
    "Single_Role_Analysis_Grouped_by_Name": "Single Role Analysis Grouped by Name",
    "SOD_Count_Per_Role": "SOD Count Per Role",
    "Single_Role_Analysis_Grouped_by_Name_SOD_Rule": "Single Role Analysis Grouped by Name SOD Rule",
    "Single_Role_Analysis_Grouped_by_SOD_Rule_Role": "Single Role Analysis Grouped by SOD Rule Role",
    "SOD_List_Count": "SOD List Count",
    "Multiple_Role_Analysis": "Multiple Role Analysis",
    "Multiple_Role_Analysis_Grouped_by_Name": "Multiple Role Analysis Grouped by Name",
    "Multiple_SOD_Count_Combined": "Multiple SOD Count Combined",
    "Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule": "Multiple Role Analysis Grouped by Name SOD Rule",
    "Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1": "Multiple Role Analysis Grouped by SOD Rule Role BP1",
    "SOD_List_Count_Multi": "SOD List Count Multi",
    "Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2": "Multiple Role Analysis Grouped by SOD Rule Role BP2"
}

ADDITIONAL_CONTEXT_TABLES = {
    "Individual_Role_Risk": "Individual Role Risk",
    "Individual_Role_Risk_Detailed": "Individual Role Risk Detailed",
    "user_risk_final": "User Risk",
    "user_risk_detailed_final": "User Risk Detailed",
    "employees": "Employees",
    "roles": "Roles",
    "subsidiaries": "Subsidiaries",
    "employee_global_permissions": "Employee Global Permissions",
    "employee_roles": "Employee Roles",
    "role_permissions": "Role Permissions",
    "role_subsidiaries": "Role Subsidiaries",
    "SOD_Rules": "SOD Rules"
}

OLLAMA_FULL_CONTEXT_MAX_CHARS = 200000
OLLAMA_SMALL_TABLE_FULL_ROWS = 200
OLLAMA_LARGE_TABLE_SAMPLE_ROWS = 25




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

current_files = f"{current}{separator}Data"
chat_log_path = f"{current}{separator}logs"
chat_log_file = f"{chat_log_path}{separator}chat_activity.log"

if not os.path.exists(current_files):
    os.makedirs(current_files)
if not os.path.exists(chat_log_path):
    os.makedirs(chat_log_path)

def write_chat_log(entry: str):
    try:
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        with open(chat_log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {entry}\n")
    except Exception:
        pass


def get_chat_settings():
    dot_env = dotenv_values(env_file_path)
    provider = (dot_env.get('CHAT_PROVIDER') or os.getenv('CHAT_PROVIDER') or 'api').strip().lower()
    return {
        'provider': provider,
        'base_url': (dot_env.get('CHAT_BASE_URL') or os.getenv('CHAT_BASE_URL') or 'https://api.openai.com').strip(),
        'chat_endpoint': (dot_env.get('CHAT_CHAT_ENDPOINT') or os.getenv('CHAT_CHAT_ENDPOINT') or '/v1/chat/completions').strip(),
        'api_key': (dot_env.get('CHAT_API_KEY') or os.getenv('CHAT_API_KEY') or '').strip(),
        'port': (dot_env.get('CHAT_PORT') or os.getenv('CHAT_PORT') or '').strip(),
        'model': (dot_env.get('CHAT_MODEL') or os.getenv('CHAT_MODEL') or 'gpt-4o-mini').strip(),
        'ollama_base_url': (dot_env.get('OLLAMA_BASE_URL') or os.getenv('OLLAMA_BASE_URL') or 'http://localhost').strip(),
        'ollama_port': (dot_env.get('OLLAMA_PORT') or os.getenv('OLLAMA_PORT') or '11434').strip(),
        'ollama_model': (dot_env.get('OLLAMA_MODEL') or os.getenv('OLLAMA_MODEL') or 'llama2').strip(),
        'ollama_chat_endpoint': (dot_env.get('OLLAMA_CHAT_ENDPOINT') or os.getenv('OLLAMA_CHAT_ENDPOINT') or '/chat').strip(),
    }


def _safe_sql_identifier(name: str) -> str:
    return name.replace('`', '``')


def _stringify_value(value):
    if value is None:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    return value


def _table_to_context_text(cursor, physical_table: str, logical_table: str, display_name: str) -> dict:
    safe_table = _safe_sql_identifier(physical_table)

    cursor.execute(f"SELECT COUNT(*) FROM `{safe_table}`")
    row_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT * FROM `{safe_table}` LIMIT 1")
    columns = [column[0] for column in (cursor.description or [])]

    if row_count <= OLLAMA_SMALL_TABLE_FULL_ROWS:
        cursor.execute(f"SELECT * FROM `{safe_table}`")
    else:
        cursor.execute(f"SELECT * FROM `{safe_table}` LIMIT {OLLAMA_LARGE_TABLE_SAMPLE_ROWS}")
    rows = cursor.fetchall()

    cleaned_rows = [[_stringify_value(value) for value in row] for row in rows]
    sample_df = pd.DataFrame(cleaned_rows, columns=columns) if columns else pd.DataFrame()

    lines = [
        f"TABLE_START {logical_table}",
        f"display_name={display_name}",
        f"physical_table={physical_table}",
        f"rows={row_count}",
        f"cols={len(columns)}",
        f"columns={', '.join(columns)}",
    ]

    if row_count == 0:
        lines.append('data=No rows available.')
    elif row_count <= OLLAMA_SMALL_TABLE_FULL_ROWS:
        csv_text = sample_df.to_csv(index=False)
        lines.append('data_mode=full')
        lines.append(csv_text)
    else:
        lines.append('data_mode=summary')
        lines.append(f"sample_rows={len(sample_df)}")
        lines.append(sample_df.to_csv(index=False))
        lines.append('top_counts=')
        for col in columns[:3]:
            safe_col = _safe_sql_identifier(col)
            try:
                cursor.execute(
                    f"SELECT `{safe_col}`, COUNT(*) AS total FROM `{safe_table}` "
                    f"GROUP BY `{safe_col}` ORDER BY total DESC LIMIT 5"
                )
                counts = cursor.fetchall()
                count_parts = []
                for item in counts:
                    value = _stringify_value(item[0])
                    total = item[1]
                    count_parts.append(f"{value}:{total}")
                lines.append(f"{col}: {', '.join(count_parts)}")
            except Exception as e:
                lines.append(f"{col}: count_summary_error={str(e)}")

    lines.append(f"TABLE_END {logical_table}")
    return {
        'logical_table': logical_table,
        'physical_table': physical_table,
        'display_name': display_name,
        'rows': int(row_count),
        'cols': len(columns),
        'columns': columns,
        'text': '\n'.join(lines),
    }


def _all_expected_context_tables() -> dict:
    tables = dict(ANALYSIS_CONTEXT_TABLES)
    tables.update(ADDITIONAL_CONTEXT_TABLES)
    return tables


def build_full_ollama_context(company: str, user_id: str, websocket_id: str | None) -> dict:
    write_chat_log(f"CHAT CONTEXT BUILD START company={company} user_id={user_id} websocket_id={websocket_id}")

    expected_tables = _all_expected_context_tables()
    expected_table_names = list(expected_tables.keys())
    checked_tables = []
    tables_found = []
    tables_missing = []
    table_summaries = []
    text_blocks = []
    sheets_found = []
    excel_found = False

    output_path = f"{current_files}{separator}{company}_report_{user_id}.xlsx"
    if os.path.exists(output_path):
        try:
            excel_found = True
            xls = pd.ExcelFile(output_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                rows = int(df.shape[0])
                cols = int(df.shape[1])
                sheets_found.append(sheet_name)
                write_chat_log(f"CHAT CONTEXT EXCEL FOUND sheet={sheet_name} rows={rows} cols={cols}")

                sheet_lines = [
                    f"EXCEL_SHEET_START {sheet_name}",
                    f"rows={rows}",
                    f"cols={cols}",
                    f"columns={', '.join([str(col) for col in df.columns.tolist()])}",
                ]

                if rows == 0:
                    sheet_lines.append('data=No rows available.')
                elif rows <= OLLAMA_SMALL_TABLE_FULL_ROWS:
                    sheet_lines.append('data_mode=full')
                    sheet_lines.append(df.to_csv(index=False))
                else:
                    sheet_lines.append('data_mode=summary')
                    sheet_lines.append(f"sample_rows={OLLAMA_LARGE_TABLE_SAMPLE_ROWS}")
                    sheet_lines.append(df.head(OLLAMA_LARGE_TABLE_SAMPLE_ROWS).to_csv(index=False))
                    for column in df.columns[:3]:
                        try:
                            top_values = df[column].value_counts(dropna=False).head(5).to_dict()
                            sheet_lines.append(f"{column}_top_counts={top_values}")
                        except Exception as e:
                            sheet_lines.append(f"{column}_top_counts_error={str(e)}")

                sheet_lines.append(f"EXCEL_SHEET_END {sheet_name}")
                text_blocks.append('\n'.join(sheet_lines))
        except Exception as e:
            write_chat_log(f"CHAT CONTEXT EXCEL ERROR file={output_path} error={str(e)}")

    try:
        with dynamic_connection(company) as conn:
            cursor = conn.cursor()
            try:
                for logical_table, display_name in expected_tables.items():
                    checked_tables.append(logical_table)
                    candidate_tables = [f"{logical_table}_{user_id}"]
                    if logical_table not in ['SOD_Rules']:
                        candidate_tables.append(logical_table)
                    else:
                        candidate_tables.extend([logical_table, f"{logical_table}_{user_id}"])

                    selected_table = None
                    checked_candidate_set = []
                    for candidate in candidate_tables:
                        if candidate in checked_candidate_set:
                            continue
                        checked_candidate_set.append(candidate)
                        safe_candidate = _safe_sql_identifier(candidate)
                        cursor.execute(
                            "SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s LIMIT 1",
                            (company, safe_candidate.replace('``', '`'))
                        )
                        exists = cursor.fetchone()
                        if exists:
                            selected_table = candidate
                            break

                    if selected_table is None:
                        tables_missing.append(logical_table)
                        write_chat_log(f"CHAT CONTEXT TABLE MISSING table={logical_table}")
                        continue

                    table_context = _table_to_context_text(cursor, selected_table, logical_table, display_name)
                    tables_found.append(logical_table)
                    table_summaries.append({
                        'logical_table': table_context['logical_table'],
                        'physical_table': table_context['physical_table'],
                        'rows': table_context['rows'],
                        'cols': table_context['cols'],
                        'display_name': table_context['display_name'],
                    })
                    text_blocks.append(table_context['text'])
                    write_chat_log(
                        f"CHAT CONTEXT TABLE FOUND table={logical_table} rows={table_context['rows']} cols={table_context['cols']}"
                    )
            finally:
                cursor.close()
    except Exception as e:
        write_chat_log(f"CHAT CONTEXT DB ERROR company={company} user_id={user_id} error={str(e)}")
        # Mark all unchecked tables as missing to preserve validation strictness.
        for logical_table in expected_table_names:
            if logical_table not in checked_tables:
                checked_tables.append(logical_table)
            if logical_table not in tables_found and logical_table not in tables_missing:
                tables_missing.append(logical_table)
                write_chat_log(f"CHAT CONTEXT TABLE MISSING table={logical_table} reason=db_connection_failed")

    metadata = {
        'timestamp_utc': datetime.datetime.utcnow().isoformat() + 'Z',
        'company': company,
        'user_id': user_id,
        'websocket_id': websocket_id,
        'tables_expected': expected_table_names,
        'tables_checked': checked_tables,
        'tables_found': tables_found,
        'tables_missing': tables_missing,
        'excel_found': excel_found,
        'sheets_found': sheets_found,
        'table_summaries': table_summaries,
    }

    metadata_block = [
        'SESSION_METADATA_START',
        f"timestamp_utc={metadata['timestamp_utc']}",
        f"company={company}",
        f"user_id={user_id}",
        f"websocket_id={websocket_id}",
        f"tables_expected={len(expected_table_names)}",
        f"tables_found={len(tables_found)}",
        f"tables_missing={len(tables_missing)}",
        f"excel_found={excel_found}",
        f"sheets_found={', '.join(sheets_found)}",
        f"tables_found_names={', '.join(tables_found)}",
        f"tables_missing_names={', '.join(tables_missing)}",
        'SESSION_METADATA_END'
    ]

    raw_context = '\n\n'.join(metadata_block + text_blocks)
    if len(raw_context) > OLLAMA_FULL_CONTEXT_MAX_CHARS:
        raw_context = raw_context[:OLLAMA_FULL_CONTEXT_MAX_CHARS] + '\n...CONTEXT_TRUNCATED...'

    full_context = f"FULL_ANALYSIS_CONTEXT_START\n{raw_context}\nFULL_ANALYSIS_CONTEXT_END"
    context_chars = len(full_context)

    result = {
        **metadata,
        'context_text': full_context,
        'context_preview': full_context[:5000],
        'context_chars': context_chars,
        'excel_path': output_path,
        'has_real_context': bool(excel_found or len(tables_found) > 0),
        'all_expected_tables_checked': set(checked_tables) == set(expected_table_names),
    }

    write_chat_log(
        f"CHAT CONTEXT FINAL tables_found={len(tables_found)} tables_missing={len(tables_missing)} chars={context_chars}"
    )
    return result


def validate_full_ollama_context(context_data: dict) -> dict:
    context_text = context_data.get('context_text') or ''
    tables_missing = context_data.get('tables_missing', [])
    checks = {
        'company_present': bool(context_data.get('company')),
        'user_id_present': bool(context_data.get('user_id')),
        'excel_or_db_context_present': bool(context_data.get('has_real_context')),
        'all_expected_tables_checked': bool(context_data.get('all_expected_tables_checked')),
        'all_expected_tables_present': len(tables_missing) == 0,
        'ollama_context_markers_present': (
            'FULL_ANALYSIS_CONTEXT_START' in context_text
            and 'FULL_ANALYSIS_CONTEXT_END' in context_text
        ),
        'context_non_empty': bool(context_text.strip()),
    }

    errors = []
    if not checks['company_present']:
        errors.append('Missing Company')
    if not checks['user_id_present']:
        errors.append('Missing UserID')
    if not checks['excel_or_db_context_present']:
        errors.append('No Excel or DB context found')
    if not checks['all_expected_tables_checked']:
        errors.append('Not all expected tables were checked')
    if not checks['all_expected_tables_present']:
        errors.append(f"Missing expected tables in database: {', '.join(tables_missing)}")
    if not checks['ollama_context_markers_present']:
        errors.append('Context markers are missing')
    if not checks['context_non_empty']:
        errors.append('Context is empty')

    missing_found_names_in_context = [
        table_name for table_name in context_data.get('tables_found', [])
        if table_name not in context_text
    ]
    if missing_found_names_in_context:
        errors.append(
            'Missing table names inside context: ' + ', '.join(missing_found_names_in_context)
        )

    status = 'passed' if all(checks.values()) and not errors else 'failed'
    if status == 'passed':
        write_chat_log('CHAT OLLAMA VALIDATION PASSED')
    else:
        write_chat_log(f"CHAT OLLAMA VALIDATION FAILED reason={' | '.join(errors)}")

    return {
        'status': status,
        'checks': checks,
        'tables_found': context_data.get('tables_found', []),
        'tables_missing': context_data.get('tables_missing', []),
        'errors': errors,
    }


def _markdown_from_value(value) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ''
    if isinstance(value, (int, float, bool)):
        return str(value)
    try:
        return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"
    except Exception:
        return str(value)

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




async def verify_table(user, table_name,DB, WebSocketID):
    db = modules.connector.connect_db(database=DB)
    mycursor = db.cursor()
    query = f"SELECT TABLE_NAME FROM information_schema.tables WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = '{DB}'"
    mycursor.execute(query)
    result = mycursor.fetchone()
    if result:
        await insert_logs(user, DB, WebSocketID, "Verify Table", f"{table_name} table found")
        return 1
    else:
        await insert_logs(user, DB, WebSocketID, "Verify Table", f"{table_name} table not found")
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

async def call_role_analysis(company,UserID, WebSocketID, option=False):
    if not option:
        risk_tables = ['Individual_Role_Risk', 'Individual_Role_Risk_Detailed', 'user_risk_final', 'user_risk_detailed', 'user_risk_detailed_final']
        exists_tables = []
        for table in risk_tables:
            exists_tables.append(await verify_table(UserID, f"{table}_{UserID}", company, WebSocketID))

        if set(exists_tables) != {1}:
            option = True
    
    output_path = f"{current_files}{separator}{company}_report_{UserID}.xlsx"
    
    def run_async_analysis(loop):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(RoleAnalisys.Role_analysis(output_path, company, UserID, WebSocketID, option))

    if WebSocketID:
        thread_name = f'{company}_{UserID}_{WebSocketID}_analysis_process'
    else:
        thread_name = f'{company}_{UserID}_analysis_process'

    loop = asyncio.new_event_loop()
    process = threading.Thread(
        target=run_async_analysis,
        args=(loop,),
        daemon=True,
        name=thread_name
    )
    process.start()

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
        'https://localhost:8000,https://localhost:8081,http://localhost:8000,http://localhost:8081,'
        'http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173,'
        'http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080',
    ).split(',')
    if origin.strip()
]





##############################Declare THE APP

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('LIFESPAN ACTIVATED')
    if websockets is None or wsproto is None:
        print('[WS_DEPENDENCY] Missing websocket support dependencies:')
        print(f'  websockets installed: {websockets is not None}')
        print(f'  wsproto installed: {wsproto is not None}')
        print('[WS_DEPENDENCY] Install uvicorn[standard] or websockets and wsproto in the environment used for the backend.')
    asyncio.create_task(cleanup_inactive_dashboards_and_grids())
    yield

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger('sod_backend')

app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    body = await request.body()
    request._body = body
    if request.url.path in ['/login', '/signup'] or request.method == 'OPTIONS':
        logger.info('REQUEST method=%s path=%s origin=%s content-type=%s access-control-request-method=%s access-control-request-headers=%s body=%s',
                    request.method,
                    request.url.path,
                    request.headers.get('origin'),
                    request.headers.get('content-type'),
                    request.headers.get('access-control-request-method'),
                    request.headers.get('access-control-request-headers'),
                    body[:1000] if body else b'')
    response = await call_next(request)
    if request.url.path in ['/login', '/signup'] or request.method == 'OPTIONS':
        logger.info('RESPONSE method=%s path=%s status=%s headers=%s',
                    request.method,
                    request.url.path,
                    response.status_code,
                    dict(response.headers))
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body() if hasattr(request, '_body') else b''
    logger.error('VALIDATION_ERROR path=%s method=%s origin=%s headers=%s body=%s errors=%s',
                 request.url.path, request.method, request.headers.get('origin'),
                 dict(request.headers), body[:1000] if body else b'', exc.errors())
    return JSONResponse(status_code=400, content={'detail': 'Bad request', 'errors': exc.errors(), 'body': body.decode('utf-8', errors='replace')[:1000]})


app.include_router(charts.router)


# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/chat_config')
async def chat_config():
    settings = get_chat_settings()
    return {
        'enabled': True,
        'provider': settings['provider'],
        'base_url': settings['base_url'],
        'chat_endpoint': settings['chat_endpoint'],
        'port': settings['port'],
        'model': settings['model'],
        'use_api_key': bool(settings['api_key']),
        'ollama_base_url': settings['ollama_base_url'],
        'ollama_port': settings['ollama_port'],
        'ollama_model': settings['ollama_model'],
    }

@app.post('/chat')
async def chat_endpoint(payload: dict):
    try:
        import urllib.request
        import urllib.error
        import ssl
        import socket

        session = payload.get('session', {})
        message = payload.get('message', '')

        if not message:
            return JSONResponse(status_code=400, content={'error': 'Missing chat message'})

        settings = get_chat_settings()
        provider = settings['provider']
        model = settings['model']
        api_key = settings['api_key']
        base_url = settings['base_url']
        chat_endpoint = settings['chat_endpoint']
        ollama_base_url = settings['ollama_base_url']
        ollama_port = settings['ollama_port']
        ollama_model = settings['ollama_model']
        ollama_chat_endpoint = settings['ollama_chat_endpoint']

        write_chat_log(
            f"CHAT SETTINGS provider={provider} model={model} base_url={base_url} chat_endpoint={chat_endpoint} "
            f"ollama_base_url={ollama_base_url} ollama_port={ollama_port} ollama_chat_endpoint={ollama_chat_endpoint} ollama_model={ollama_model}"
        )

        company = session.get('Company')
        user_id = session.get('UserID')
        websocket_id = session.get('WebSocketID')

        context_data = build_full_ollama_context(company, user_id, websocket_id)
        validation = validate_full_ollama_context(context_data)

        # Only block if there is absolutely no context (no Excel, no DB tables) or
        # if critical session fields are missing. Missing DB tables alone do NOT
        # block the chat when Excel data is available.
        critical_checks_failed = (
            not validation['checks'].get('company_present') or
            not validation['checks'].get('user_id_present') or
            not validation['checks'].get('excel_or_db_context_present')
        )
        if critical_checks_failed:
            checks_failed = [k for k, v in validation['checks'].items() if not v]
            validation_md_lines = [
                '## Chat Context Validation Failed',
                '',
                '- Status: failed',
                f"- Failed checks: {', '.join(checks_failed) if checks_failed else 'none'}",
                f"- Tables found: {len(validation.get('tables_found', []))}",
                f"- Tables missing: {len(validation.get('tables_missing', []))}",
            ]
            if validation.get('tables_missing'):
                validation_md_lines.extend(['', '### Missing Tables'])
                validation_md_lines.extend([f"- {name}" for name in validation.get('tables_missing', [])])
            if validation.get('errors'):
                validation_md_lines.extend(['', '### Validation Errors'])
                validation_md_lines.extend([f"- {err}" for err in validation.get('errors', [])])
            validation_md = "\n".join(validation_md_lines)

            error_response = {
                'error': 'Chat context validation failed',
                'detail': 'Chat context validation failed',
                'assistant': validation_md,
                'checks_failed': checks_failed,
                'tables_found': validation.get('tables_found', []),
                'tables_missing': validation.get('tables_missing', []),
                'errors': validation.get('errors', []),
                'context_chars': context_data.get('context_chars', 0),
                'tables_expected': context_data.get('tables_expected', []),
            }
            write_chat_log(f"CHAT VALIDATION FAILED_RESPONSE {json.dumps(error_response)}")
            return JSONResponse(status_code=422, content=error_response)

        messages = [
            {
                'role': 'system',
                'content': (
                    #You are an expert NetSuite SOD analysis assistant. '
                    #Answer using ONLY the provided context. '
                    #If information is missing from the context, explicitly say so and do not invent details.'
                    """
                    You are a Senior Segregation of Duties (SoD) Auditor, Risk Analyst, Internal Controls Specialist, and Compliance Expert.

Your primary responsibility is to review SoD conflict analysis results and transform highly technical access-control findings into accurate, auditor-ready, executive-friendly, and business-readable explanations.

You are not a generic assistant. You are an expert reviewer of SoD analysis results whose purpose is to validate findings, explain their significance, identify business risks, and communicate them clearly to non-technical stakeholders.

====================================================================
CORE RESPONSIBILITIES
====================================================================

Your tasks are to:

1. Analyze the provided SoD conflict results.
2. Interpret the Ruleset(s) that triggered the conflict.
3. Explain the conflict in plain business language.
4. Describe the business process involved.
5. Explain why the combination of access creates a Segregation of Duties concern.
6. Identify the associated business risk.
7. Describe realistic risk scenarios enabled by the access combination.
8. Summarize findings for auditors, managers, compliance teams, and executives.
9. Validate findings using only the supplied context.
10. Avoid technical jargon whenever possible.

====================================================================
STRICT DATA USAGE RULES
====================================================================

You MUST follow these rules:

- Use ONLY information provided in the context.
- Never invent roles, permissions, transactions, capabilities, risks, controls, or business processes.
- Never assume a role grants permissions unless explicitly stated.
- Never infer NetSuite functionality that is not present in the provided data.
- Never create fake explanations.
- Never create fake evidence.
- Never speculate.

If information required to explain a conflict is missing, explicitly state:

"Insufficient information available in the provided context to fully explain this conflict."

If a risk scenario cannot be derived from the provided information, state:

"The provided context does not contain enough information to determine a specific risk scenario."

====================================================================
HOW TO ANALYZE A CONFLICT
====================================================================

For each conflict:

Step 1:
Identify the conflicting roles, permissions, functions, transactions, or access capabilities.

Step 2:
Identify the Ruleset or rule that triggered the conflict.

Step 3:
Determine what business activities each side of the conflict represents.

Step 4:
Explain why combining these activities violates segregation of duties principles.

Step 5:
Describe the business risk created by the access combination.

Step 6:
Generate a clear human-readable explanation.

Step 7:
Create a concise executive summary.

====================================================================
RISK INTERPRETATION GUIDELINES
====================================================================

When supported by the provided context, consider whether the conflict could enable:

- Unauthorized financial activity
- Fraud
- Concealment of fraud
- Unauthorized payments
- Fictitious vendors
- Fictitious customers
- Procurement manipulation
- Self-approval of transactions
- Journal entry manipulation
- Unauthorized adjustments
- Sensitive master data manipulation
- Revenue manipulation
- Cash handling conflicts
- Vendor management conflicts
- Customer management conflicts
- Approval workflow bypasses
- Excessive access concentration

IMPORTANT:

Only discuss risks that can reasonably be linked to the provided ruleset, conflict details, and context.

Do not mention risks unsupported by the supplied information.

====================================================================
BUSINESS LANGUAGE TRANSLATION RULES
====================================================================

Translate technical findings into language understandable by:

- Executives
- Managers
- Auditors
- Compliance teams
- Business stakeholders

Avoid unnecessary technical terminology.

Instead of:

"Role A conflicts with Role B under Rule AP-001."

Prefer:

"This user has access to both vendor-related setup activities and payment processing activities, creating a lack of independent oversight."

Always prioritize business meaning over technical wording.

====================================================================
DEDUPLICATION RULES
====================================================================

If multiple conflicts describe essentially the same risk:

- Group them together.
- Avoid repeating identical explanations.
- Produce a consolidated explanation when appropriate.
- Highlight the most significant risk first.

====================================================================
CONFIDENCE AND EVIDENCE
====================================================================

Every conclusion must be traceable to information found in the provided context.

Clearly distinguish between:

FACTS:
Information directly present in the conflict data.

INTERPRETATION:
Reasonable risk explanation derived from the provided ruleset and conflict information.

Never present interpretations as facts.

====================================================================
OUTPUT FORMAT
====================================================================

For each conflict produce:

# Conflict Summary

Rule / Ruleset:
[rule name]

Severity:
[severity if available, otherwise "Not Provided"]

Conflicting Access:
[list of conflicting roles, permissions, functions, or capabilities]

Business Area:
[procurement, accounts payable, accounts receivable, general ledger, etc. if available]

--------------------------------------------------

# Human-Readable Explanation

Provide a plain-language explanation of the conflict.

--------------------------------------------------

# Why This Matters

Explain why the access combination creates a segregation of duties concern.

--------------------------------------------------

# Business Risk

Describe the business risk supported by the provided context.

--------------------------------------------------

# Potential Risk Scenario

Describe a realistic scenario enabled by the conflicting access.

If insufficient information exists, explicitly state so.

--------------------------------------------------

# Evidence

List only the facts found in the provided context that support the analysis.

--------------------------------------------------

# Recommended Review

Suggest an appropriate access review, control review, mitigation review, or segregation assessment.

Do not recommend specific remediation actions unless supported by the context.

====================================================================
EXECUTIVE SUMMARY SECTION
====================================================================

When multiple conflicts are provided, add:

# Executive Summary

- Total conflicts analyzed.
- Highest-risk conflicts identified.
- Common themes across findings.
- Major business processes affected.
- Overall segregation-of-duties observations.

Keep this section concise and business-focused.

====================================================================
FINAL BEHAVIOR RULES
====================================================================

Be precise.
Be conservative.
Be evidence-based.
Be auditor-oriented.
Be business-friendly.
Be human-readable.

Most importantly:

Never invent information that does not exist in the provided context.
Every conclusion must be supported by the supplied conflict data and ruleset information.
                    """
                )
            },
            {
                'role': 'system',
                'content': context_data['context_text']
            }
        ]

        history_messages = payload.get('history', [])
        normalized_history = []
        if isinstance(history_messages, list):
            for history_item in history_messages:
                role = history_item.get('role')
                text = history_item.get('text')
                if text is None:
                    text = history_item.get('content')
                if role in ['user', 'assistant', 'system'] and isinstance(text, str) and text.strip():
                    if text != 'Sending your query to the backend... please wait.':
                        normalized_history.append({'role': role, 'content': text})

        messages.extend(normalized_history)
        last_history_user_text = None
        for item in reversed(normalized_history):
            if item['role'] == 'user':
                last_history_user_text = item['content'].strip()
                break
        if (last_history_user_text or '') != message.strip():
            messages.append({'role': 'user', 'content': message})

        if not any(
            msg.get('role') == 'system'
            and 'FULL_ANALYSIS_CONTEXT_START' in msg.get('content', '')
            and 'FULL_ANALYSIS_CONTEXT_END' in msg.get('content', '')
            for msg in messages
        ):
            write_chat_log('CHAT OLLAMA VALIDATION FAILED reason=Context markers missing in final payload')
            return JSONResponse(status_code=500, content={'error': 'Chat context markers are missing in payload'})

        write_chat_log(
            f"CHAT OLLAMA REQUEST messages={len(messages)} context_chars={context_data.get('context_chars', 0)}"
        )

        request_payload = {
            'model': model,
            'messages': messages,
            'temperature': 0.2,
        }

        if provider.lower() == 'ollama':
            request_body = json.dumps({
                'model': ollama_model,
                'messages': request_payload['messages'],
                'stream': False,
            }).encode('utf-8')
            ollama_endpoint = ollama_chat_endpoint if ollama_chat_endpoint.startswith('/') else f"/{ollama_chat_endpoint}"
            url = f"{ollama_base_url.rstrip('/')}:{ollama_port}{ollama_endpoint}"
            headers = {'Content-Type': 'application/json'}
        else:
            request_body = json.dumps(request_payload).encode('utf-8')
            url = f"{base_url.rstrip('/')}{chat_endpoint}"
            headers = {
                'Content-Type': 'application/json',
            }
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

        write_chat_log(f"CHAT REQUEST url={url} provider={provider} model={model} session={session.get('Company')}|{session.get('UserID')} message={message}")
        req = urllib.request.Request(url, data=request_body, headers=headers)
        context = ssl.create_default_context()
        with urllib.request.urlopen(req, context=context, timeout=300) as resp:
            response_body = json.loads(resp.read().decode('utf-8'))

        write_chat_log(f"CHAT RESPONSE status={resp.status} body={json.dumps(response_body, ensure_ascii=False)[:2000]}")

        assistant_text = ''
        if isinstance(response_body, dict):
            # Ollama native format: top-level 'message' dict
            if not assistant_text and 'message' in response_body and 'choices' not in response_body:
                ollama_msg = response_body.get('message')
                if isinstance(ollama_msg, dict):
                    raw = ollama_msg.get('content', '')
                    assistant_text = raw if isinstance(raw, str) else str(raw)
            # OpenAI format: choices[0].message.content
            if not assistant_text and 'choices' in response_body:
                choices = response_body.get('choices', [])
                if isinstance(choices, list) and choices:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict):
                        if 'message' in first_choice:
                            raw = first_choice.get('message', {}).get('content', '')
                            assistant_text = raw if isinstance(raw, str) else str(raw)
                        elif 'text' in first_choice:
                            raw = first_choice.get('text', '')
                            assistant_text = raw if isinstance(raw, str) else str(raw)
                        elif 'content' in first_choice:
                            content = first_choice.get('content', '')
                            if isinstance(content, list) and content:
                                item = content[0]
                                assistant_text = item.get('text', '') if isinstance(item, dict) else str(item)
                            elif isinstance(content, str):
                                assistant_text = content
                            else:
                                assistant_text = str(content)
            # Anthropic-style results array
            if not assistant_text and 'results' in response_body:
                results = response_body.get('results', [])
                if isinstance(results, list) and results:
                    first_result = results[0]
                    if isinstance(first_result, dict):
                        content = first_result.get('content') or first_result.get('output')
                        if isinstance(content, list) and content:
                            first_content = content[0]
                            if isinstance(first_content, dict):
                                assistant_text = first_content.get('text', '') or first_content.get('content', '')
                            else:
                                assistant_text = str(first_content)
                        elif isinstance(content, str):
                            assistant_text = content
                        elif content is not None:
                            assistant_text = str(content)
            # Generic fallbacks
            if not assistant_text:
                for key in ('text', 'detail', 'error', 'response', 'output'):
                    val = response_body.get(key, '')
                    if val and isinstance(val, str):
                        assistant_text = val
                        break
                    elif val:
                        assistant_text = str(val)
                        break

        if not assistant_text:
            assistant_text = 'The assistant returned an empty response. Verify the backend chat provider configuration.'

        assistant_text = _markdown_from_value(assistant_text)

        write_chat_log(f"CHAT PARSED assistant={assistant_text[:2000]}")
        return {'assistant': assistant_text}

    except urllib.error.HTTPError as http_err:
        try:
            error_body = http_err.read().decode('utf-8')
        except Exception:
            error_body = ''
        write_chat_log(f"CHAT HTTP ERROR code={http_err.code} reason={http_err.reason} body={error_body[:2000]}")
        assistant_md = "\n".join([
            '## Chat Provider Error',
            '',
            f"- HTTP status: {http_err.code}",
            f"- Reason: {http_err.reason}",
        ])
        return JSONResponse(status_code=500, content={
            'error': f'Chat provider error: HTTP {http_err.code}',
            'detail': f'Chat provider error: HTTP {http_err.code}',
            'assistant': assistant_md,
        })
    except (urllib.error.URLError, socket.timeout) as net_err:
        write_chat_log(f"CHAT NETWORK ERROR {type(net_err).__name__} {str(net_err)}")
        assistant_md = "\n".join([
            '## Chat Provider Timeout',
            '',
            f"- Error type: {type(net_err).__name__}",
            f"- Detail: {str(net_err)}",
        ])
        return JSONResponse(status_code=500, content={
            'error': 'Chat provider timeout',
            'detail': 'Chat provider timeout',
            'assistant': assistant_md,
        })
    except Exception as e:
        write_chat_log(f"CHAT ERROR {type(e).__name__} {str(e)}")
        assistant_md = "\n".join([
            '## Chat Endpoint Error',
            '',
            f"- Error type: {type(e).__name__}",
            f"- Detail: {str(e)}",
        ])
        return JSONResponse(status_code=500, content={
            'error': 'Chat endpoint error',
            'detail': 'Chat endpoint error',
            'assistant': assistant_md,
        })


@app.post('/chat_context_debug')
async def chat_context_debug(session: SessionData):
    context_data = build_full_ollama_context(session.Company, session.UserID, session.WebSocketID)
    return {
        'company': context_data.get('company'),
        'user_id': context_data.get('user_id'),
        'tables_expected': context_data.get('tables_expected', []),
        'tables_found': context_data.get('tables_found', []),
        'tables_missing': context_data.get('tables_missing', []),
        'excel_found': context_data.get('excel_found', False),
        'sheets_found': context_data.get('sheets_found', []),
        'context_chars': context_data.get('context_chars', 0),
        'context_preview': context_data.get('context_preview', ''),
    }


@app.post('/validate_chat_context')
async def validate_chat_context(session: SessionData):
    context_data = build_full_ollama_context(session.Company, session.UserID, session.WebSocketID)
    return validate_full_ollama_context(context_data)

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

@app.post('/is_analysis_process_running')
async def is_analysis_process_running(session: SessionData):
    current_process = None
    if session.WebSocketID:
        name = f'{session.Company}_{session.UserID}_{session.WebSocketID}_analysis_process'
    else:
        name = f'{session.Company}_{session.UserID}_analysis_process'

    for process in threading.enumerate():
        if process.name == name:
            current_process = process
            break
    if current_process and current_process.is_alive():
        return True
    return False

@app.post("/login")
async def login(credentials: UserCredentials):#SessionPlusCredData):
    logger.info('LOGIN_ROUTE payload UserID=%s user_type=%s', credentials.UserID, type(credentials).__name__)
    params = (credentials.UserID,)# credentials.Password)
    db = modules.connector.connect_db(database='sod')
    query = "SELECT * FROM users WHERE UserID = %s;"# AND Password = %s;"
    cursor = db.cursor()
    #print(query)
    cursor.execute(query, params)
    user_results = cursor.fetchone()
    #print(user_results)
    if user_results != None:
        stored_hash = user_results[1] if user_results and len(user_results) > 1 else None
        try:
            password_valid = bool(stored_hash) and check_password_hash(stored_hash, credentials.Password)
        except ValueError:
            password_valid = False
        if password_valid:
            company = user_results[3]
            await insert_logs(credentials.UserID, company, None, "Login", "Starting Session")
            #createdb = f'CREATE DATABASE IF NOT EXISTS {credentials.Company} CHARACTER SET utf8mb4;'
            await insert_logs(credentials.UserID, company, None, "Login", f"Creating {company} database if not exists")
            createdb = f'CREATE DATABASE IF NOT EXISTS {company} CHARACTER SET utf8mb4;'
            db = modules.connector.connect_db(database='')
            cursor = db.cursor()
            result = cursor.execute(createdb)
            db.commit()
            #exist = verify_table(f"SOD_Rules",credentials.Company)
            #exist = verify_table(credentials.UserID, f"SOD_Rules", company, None)
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
            #if exist == -1:
                #new_query=f"CREATE TABLE SOA.SOD_Rules AS SELECT * FROM sod.Original_SOD_Rule_Set"
            #new_query=f"CREATE OR REPLACE TABLE {company}.SOD_Rules AS SELECT * FROM sod.Original_SOD_Rule_Set" 
            #cursor.execute(new_query)
            drop_query = f"DROP TABLE IF EXISTS {company}.SOD_Rules"
            new_query = f"CREATE TABLE {company}.SOD_Rules AS SELECT * FROM sod.Original_SOD_Rule_Set"
            cursor.execute(drop_query)
            cursor.execute(new_query)
            db.commit()
            await insert_logs(credentials.UserID, company, None, "Login", f"SOD_Rules table created")
            ########################
            exist = await verify_table(credentials.UserID, f'SOD_Rules_{credentials.UserID}', company, None)
            if exist == -1:
                sod_rules_by_company = f"CREATE TABLE {company}.SOD_Rules_{credentials.UserID} AS SELECT * FROM sod.Original_SOD_Rule_Set WHERE 1=0"
                cursor.execute(sod_rules_by_company)
                db.commit()
                await insert_logs(credentials.UserID, company, None, "Login", f"SOD_Rules_{credentials.UserID} table created")
            ########################
            cursor.close()
            db.close()
            exist_logs = await verify_table(credentials.UserID, "Logs", company, None)
            if exist_logs == -1:
                create_logs_table(company)
            #exists_permissions = verify_table(f"Role_to_Permissions_{credentials.UserID}",credentials.Company)
            #exists_permissions = verify_table(credentials.UserID, f"Role_to_Permissions_{credentials.UserID}", company, None)
            #exists_Users = verify_table(f"Role_to_Users_{credentials.UserID}",credentials.Company)
            #exists_Users = verify_table(credentials.UserID, f"Role_to_Users_{credentials.UserID}", company, None)
            await insert_logs(credentials.UserID, company, None, "Login", "Session started")
            return {'UserID' : user_results[0],'UserType':user_results[2] ,'Company' : user_results[3] ,'Email': user_results[4] ,'Phone': user_results[5] ,'Active': user_results[6]  }
    return {'UserType':-1}
    

@app.post("/logout")
async def logout(session:SessionData):
    #try:
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Logout", "Colosing Session")
        isRegister = await manager.isRegister(f'{session.Company}_{session.UserID}')
        if not isRegister:
            db = modules.connector.connect_db(database=session.Company)
            for i in created_tables:
                try:
                    query = f"Drop table {i}_{session.UserID};"
                    cursor = db.cursor()
                    cursor.execute(query)
                except:
                    pass
            await insert_logs(session.UserID, session.Company, session.WebSocketID, "Logout", "Session Tables removed")
        
            clear(app, session.UserID, session.Company, session.WebSocketID)
        
            files = [
                f"{current}{separator}{session.Company}_Role_Conflicts_Details_{session.UserID}.xlsx",
                f"{current}{separator}{session.Company}_Role_Conflicts_Details_Filtered_{session.UserID}.xlsx",
                f"{current_files}{separator}{session.Company}_report_{session.UserID}.xlsx"
            ]
            for file_path in files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Logout", f"{file_path.split(separator)[-1]} file has been removed")
                    except Exception as e:
                        print(e)
                        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Logout", f"An error ocurred while trying to delete the file {file_path.split(separator)[-1]}: {e}")
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Logout", "Session Closed")
        return {"Results": 0 }
    #except Exception as e:
    #    return {'Result':-2}

async def check_status(UserID, Company, WebSocketID):
    company_tables = ["employees", "roles", "subsidiaries", "employee_global_permissions", "role_permissions", "role_subsidiaries", "employee_roles"]
    exists_tables = []
    exists_Rules = await verify_table(UserID, f"SOD_Rules", Company, WebSocketID)
    for table in company_tables:
        exists_tables.append(await verify_table(UserID, table, Company, WebSocketID))
    
    if exists_Rules == 1 and set(exists_tables) == {1}:
        with dynamic_connection(Company) as conn:
            cursor = conn.cursor()
            try:
                for table in company_tables:
                    #cursor.execute(f'CREATE OR REPLACE TABLE {table}_{UserID} AS SELECT * FROM {table}')
                    cursor.execute(f'DROP TABLE IF EXISTS {table}_{UserID}')
                    cursor.execute(f'CREATE TABLE {table}_{UserID} AS SELECT * FROM {table}')
            finally:
                cursor.close()
        await insert_logs(UserID, Company, WebSocketID, "Check Report Status", "Active")
        return {"Result" : 1}
    else:
        await insert_logs(UserID, Company, WebSocketID, "Check Report Status", "Inactive")
        return {"Result" : -1}

@app.post("/is_report_active")
async def read_items(session:SessionData):
    return await check_status(session.UserID, session.Company, session.WebSocketID)


@app.post("/upload_zip")
async def upload_zip_file(session: str = Form(...), file: UploadFile = File(...)):
    session_data = json.loads(session)
    UserID = session_data.get('UserID', '')
    Company = session_data.get('Company', '')
    WebSocketID = session_data.get('WebSocketID', None)
    filename= file.filename
    file_extension = os.path.splitext(filename)[1]
    if "zip" not in file_extension.lower():
        await insert_logs(UserID, Company, WebSocketID, "Upload zip", "Invalid file type")
        raise HTTPException(status_code=409, detail="Invalid file type")
    destination_file_path = f"{current_files}{separator}Data_{Company}_{UserID}{file_extension}"
    try:
        async with aiofiles.open(destination_file_path, 'wb') as out_file:
            while content := await file.read(1024):
                await out_file.write(content)
        await insert_logs(UserID, Company, WebSocketID, "Upload zip", f"Zip file saved successfully.")
    except Exception as e:
        await insert_logs(UserID, Company, WebSocketID, "Upload zip", f"An error occurred while saving the zip file: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while saving the zip file: {e}")
    decompressed_file, message = await decompress_file(UserID, Company, WebSocketID, destination_file_path)
    if decompressed_file is None:
        raise HTTPException(status_code=500, detail=message)
    result, message = await start_load_data(UserID, Company, WebSocketID, decompressed_file)
    if result is None:
        raise HTTPException(status_code=500, detail=message)
    result = await check_status(UserID, Company, WebSocketID)
    if result['Result'] == 1:
        output_zip = await call_role_analysis(Company, UserID, WebSocketID, option=True)
    

@app.post('/execute_analysis')
async def execute_analysis(session: SessionData):
    try:
        output_zip = await call_role_analysis(session.Company, session.UserID, session.WebSocketID)
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Login", f'First anaysis completed')
    except Exception as e:
        print(e)
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Login", f'An error occurred while executing the initial analysis: {e}')
        raise HTTPException(status_code=500, detail=f'An error occurred while executing the initial analysis: {e}')

@app.post("/get_creation_date")
async def get_creation_date(tabledata: VeriTable):
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
        await insert_logs(credentials.UserID, credentials.Company, credentials.WebSocketID, "Signup", "User already registered")
        raise HTTPException(status_code=409, detail="User already registered")
    else:
        await insert_logs(credentials.UserID, credentials.Company, credentials.WebSocketID, "Signup", "New user registered")
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
        #output_zip = f"{current}{separator}{session.Company}_Role_Conflicts_Details_{session.UserID}.xlsx"
        output_zip = f"{current_files}{separator}{session.Company}_report_{session.UserID}.xlsx"
        if not os.path.exists(output_zip):
            result = await check_status(session.UserID, session.Company, session.WebSocketID)
            if result['Result'] != 1:
                message = f"No Results for company {session.Company} were found, Have been all the files already uploaded?"
                await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results", message)
                return {"Result" : message}
            else:
                output_zip = await call_role_analysis(session.Company, session.UserID, session.WebSocketID)    
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Results", f"{output_zip.split(separator)[-1]} file returned")
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
    
'''@app.post("/upload_user")
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


'''@app.post("/get_user_html")
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
'''
'''
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
'''

'''
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get SOD html", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get single role conflicts", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get single merged role to permissions", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get single role analysis", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get single role analysis grouped by name", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "SOD count per role", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Single role analysis grouped by name sod rules", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get single role analysis grouped by SOD rule role", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "SOD list count", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get multiple role analysis", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Single role analysis grouped by name", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Multiple SOD count combined", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Multiple role analysis grouped by name SOD rule", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Multiple role analysis grouped by SOD rule role BP1", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "SOD list count multi", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Multiple role analyis grouped by SOD rule role BP2", f"An error has ocurred: {e}")
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
        endpoints = ANALYSIS_CONTEXT_TABLES
        identifier = f'get_data_{session.UserID}'
        html_tables = generate_dash_tables(app, session.Company, session.UserID, session.WebSocketID, identifier, endpoints)
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Data", "Data tables returned")
        return html_tables
    except Exception as e:
        print(e)
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Data", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get user html filtered", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get permission html filtered", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get SOD html filtered", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Filtered", "Data tables returned")
        return html_tables
    except Exception as e:
        print(e)
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Get Filtered", f"An error has ocurred: {e}")
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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Dashboard", F"An error has ocurred: {e}")
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
    print(f'[WS_ENDPOINT] Connect requested for identifier={identifier}')
    try:
        await manager.connect(websocket, identifier)
        print(f'[WS_ENDPOINT] Websocket accepted for identifier={identifier}')
        await websocket.send_text(json.dumps({
            'type': 'connected',
            'message': 'WebSocket connection established',
            'identifier': identifier,
        }))
        while True:
            data = await websocket.receive_text()
            print(f'[WS_ENDPOINT] Received from {identifier}:', data)
    except WebSocketDisconnect:
        print(f'[WS_ENDPOINT] Websocket disconnect for identifier={identifier}')
    except Exception as e:
        print(f'[WS_ENDPOINT] Websocket error for identifier={identifier}:', repr(e))
    finally:
        manager.disconnect(identifier)
        print(f'[WS_ENDPOINT] Cleaned up websocket identifier={identifier}')

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
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "Filter Table", F"An error has ocurred: {e}")
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

@app.post("/top_10_user_risk")
async def top_10_user_risk(session: SessionData):
    try:
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "top_10_user_risk", f"Loading")
        with dynamic_engine(session.Company) as engine:
            query = f'''
                SELECT CONCAT(COALESCE(`User Name`, 'Null'),'-',COALESCE(`User ID`, 'Null')) AS `User Name`, COUNT(*) AS `Total`
                FROM `user_risk_detailed_final_{session.UserID}`
                GROUP BY `User ID`, `User Name`
                ORDER BY `Total` DESC
                LIMIT 10
            '''
            df = pd.read_sql(query, engine)
            data = {
                "labels": df["User Name"].tolist(),
                "datasets":[
                    {
                        "label":"Users",
                        "data":df["Total"].tolist(),
                        "backgroundColor": "#3b4265"
                    }
                ]
            }

            options = {
                "plugins": {
                    "title": {
                        "display": False,
                        "text": 'Top 10 Users With Risk',
                        "font": {
                            "size": 16
                        }
                    },
                    "legend": {
                        "position": "bottom"
                    }
                },
                "responsive": True,
                "maintainAspectRatio": False
            }
            await insert_logs(session.UserID, session.Company, session.WebSocketID, "top_10_user_risk", f"Returned data")
            return {
                "options":options,
                "data":data
            }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/top_10_user_risk_filter")
async def top_10_user_risk_filter(session: SessionDataFilter):
    name = 'Top 10 Users With Risk'
    splited_filter = session.filter.split('-') 
    user_name = splited_filter[0]
    user_id = splited_filter[1]
    
    if user_name.lower() == 'null':
        user_name = " IS Null"
    else:
        user_name = f"='{user_name}'"
    
    if user_id.lower() == 'null':
        user_id = " IS Null"
    else:
        user_id = f"='{user_id}'"
    
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `user_risk_detailed_final_{session.UserID}`
            WHERE `User Name`{user_name} AND `User ID`{user_id}
            ORDER BY `User ID` ASC, `User Name` ASC, `Risk Name` ASC, `Company` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'top_10_user_risk_filter',
        f'{name}_{session.filter}'
    )
    return data

@app.post("/top_user_risks")
async def top_user_risks(session: SessionData):
    try:
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "top_user_risk", f"Loading")
        with dynamic_engine(session.Company) as engine:
            query = f'''
                SELECT `Risk Name`, COUNT(*) AS `Total`
                FROM `user_risk_detailed_final_{session.UserID}`
                GROUP BY `Risk Name`
                ORDER BY `Total` DESC
                LIMIT 5
            '''
            df = pd.read_sql(query, engine)
            data = {
                "labels": df["Risk Name"].tolist(),
                "datasets":[
                    {
                        "label":"Risks",
                        "data":df["Total"].tolist(),
                        "backgroundColor": "#3b4265"
                    }
                ]
            }

            options = {
                "plugins": {
                    "title": {
                        "display": False,
                        "text": 'Top User Risks',
                        "font": {
                            "size": 16
                        }
                    },
                    "legend": {
                        "position": "bottom"
                    }
                },
                "responsive": True,
                "maintainAspectRatio": False
            }
            await insert_logs(session.UserID, session.Company, session.WebSocketID, "top_user_risk", f"Returned data")
            return {
                "options":options,
                "data":data
            }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/top_user_risks_filter")
async def top_user_risks_filter(session: SessionDataFilter):
    name = 'Top User Risks'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `user_risk_detailed_final_{session.UserID}`
            WHERE `Risk Name`='{session.filter}'
            ORDER BY `User ID` ASC, `User Name` ASC, `Risk Name` ASC, `Company` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'top_user_risks_filter',
        f'{name}_{session.filter}'
    )
    return data

@app.post("/top_10_role_risk")
async def top_10_role_risk(session: SessionData):
    try:
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "top_10_role_risk", f"Loading")
        with dynamic_engine(session.Company) as engine:
            query = f'''
                SELECT `Role`, COUNT(*) AS `Total`
                FROM `Individual_Role_Risk_Detailed_{session.UserID}`
                GROUP BY `Role Id`, `Role`
                ORDER BY `Total` DESC
                LIMIT 10
            '''
            df = pd.read_sql(query, engine)
            data = {
                "labels": df["Role"].tolist(),
                "datasets":[
                    {
                        "label":"Roles",
                        "data":df["Total"].tolist(),
                        "backgroundColor": "#3b4265"
                    }
                ]
            }

            options = {
                "plugins": {
                    "title": {
                        "display": False,
                        "text": 'Top 10 Roles With Risk',
                        "font": {
                            "size": 16
                        }
                    },
                    "legend": {
                        "position": "bottom"
                    }
                },
                "responsive": True,
                "maintainAspectRatio": False
            }
            await insert_logs(session.UserID, session.Company, session.WebSocketID, "top_10_role_risk", f"Returned data")
            return {
                "options":options,
                "data":data
            }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/top_10_role_risk_filter")
async def top_10_role_risk_filter(session: SessionDataFilter):
    name = 'Top 10 Roles With Risk'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `Individual_Role_Risk_Detailed_{session.UserID}`
            WHERE `Role`='{session.filter}'
            ORDER BY `Role Id` ASC, `Role` ASC, `Risk Name` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'top_10_role_risk_filter',
        f'{name}_{session.filter}'
    )
    return data

@app.post("/high_risk_business_process")
async def high_risk_business_process(session: SessionData):
    try:
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "high_risk_business_process", f"Loading")
        with dynamic_engine(session.Company) as engine:
            query = f'''
                SELECT `Business Process`, COUNT(*) AS `Total`
                FROM `user_risk_detailed_final_{session.UserID}`
                GROUP BY `Business Process`
                ORDER BY `Total` DESC
                LIMIT 10
            '''
            df = pd.read_sql(query, engine)
            data = {
                "labels": df["Business Process"].tolist(),
                "datasets":[
                    {
                        "label":"Business Process",
                        "data":df["Total"].tolist(),
                        "backgroundColor": "#3b4265"
                    }
                ]
            }

            options = {
                "plugins": {
                    "title": {
                        "display": False,
                        "text": 'High Risk Business Process by User Count',
                        "font": {
                            "size": 16
                        }
                    },
                    "legend": {
                        "position": "bottom"
                    }
                },
                "responsive": True,
                "maintainAspectRatio": False
            }
            await insert_logs(session.UserID, session.Company, session.WebSocketID, "high_risk_business_process", f"Returned data")
            return {
                "options":options,
                "data":data
            }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/high_risk_business_process_filter")
async def high_risk_business_process_filter(session: SessionDataFilter):
    name = 'High Risk Business Process by User Count'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `user_risk_detailed_final_{session.UserID}`
            WHERE `Business Process`='{session.filter}'
            ORDER BY `User ID` ASC, `User Name` ASC, `Risk Name` ASC, `Company` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'high_risk_business_process_filter',
        f'{name}_{session.filter}'
    )
    return data

@app.post("/risk_level")
async def risk_level(session: SessionData):
    try:
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "risk_level", f"Loading")
        with dynamic_engine(session.Company) as engine:
            query = f'''
                SELECT `Risk Level`, COUNT(*) AS `Total`
                FROM `user_risk_detailed_final_{session.UserID}`
                GROUP BY `Risk Level`
                ORDER BY `Risk Level` DESC
            '''
            df = pd.read_sql(query, engine)
            data = {
                "labels": df["Risk Level"].tolist(),
                "datasets":[
                    {
                        "label":"Risk Levels",
                        "data":df["Total"].tolist()
                    }
                ]
            }

            options = {
                "plugins": {
                    "title": {
                        "display": False,
                        "text": 'User Risk by Risk Level',
                        "font": {
                            "size": 16
                        }
                    },
                    "legend": {
                        "position": "top"
                    }
                },
                "responsive": True,
                "maintainAspectRatio": False
            }
            await insert_logs(session.UserID, session.Company, session.WebSocketID, "risk_level", f"Returned data")
            return {
                "options":options,
                "data":data
            }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/risk_level_filter")
async def risk_level_filter(session: SessionDataFilter):
    name = 'User Risk by Risk Level'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `user_risk_detailed_final_{session.UserID}`
            WHERE `Risk Level`='{session.filter}'
            ORDER BY `User ID` ASC, `User Name` ASC, `Risk Name` ASC, `Company` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'risk_level_filter',
        f'{name}_{session.filter}'
    )
    return data

@app.post("/system_data")
async def system_data(session: SessionData):
    try:
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "system_data", "Loading")
        with dynamic_connection(session.Company) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f'SELECT COUNT(*) AS `Companies` FROM (SELECT COUNT(*) FROM `subsidiaries_{session.UserID}` GROUP BY `InternalId`, `Name`) AS `unique_subsidiaries`;')
                companies = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) AS `Users` FROM (SELECT COUNT(*) FROM `employees_{session.UserID}` GROUP BY `InternalId`, `Email`, `Name`) AS `unique_employess`;')
                users = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) AS `Roles` FROM (SELECT COUNT(*) FROM `roles_{session.UserID}` GROUP BY `InternalId`, `Name`) AS `unique_roles`;')
                roles = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) AS `Total` FROM `employee_global_permissions_{session.UserID}`;')
                global_permissions = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) AS `Total` FROM `role_permissions_{session.UserID}`;')
                role_permissions = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) AS `Total` FROM `employee_roles_{session.UserID}`;')
                employee_roles = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) AS `Total` FROM `role_subsidiaries_{session.UserID}`;')
                role_subsidiaries = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) AS `Total` FROM `SOD_Rules`;')
                sod_rules = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) AS `Total` FROM `SOD_Rules_{session.UserID}`;')
                personal_sod_rules = cursor.fetchone()[0]
            finally:
                cursor.close()

        await insert_logs(session.UserID, session.Company, session.WebSocketID, "system_data", "Returned data")
        return {
            "title": "System Data",
            "line1": f"{companies} Companies",
            "line2": f"{users} Users",
            "line3": f"{roles} Roles",
            "line4": f"{global_permissions} Employee Global Permissions",
            "line5": f"{role_permissions} Role Permissions",
            "line6": f"{employee_roles} Employee Roles",
            "line7": f"{role_subsidiaries} Role Subsidiaries",
            "line8": f"{sod_rules} SOD Rules",
            "line9": f"{personal_sod_rules} Personal SOD Rules"
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/system_data_filter")
async def system_data_filter(session: SessionDataFilter):
    try:
        options = [
            ('Companies', 'subsidiaries', 'Name'),
            ('Users', 'employees', 'Name'),
            ('Roles', 'roles', 'Name'),
            ('Employee Global Permissions', 'employee_global_permissions', 'Email'),
            ('Role Permissions', 'role_permissions', 'Id'),
            ('Employee Roles', 'employee_roles', 'Email'),
            ('Role Subsidiaries', 'role_subsidiaries', 'Id'),
            ('SOD Rules', 'SOD_Rules', 'RULESET NAME'),
            ('Personal SOD Rules', 'SOD_Rules', 'RULESET NAME')
        ]
        name = f"System Data - {options[int(session.filter)][0]}"
        table_name = f"{options[int(session.filter)][1]}_{session.UserID}" if options[int(session.filter)][0] != 'SOD Rules' else f"{options[int(session.filter)][1]}"
        data = await get_all_data_with_filters(
            f'''
                SELECT *
                FROM `{table_name}`
                ORDER BY `{options[int(session.filter)][2]}` ASC
            ''',
            name,
            session.Company,
            session.UserID,
            session.WebSocketID,
            'system_data_filter',
            name
        )
        return data
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/analysis_summary")
async def analysis_summary(session: SessionData):
    try:
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "analysis_summary", f"Loading")
        tables = [('Individual Role Risk Detailed', 'Individual_Role_Risk_Detailed'), ('Individual Role Risk', 'Individual_Role_Risk'), ('User Risk Detailed', 'user_risk_detailed_final'), ('User Risk', 'user_risk_final')]
        with dynamic_connection(session.Company) as conn:
            cursor = conn.cursor()
            try:
                data = {"title": "Analysis Summary"}
                for i in range(len(tables)):
                    cursor.execute(f'SELECT COUNT(*) AS `Total` FROM `{tables[i][1]}_{session.UserID}`;')
                    total = cursor.fetchone()
                    total = total[0]
                    data[f"line{i+1}"]=f"{total} {tables[i][0]}"
            finally:
                cursor.close()

            await insert_logs(session.UserID, session.Company, session.WebSocketID, "analysis_summary", f"Returned data")
            return data
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/analysis_summary_filter")
async def analysis_summary_filter(session: SessionDataFilter):
    try:
        options = [
            ('Individual Role Risk Detailed', 'Individual_Role_Risk_Detailed', 'Role Id'),
            ('Individual Role Risk', 'Individual_Role_Risk', 'Role Id'),
            ('User Risk Detailed', 'user_risk_detailed_final', 'User ID'),
            ('User Risk', 'user_risk_final', 'User Name')
        ]
        name = f"System Data - {options[int(session.filter)][0]}"
        data = await get_all_data_with_filters(
            f'''
                SELECT *
                FROM `{options[int(session.filter)][1]}_{session.UserID}`
                ORDER BY `{options[int(session.filter)][2]}` ASC
            ''',
            name,
            session.Company,
            session.UserID,
            session.WebSocketID,
            'analysis_summary_filter',
            name
        )
        return data
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

async def get_percentage(database, query1, query2, title, option, UserID, Company, WebSocketID):
    try:
        await insert_logs(UserID, Company, WebSocketID, "get_percentage", f"getting percentage")
        with dynamic_connection(database) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query1)
                value1 = cursor.fetchone()
                value1 = value1[0]
                cursor.execute(query2)
                value2 = cursor.fetchone()
                value2 = value2[0]
                percentage = round((value2 / value1) * 100, 2)
                return {
                    "title": title,
                    "line1":f"{value2} {option}",
                    "line2":f"{percentage}% of total {option.lower()}"
                }
            finally:
                cursor.close()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/users_with_risk")
async def users_with_risk(session: SessionData):
    await insert_logs(session.UserID, session.Company, session.WebSocketID, "users_with_risk", f"Loading")
    response = await get_percentage(
        session.Company,
        f'SELECT COUNT(*) AS `Users` FROM (SELECT COUNT(*) FROM `employees_{session.UserID}` GROUP BY `InternalId`, `Email`, `Name`) AS `unique_employess`;',
        f'SELECT COUNT(*) AS `Users` FROM (SELECT COUNT(*) FROM `user_risk_detailed_final_{session.UserID}` GROUP BY `User ID`, `User Name`) AS `unique_employess`;',
        'Users with Risk',
        'Users',
        session.UserID,
        session.Company,
        session.WebSocketID
    )
    await insert_logs(session.UserID, session.Company, session.WebSocketID, "users_with_risk", f"Returned data")
    return response

@app.post("/users_with_risk_filter")
async def users_with_risk_filter(session: SessionDataFilter):
    name = 'Users with Risk'
    data = await get_all_data_with_filters(
        f'''
            SELECT DISTINCT `User ID`, `User Name`
            FROM `user_risk_detailed_final_{session.UserID}`
            ORDER BY `User ID` ASC, `User Name` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'users_with_risk_filter',
        name
    )
    return data

@app.post("/roles_with_risk")
async def roles_with_risk(session: SessionData):
    await insert_logs(session.UserID, session.Company, session.WebSocketID, "roles_with_risk", f"Loading")
    response = await get_percentage(
        session.Company,
        f'SELECT COUNT(*) AS `Roles` FROM (SELECT COUNT(*) FROM `roles_{session.UserID}` GROUP BY `InternalId`, `Name`) AS `unique_roles`;',
        f'SELECT COUNT(*) AS `Roles` FROM (SELECT COUNT(*) FROM `Individual_Role_Risk_Detailed_{session.UserID}` GROUP BY `Role Id`, `Role`) AS `unique_roles`;',
        'Roles with Risk',
        'Roles',
        session.UserID,
        session.Company,
        session.WebSocketID
    )
    await insert_logs(session.UserID, session.Company, session.WebSocketID, "roles_with_risk", f"Returned data")
    return response

@app.post("/roles_with_risk_filter")
async def roles_with_risk_filter(session: SessionDataFilter):
    name = 'Roles with Risk'
    data = await get_all_data_with_filters(
        f'''
            SELECT DISTINCT `Role` AS `Role`
            FROM `Individual_Role_Risk_Detailed_{session.UserID}`
            ORDER BY `Role` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'roles_with_risk_filter',
        name
    )
    return data

@app.post("/users_with_globals")
async def users_with_globals(session: SessionData):
    await insert_logs(session.UserID, session.Company, session.WebSocketID, "users_with_globals", f"Loading")
    response = await get_percentage(
        session.Company,
        f'SELECT COUNT(*) AS `Users` FROM (SELECT COUNT(*) FROM `employees_{session.UserID}` GROUP BY `InternalId`, `Email`, `Name`) AS `unique_employess`;',
        f'SELECT COUNT(DISTINCT `Email`) AS `Users` FROM `employee_global_permissions_{session.UserID}`;',
        'Users with Globals',
        'Users',
        session.UserID,
        session.Company,
        session.WebSocketID
    )
    await insert_logs(session.UserID, session.Company, session.WebSocketID, "users_with_globals", f"Returned data")
    return response

@app.post("/users_with_globals_filter")
async def users_with_globals_filter(session: SessionDataFilter):
    name = 'Users with Globals'
    data = await get_all_data_with_filters(
        f'''
            SELECT DISTINCT `Email` AS `Email`
            FROM `employee_global_permissions_{session.UserID}`
            ORDER BY `Email` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'users_with_globals_filter',
        name
    )
    return data

@app.post("/user_risk_by_company")
async def user_risk_by_company(session: SessionData):
    try:
        await insert_logs(session.UserID, session.Company, session.WebSocketID, "users_risk_by_company", f"Loading")
        with dynamic_engine(session.Company) as engine:
            query = f'''
                SELECT `Company`, COUNT(*) AS `Total Risks`
                FROM `user_risk_detailed_final_{session.UserID}`
                GROUP BY `Company ID`, `Company`
                ORDER BY `Total Risks` DESC
            '''
            df = pd.read_sql(query, engine)
            columns = df.columns.tolist()
            data = df.to_dict('records')
            await insert_logs(session.UserID, session.Company, session.WebSocketID, "users_risk_by_company", f"Returned data")
            return {
                "title": "User Risk by Company",
                "columns": columns,
                "data": data
            }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/user_risk_by_company_filter")
async def user_risk_by_company_filter(session: SessionDataFilter):
    name = 'User Risk by Company'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `user_risk_detailed_final_{session.UserID}`
            WHERE `Company`='{session.filter}'
            ORDER BY `User ID` ASC, `User Name` ASC, `Risk Name` ASC, `Company` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'user_risk_by_company_filter',
        f'{name}_{session.filter}'
    )
    return data

def replace_nan_with_none(obj):
    if isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan_with_none(i) for i in obj]
    elif isinstance(obj, float) and np.isnan(obj):
        return None
    return obj

async def get_all_data_with_filters(query:str, title:str, company:str, UserID:str, WebSocketID:str, function_name:str, file_name:str):
    try:
        await insert_logs(UserID, company, WebSocketID, function_name, "Loading")
        with dynamic_engine(company) as engine:
            df = pd.read_sql(query, engine)
            columns = df.columns.tolist()
            data = df.to_dict('records')
            data = replace_nan_with_none(data)
            uniques={}
            for column in columns:
                values = []
                for value in df[column].sort_values().drop_duplicates():
                    if isinstance(value, float) and np.isnan(value):
                        value = None
                    values.append({"value":value})
                uniques[column]=values
            await insert_logs(UserID, company, WebSocketID, function_name, "Returned data")
            return {
                "title": title,
                "columns": columns,
                "data": data,
                "uniques":uniques,
                "fileName": file_name
            }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/individual_role_risk")
async def individual_role_risk(session: SessionData):
    name = 'Individual Role Risk'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `Individual_Role_Risk_{session.UserID}`
            ORDER BY `Role` ASC, `Business Process` ASC, `Object Label` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'individual_role_risk',
        name
    )
    return data

@app.post("/individual_role_risk_detailed")
async def individual_role_risk_detailed(session: SessionData):
    name = 'Individual Role Risk Detailed'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `Individual_Role_Risk_Detailed_{session.UserID}`
            ORDER BY `Role` ASC, `Business Process` ASC, `Object Label` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'individual_role_risk_detailed',
        name
    )
    return data

@app.post("/user_risk")
async def user_risk(session: SessionData):
    name = 'User Risk'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `user_risk_final_{session.UserID}`
            ORDER BY `User Name` ASC, `Risk Name` ASC, `Company` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'user_risk',
        name
    )
    return data

@app.post("/user_risk_detailed")
async def user_risk_detailed(session: SessionData):
    name = 'User Risk Detailed'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `user_risk_detailed_final_{session.UserID}`
            ORDER BY `User ID` ASC, `User Name` ASC, `Risk Name` ASC, `Company` ASC, `Security Object` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'user_risk_detailed',
        name
    )
    return data

@app.post("/employees")
async def get_employees(session: SessionData):
    name = 'Employees'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `employees_{session.UserID}`
            ORDER BY `Name` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'get_employees',
        name.lower()
    )
    return data

@app.post("/roles")
async def get_roles(session: SessionData):
    name = 'Roles'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `roles_{session.UserID}`
            ORDER BY `Name` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'get_roles',
        name.lower()
    )
    return data

@app.post("/subsidiaries")
async def get_subsidiaries(session: SessionData):
    name = 'Subsidiaries'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `subsidiaries_{session.UserID}`
            ORDER BY `Name` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'get_subsidiaries',
        name.lower()
    )
    return data

@app.post("/global_permissions")
async def get_global_permissions(session: SessionData):
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `employee_global_permissions_{session.UserID}`
            ORDER BY `Email` ASC
        ''',
        'Global Permissions',
        session.Company,
        session.UserID,
        session.WebSocketID,
        'get_global_permissions',
        'employee_global_permissions'
    )
    return data

@app.post("/employee_roles")
async def get_employee_roles(session: SessionData):
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `employee_roles_{session.UserID}`
            ORDER BY `Email` ASC
        ''',
        'Employee Roles',
        session.Company,
        session.UserID,
        session.WebSocketID,
        'get_employee_roles',
        'employee_roles'
    )
    return data
    
@app.post("/role_permissions")
async def get_role_permissions(session: SessionData):
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `role_permissions_{session.UserID}`
            ORDER BY `Id` ASC
        ''',
        'Role Permissions',
        session.Company,
        session.UserID,
        session.WebSocketID,
        'get_role_permissions',
        'role_permissions'
    )
    return data

@app.post("/role_subsidiaries")
async def get_role_subsidiaries(session: SessionData):
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `role_subsidiaries_{session.UserID}`
            ORDER BY `Id` ASC
        ''',
        'Role Subsidiaries',
        session.Company,
        session.UserID,
        session.WebSocketID,
        'get_role_subsidiaries',
        'role_subsidiaries'
    )
    return data

#################### SOD Rules #####################

@app.post("/SOD_RuleSet")
async def get_SOD_RuleSet(session: SessionData):
    name = 'SOD RuleSet'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `SOD_Rules`
            ORDER BY `Risk Id` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'get_SOD_RuleSet',
        name
    )
    return data

@app.post("/personal_SOD_RuleSet")
async def get_personal_SOD_RuleSet(session: SessionData):
    name = 'Personal SOD RuleSet'
    data = await get_all_data_with_filters(
        f'''
            SELECT *
            FROM `SOD_Rules_{session.UserID}`
            ORDER BY `Risk Id` ASC
        ''',
        name,
        session.Company,
        session.UserID,
        session.WebSocketID,
        'get_personal_SOD_RuleSet',
        name
    )
    return data

@app.put("/change_SOD_Rule_status")
async def change_SOD_Rule_status(session: UpdateSODRuleSet):
    try:
        SODRule = session.SODRule
        table_name = 'SOD_Rules'
        if SODRule.TableType:
            table_name = f'{table_name}_{session.UserID}'
        with dynamic_connection(session.Company) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"UPDATE {table_name} SET `ENABLED`=%s WHERE `Risk Id`=%s AND `SECURITY OBJECT LABEL`=%s", (SODRule.Enabled, SODRule.RiskId, SODRule.SecurityObjectLabel))
                conn.commit()
            finally:
                cursor.close()
        if SODRule.Enabled == 1 or SODRule.Enabled == 0:
            if SODRule.Enabled == 1:
                action='Enabled'
            elif SODRule.Enabled == 0:
                action='Disabled'
            await insert_logs(session.UserID, session.Company, session.WebSocketID, 'change_SOD_Rule_status', f"The SOD rule with 'Risk Id': {SODRule.RiskId} and 'SECURITY OBJECT LABEL': {SODRule.SecurityObjectLabel} from the table {table_name} has been {action}")
    except Exception as e:
        print(e)
        await insert_logs(session.UserID, session.Company, session.WebSocketID, 'change_SOD_Rule_status', f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/remove_all_personal_SOD_RuleSet")
async def remove_all_personal_SOD_RuleSet(session: SessionData):
    try:
        with dynamic_connection(session.Company) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"TRUNCATE TABLE SOD_Rules_{session.UserID}")
                conn.commit()
            finally:
                cursor.close()
        await insert_logs(session.UserID, session.Company, session.WebSocketID, 'remove_all_personal_SOD_RuleSet', "All personal SOD Rules have been remove")
    except Exception as e:
        print(e)
        await insert_logs(session.UserID, session.Company, session.WebSocketID, 'remove_all_personal_SOD_RuleSet', f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/remove_selected_SOD_rules")
async def remove_selected_SOD_rules(session: RemoveSODRules):
    try:
        SODRules = session.SODRules
        with dynamic_connection(session.Company) as conn:
            try:
                cursor = conn.cursor()
                try:
                    for SODRule in SODRules:
                        cursor.execute(f"DELETE FROM SOD_Rules_{session.UserID} WHERE `Risk Id`=%s AND `SECURITY OBJECT LABEL`=%s", (SODRule.RiskId, SODRule.SecurityObjectLabel))
                    conn.commit()
                    await insert_logs(session.UserID, session.Company, session.WebSocketID, 'remove_selected_SOD_rules', "Selected SOD Rules have been removed")
                finally:
                    cursor.close()
            except Exception as e:
                print(e)
                await insert_logs(session.UserID, session.Company, session.WebSocketID, 'remove_selected_SOD_rules', f"An error occurred while removing selected SOD Rules: {e}. Rolling back.")
                conn.rollback()
    except Exception as e:
        print(e)
        await insert_logs(session.UserID, session.Company, session.WebSocketID, 'remove_selected_SOD_rules', f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print(f"################################# THIS IS THE PID {os.getpid()} ##################################################" )
    uvicorn.run("API:app", host="0.0.0.0",  port=5678, reload=False)#, ssl_keyfile="/storage/certs/privkey.pem", ssl_certfile="/storage/certs/fullchain.pem")

