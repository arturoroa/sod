from zipfile import ZipFile
import pandas as pd
import sys
import os
from Models_and_engine import dynamic_engine, insert_logs
import shutil
from sqlalchemy import text

async def decompress_file(UserID, Company, WebSocketID, path:str, pwd=None):
    try:
        await insert_logs(UserID, Company, None, "decompress_file", "Unzipping zip file.")
        new_path = os.path.splitext(path)[0]
        with ZipFile(path) as zip_file:
            zip_file.extractall(new_path, pwd=pwd)
        await insert_logs(UserID, Company, WebSocketID, "decompress_file", "File successfully unzipped.")
        return new_path, None
    except Exception as e:
        print(e)
        message = f"An error occurred while unzipping the file: {e}"
        await insert_logs(UserID, Company, WebSocketID, "decompress_file", message)
        return None, message

async def drop_table_if_exists(UserID, Company, WebSocketID, engine, table_name):
    try:
        with engine.connect() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
        await insert_logs(UserID, Company, WebSocketID, "drop_table_if_exists", f"Dropped table '{table_name}' if it existed")
    except Exception as e:
        print(e)
        await insert_logs(UserID, Company, WebSocketID, "drop_table_if_exists", f"An error occurred while deleting the table {table_name}: {e}")

async def process_file(UserID, Company, WebSocketID, file_path, engine, filetype):
    #try:
    # Read CSV file
    message = ''
    if filetype == 'csv':
        df = pd.read_csv(file_path)
        message = 'CSV file'
    else:
        df = pd.read_excel(file_path)
        message = 'xlsx file'
    await insert_logs(UserID, Company, WebSocketID, "process_file", f"{message} '{file_path}' read successfully")
    
    # Get table name from file name (without extension)
    table_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Drop the table if it exists
    await drop_table_if_exists(UserID, Company, WebSocketID, engine, table_name)
    
    # Write to SQL database
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    await insert_logs(UserID, Company, WebSocketID, "process_file", f"Data from '{file_path}' inserted into table '{table_name}' successfully")
    #except Exception as e:
    #    print(e)
    #    insert_logs(UserID, Company, WebSocketID, "drop_table_if_exists", f"An error occurred: {e}")


async def start_load_data(UserID, Company, WebSocketID, folder_path):
    try:
        required_files = [
            ("employees.csv", "employees.xlsx"),
            ("roles.csv", "roles.xlsx"),
            ("subsidiaries.csv", "subsidiaries.xlsx"),
            ("employee_global_permissions.csv", "employee_global_permissions.xlsx"),
            ("role_permissions.csv", "role_permissions.xlsx"),
            ("role_subsidiaries.csv", "role_subsidiaries.xlsx"),
            ("employee_roles.csv", "employee_roles.xlsx")
        ]

        missing_files = []
        for file in required_files:
            if not os.path.exists(os.path.join(folder_path, file[0])) and not os.path.exists(os.path.join(folder_path, file[1])):
                await insert_logs(UserID, Company, WebSocketID, "start_load_data", f"File {file[0]} or {file[1]} not found")
                missing_files.append(file)
        message = ''
        if len(missing_files)>0:
            for file in missing_files:
                message += f"{file[0]}/{file[1]}\n"
            message = message[:-1]
            return None, f"The following files were not found and are required:\n{message}"

        with dynamic_engine(Company) as engine:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if filename.endswith('.csv'):
                    await process_file(UserID, Company, WebSocketID, file_path, engine,"csv")
                if filename.endswith('.xlsx'):
                    await process_file(UserID, Company, WebSocketID, file_path, engine,"xlsx")
        await insert_logs(UserID, Company, WebSocketID, "start_load_data", "All data was loaded successfully")
        return True, None
    except Exception as e:
        await insert_logs(UserID, Company, WebSocketID, "start_load_data", f"An error occurred: {e}")
        return None, f"An error occurred: {e}"
    finally:
        try:
            os.remove(f"{folder_path}.zip")
        except:
            pass
        try:
            shutil.rmtree(folder_path)
        except:
            pass
            
