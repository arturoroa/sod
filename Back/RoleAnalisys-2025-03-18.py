import os
import pathlib
import json
import openpyxl
import pandas as pd
from openpyxl.styles import Font
from pretty_html_table import build_table
import re
import numpy as np
import ollama
import requests
import sqlite3
from fpdf import FPDF
import zipfile
import sys
from datetime import datetime
from Models_and_engine import insert_logs



current = pathlib.Path(".").parent.absolute()

separator =''

if sys.platform.startswith('win'):
    separator = '\\'
else:
    separator='/'

ip='localhost'
port=11434
ollama_url = f"http://{ip}:{port}/api/generate"

def Role_analysis(Type_of_Run, DB, R_User, R_Permission, SOD, TMP, DRS, output_path, output_pdf, output_zip, company, User, WebSocketID):
    insert_logs(User, company, WebSocketID,  'Role Analysis', 'Role Analysis process started')
    #TMP=TMP.split('.')[0]
    DRS=DRS.split('.')[0]
    current = pathlib.Path(".").parent.absolute()
    #DB= f"{current}\\Data\\SOD.db"
    
    #pdf = FPDF()
    #pdf.add_page()
    #pdf.set_font("Arial", size=12)
    #pdf.set_auto_page_break(auto=True, margin=15)
    
    
    #engine = create_engine(SQLALCHEMY_DATABASE_URL)
    #SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    #Base = declarative_base()
    #db = SessionLocal()
    ##Files to load
    nSOD=SOD
    nSOD=f'{nSOD}new.xlsx'
    insert_logs(User, company, WebSocketID,  'Role Analysis', f'Reading {SOD} table')
    df=pd.read_sql(SOD,DB)
    df.columns = df.columns.str.title()
    #df=pd.read_sql(TMP,DB)
    df = df[df['Risk Type'] == 'Segregation of Duties']
    #df[['Business Process 1', 'Business Process 2']] = df['Name'].str.split('&', expand=True)
    df[['Business Process 1', 'Business Process 2']] = df['Name'].str.split(r'&|and', expand=True)
    #df.drop('Name', axis=1, inplace=True)
    counts = df['Risk Id'].value_counts()
    #print(counts)
    unique_df = df[df['Risk Id'].isin(counts[counts == 1].index)]
    #print(unique_df)
    list_a = unique_df['Security Object Name'].tolist()
    #print(list_a)
    mask_bp1 = df['Business Process 1'].str.strip() == df['Business Process'].str.strip()
    mask_bp2 = df['Business Process 2'].str.strip() == df['Business Process'].str.strip()

    #df.loc[mask_bp1, 'Business Process 1'] = df.loc[mask_bp1, 'Security Object Label'].str.strip()
    #df.loc[mask_bp2, 'Business Process 2'] = df.loc[mask_bp2, 'Security Object Label'].str.strip()
    df.loc[mask_bp1, 'Permission 1'] = df.loc[mask_bp1, 'Security Object Label'].str.strip()
    df.loc[mask_bp2, 'Permission 2'] = df.loc[mask_bp2, 'Security Object Label'].str.strip()
    #print(df)
    df['Permission 1'] = df['Permission 1'].fillna(df['Business Process 1'])
    df['Permission 2'] = df['Permission 2'].fillna(df['Business Process 2'])
    df.to_excel(nSOD,index=False)
    insert_logs(User, company, WebSocketID,  'Role Analysis', f'{nSOD} file created')
    #TMP=f"{current}{separator}{SOD}temp.xlsx"
    df.to_excel(TMP,index=False)
    insert_logs(User, company, WebSocketID,  'Role Analysis', f'{TMP} file created')

    #new_df = df[['Business Cycle','Name', 'Description', 'Business Process 1','Business Process 2','Risk Id','Risk Level','Business Process','Business Cycle']]
    new_df = df[['Business Cycle','Name', 'Description', 'Business Process 1','Business Process 2','Permission 1','Permission 2','Risk Id','Risk Level','Business Process']]    
    new_df=new_df.rename(columns={'Description': 'Conflict Details'})
    new_df=new_df.rename(columns={'Name': 'SOD Rule'})
    new_df.drop_duplicates(inplace=True)

    #new_df.to_excel(nSOD,index=False)

    #load files
    insert_logs(User, company, WebSocketID,  'Role Analysis', f'Reading {R_User} table')
    df_role_to_users = pd.read_sql(R_User, DB)
    df_role_to_permissions = pd.read_sql(R_Permission, DB).query("Level not in ['View', None,'',' ','None','NaN']")
    
    if df_role_to_users.empty:
        return None, 0
    if df_role_to_permissions.empty:
        return None, 1

    df_role_to_permissions =df_role_to_permissions.dropna(subset=['Level'])
    #print(df_role_to_permissions.iloc[[53]])
    #print(df_role_to_permissions.iloc[[54]])
    #print(df_role_to_permissions.iloc[[55]])
    
    df_sod = new_df#pd.read_excel(nSOD, sheet_name=0, engine='openpyxl')            
    df_role_to_permissions.to_excel(f'{current}{separator}role_to_permissions_used_{company}.xlsx',index=False)
    insert_logs(User, company, WebSocketID,  'Role Analysis', f'role_to_permissions_used_{company}.xlsx file created')
    df_no_sod = df_role_to_permissions.query("Level  in ['View', 'None','',' ','NaN',None]")
    
    single_role_results = []
    multiple_role_results = []

    #Get all the roles (uniques)
    roles = df_role_to_permissions['Role'].unique()
    permissions={}
    levels={}      

    #for each role, get the perimission list
    for role in roles:
            #permissions[role] = df_role_to_permissions[df_role_to_permissions['Role'] == role]['Permission'].unique()
            permissions[role] = df_role_to_permissions[df_role_to_permissions['Role'] == role][['Permission', 'Level']]
    conflict={}
    count=0

    ###the conflict are declared in pairs
    for index,row in df_sod.iterrows():
        sublevel_permission1 = str(row['Permission 1']).strip()
        sublevel_permission2 = str(row['Permission 2']).strip()
        permission1 = str(row['Business Process 1']).strip()
        permission2 = str(row['Business Process 2']).strip()
        details=str(row['Conflict Details']).strip()
        RID=str(row['Risk Id']).strip()
        RLevel=str(row['Risk Level']).strip()
        Name = str(row['SOD Rule']).strip()
        Business_Process=str(row['Business Process']).strip()
        Business_Cycle=str(row['Business Cycle']).strip()
        for role in permissions.keys():
            permission_list= permissions[role]['Permission'].tolist()
            if role == "Cytek - Accountant":
                pass
                #print(permissions[role]['Permission'].tolist())
                #print(permission1,permission2,sublevel_permission1,sublevel_permission2)
                #if (sublevel_permission1 and sublevel_permission2 ) in permissions[role]['Permission'].tolist():
                #    print(f"Conflict detected\n\n")
            
            if ( sublevel_permission1 in permission_list and sublevel_permission2  in permission_list) or (sublevel_permission1 in list_a or sublevel_permission2 in list_a):
                conflict.update( {count : {'Role':role, 'Bussiness Process 1' : permission1, 'Businnes Process 2' : permission2,'Permission 1' : sublevel_permission1,'Permission 2': sublevel_permission2,'Conflict Details' : details,"Risk ID" : RID,'Risk Level':RLevel,'Name':Name,'Business Process':Business_Process,'Business Cycle':Business_Cycle}})
                count+=1
            #print("\n")
                    
            
    data_list = list(conflict.values())
    df = pd.DataFrame(data_list)
    if df.empty:
        return None, 3
    merged_df = pd.merge(df_role_to_users, df, on="Role", how="inner").drop_duplicates()
    tab1 = df.copy()
    #tab1 = df.drop(['Permission 1', 'Permission 2'], axis=1)
    #tab1_column = tab1.pop('Business Process')
    #tab1.insert(5, 'Business Process', tab1_column)
    #tab1.rename(columns={'Business Process': 'Permission', 'Name': 'SOD Rule'}, inplace=True)
    tab1.rename(columns={'Name': 'SOD Rule'}, inplace=True)
    insert_logs(User, company, WebSocketID,  'Role Analysis', f'Creating file: {output_path.split(separator)[-1]}')
    with pd.ExcelWriter(output_path) as writer:
        tab1 = tab1.sort_values(by='Role')
        tab1.to_excel(writer, sheet_name='Role Level Conflicts Detailed', index=False)
        insert_logs(User, company, WebSocketID,  'Role Analysis', f'Role Level Conflicts sheet added')
        try:
            tab1.to_sql(f'Role_Level_Conflicts_Detailed_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Role_Level_Conflicts_Detailed_{User} table created')
        except Exception as e:
            pass
        tab1_simplified = tab1.drop_duplicates(subset=['Role', 'Bussiness Process 1', 'Businnes Process 2', 'Conflict Details'])
        #tab1_simplified = tab1_simplified.drop(['Permission'], axis=1)
        tab1_simplified.to_excel(writer, sheet_name='Role Level Conflicts Simplified', index=False)
        insert_logs(User, company, WebSocketID,  'Role Analysis', f'Role Level Conflicts Simplified sheet added')
        try:
            tab1_simplified.to_sql(f'Role_Level_Conflicts_Simplified_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Role_Level_Conflicts_Simplified_{User} table created')
        except:
            pass
        try:
            df.to_sql(f'Role_Level_Conflicts_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Role_Level_Conflicts_{User} table created')
        except:
            pass
        try:
            df.to_sql(f'Role_Level_Conflicts_Filtered_{User}', DB, if_exists='replace', index=False)  
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Role_Level_Conflicts_Filtered_{User} table created')
        except:
            pass
        ollama_df = df[['Role', 'Conflict Details','Name','Permission 1','Permission 2']]
        question = f'''Given the dataframe Below, provide the summary.
        Identify the patterns, trends or features related to the conflicts.
        Column 'Permission 1' and 'Column Permission 2' creates a conflict  detailed in Column 'Conflict Details'.
        Identify conflicts that are succeptable to commit fraud.
        Identify the permission given a role that are strange. i.e. An HR role should'nt have purchases permission. 
        \n Dataframe : \n{ollama_df}.''' 
        data = {"model": "llama3","prompt": question,"stream": False}
        insert_logs(User, company, WebSocketID,  'Role Analysis', f'Querying the AI Model')
        response = requests.post(ollama_url, json=data)
        try:
            response=response.json()
        except Exception as e:
            response={'response':'Loading Error'}
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'An error occurred while Querying the AI Model: {e}')
            print(e)
        
        #pdf.multi_cell(0, 10, txt=f"{response['response']}", align='C')
        #pdf.output(output_pdf)
        #print(response['response'])
        df_unique = merged_df.drop_duplicates(subset=['Name_x', 'Role'])
        df_unique = df_unique.rename(columns={'Name_x': 'Name'})
        df_unique = df_unique.rename(columns={'Name_y': 'SOD Rule'})
        client_data_simplified = df_unique[['Name', 'Email', 'Phone', 'Conflict Details', 'SOD Rule']]
        #df_unique.to_excel(writer, sheet_name='User Conflicts By Role', index=False)
        try:
            client_data_simplified.to_sql(f'Client_Data_Simplified_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Client_Data_Simplified_{User} table created')
        except Exception as e:
            pass

        start_row = 1
        df_single_role=df_unique
        try:
            df_single_role.to_sql(f'Single_Role_Conflicts_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Single_Role_Conflicts_{User} table created')
        except:
            pass
        try:
            df_single_role.to_sql(f'Single_Role_Conflicts_Filtered_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Single_Role_Conflicts_Filtered_{User} table created')
        except:
            pass

        bold_font = Font(bold=True, size=14)        
        pivot1 = pd.pivot_table(df_single_role, index='Role', columns='Name', values='SOD Rule', aggfunc='count').fillna(0)
        #pivot1.to_excel(writer, sheet_name='Role Conflict Matrix', startrow=start_row)
        try:
            pivot1.to_sql(f'Single_Role_Analysis_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Single_Role_Analysis_{User} table created')
        except:
            pass

        start_row = 1#len(pivot1) + 3
        pivot2 = df_single_role.groupby(['Name', 'Role'])['SOD Rule'].count().unstack().fillna(0)
        #pivot2.to_excel(writer, sheet_name='Name Level Matrix', startrow=start_row)
        try:
            pivot2.to_sql(f'Single_Role_Analysis_Grouped_by_Name_{User}', DB, if_exists='replace', index=False, chunksize=10, method='multi')
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Single_Role_Analysis_Grouped_by_Name_{User} table created')
        except:
            pass

        start_row = 1#len(pivot2) + 3
        sod_count_per_role = df_single_role.groupby('Role')['SOD Rule'].nunique().reset_index()
        #sod_count_per_role.to_excel(writer, sheet_name='User Level Matrix', startrow=start_row, index=False)
        try:
            sod_count_per_role.to_sql(f'SOD_Count_Per_Role_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'SOD_Count_Per_Role_{User} table created')
        except:
            pass

        pivot3 = df_single_role.groupby(['Name', 'SOD Rule']).size().unstack().fillna(0)
        #pivot3.to_excel(writer, sheet_name='Name Level Matrix', startrow=start_row)
        try:
            pivot3.to_sql(f'Single_Role_Analysis_Grouped_by_Name_SOD_Rule_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Single_Role_Analysis_Grouped_by_Name_SOD_Rule_{User} table created')
        except:
            pass

        start_row = 1# len(pivot3) + 15
        pivot4 = df_single_role.groupby(['SOD Rule', 'Role']).size().unstack().fillna(0)
        #pivot4.to_excel(writer, sheet_name='SOD Level Matrix', startrow=start_row)
        try:
            pivot4.to_sql(f'Single_Role_Analysis_Grouped_by_SOD_Rule_Role_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Single_Role_Analysis_Grouped_by_SOD_Rule_Role_{User} table created')
        except:
            pass

        #merged_df.to_excel(writer, sheet_name='User Level Conflicts', index=False)
        df_multiple_role=merged_df
        df_multiple_role.rename(columns={'Name_x': 'Name', 'Name_y': 'SOD Rule'}, inplace=True)
        df_multiple_role.to_excel(writer, sheet_name='Client Data', index=False)
        insert_logs(User, company, WebSocketID,  'Role Analysis', f'Client Data sheet added')
        #df_multiple_role.to_excel(writer, sheet_name='User Level Conflicts', index=False)
        client_data_simplified.to_excel(writer, sheet_name='Client Data Simplified', index=False)
        insert_logs(User, company, WebSocketID,  'Role Analysis', f'Client Data Simpified sheet added')
        try:
            merged_df.to_sql(f'Merged_Users_to_Permissions_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Merged_Users_to_Permissions_{User} table created')
        except:
            pass
        try:
            merged_df.to_sql(f'Merged_Users_to_Permissions_Filtered_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Merged_Users_to_Permissions_Filtered_{User} table created')
        except:
            pass
        
        start_row += len(pivot4) + 15
        tab3_start_row = 0
        tab3_sheet_name = 'Total SOD Rules with Conflicts'
        sod_list_count = df_single_role['SOD Rule'].value_counts().reset_index()
        sod_list_count.columns = ['SOD Rule', 'Count']
        sod_list_count.to_excel(writer, sheet_name=tab3_sheet_name, startrow=tab3_start_row, index=False)
        #sod_list_count.to_excel(writer, sheet_name='SOD Level Matrix', startrow=start_row, index=False)  
        try:
            sod_list_count.to_sql(f'SOD_List_Count_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'SOD_List_Count_{User} table created')
        except:
            pass
        

        start_row = 1
        pivot1 = pd.pivot_table(df_multiple_role, index='Role', columns='Name', values='SOD Rule',
                                        aggfunc='count').fillna(0)
        #pivot1.to_excel(writer, sheet_name='Permission by Role Level Matrix', startrow=start_row)
        try:
            pivot1.to_sql(f'Multiple_Role_Analysis_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Multiple_Role_Analysis_{User} table created')
        except:
            pass

        start_row += len(pivot1) + 3
        pivot2 = df_multiple_role.groupby(['Name', 'Role'])['SOD Rule'].count().unstack().fillna(0)
        #pivot2.to_excel(writer, sheet_name='Permission by Role Level Matrix', startrow=start_row)
        try:
            pivot2.to_sql(f'Multiple_Role_Analysis_Grouped_by_Name_{User}', DB, if_exists='replace', index=False, chunksize=200, method='multi')
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Multiple_Role_Analysis_Grouped_by_Name_{User} table created')
        except:
            pass
        start_row += len(pivot2) + 3
        tab3_start_row += len(sod_list_count) + 3
        sod_count_combined = df_multiple_role.groupby('Role')['SOD Rule'].nunique().reset_index()
        #sod_count_combined.to_excel(writer, sheet_name='Permission by Role Level Matrix', startrow=start_row, index=False)
        sod_count_combined.to_excel(writer, sheet_name=tab3_sheet_name, startrow=tab3_start_row, index=False)
        try:
            sod_count_combined.to_sql(f'Multiple_SOD_Count_Combined_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Multiple_SOD_Count_Combined_{User} table created')
        except:
            pass
        
        start_row = 1# len(sod_count_combined) + 3
        pivot3 = df_multiple_role.groupby(['Name', 'SOD Rule']).size().unstack().fillna(0)
        #pivot3.to_excel(writer, sheet_name='Name by permission Level Matrix', startrow=start_row)
        try:
            pivot3.to_sql(f'Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Multiple_Role_Analysis_Grouped_by_Name_SOD_Rule_{User} table created')
        except:
            pass

        start_row = 1#len(pivot3) + 3
        # Pivot: SOD Rules x Role BP1
        pivot4 = df_multiple_role.groupby(['SOD Rule', 'Permission 1']).size().unstack().fillna(0)
        #pivot4.to_excel(writer, sheet_name='SOD By Permission Level Matrix', startrow=start_row)
        try:
            pivot4.to_sql(f'Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP1_{User} table created')
        except:
            pass
        start_row += len(pivot4) + 3

        # Pivot: SOD Rules x Role BP2
        pivot5 = df_multiple_role.groupby(['SOD Rule', 'Permission 2']).size().unstack().fillna(0)
        #pivot5.to_excel(writer, sheet_name='SOD By Permission Level Matrix', startrow=start_row)
        try:
            pivot5.to_sql(f'Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'Multiple_Role_Analysis_Grouped_by_SOD_Rule_Role_BP2_{User} table created')
        except:
            pass

        start_row += len(pivot5) + 3
        tab3_start_row += len(sod_count_combined) + 3
        # List of SOD rules and the count for multiple roles
        sod_list_count_multi = df_multiple_role['SOD Rule'].value_counts().reset_index()
        sod_list_count_multi.columns = ['SOD Rule', 'Count']
        #sod_list_count_multi.to_excel(writer, sheet_name='SOD By Permission Level Matrix', startrow=start_row, index=False)
        sod_list_count_multi.to_excel(writer, sheet_name=tab3_sheet_name, startrow=tab3_start_row, index=False)
        try:
            sod_list_count_multi.to_sql(f'SOD_List_Count_Multi_{User}', DB, if_exists='replace', index=False)
            insert_logs(User, company, WebSocketID,  'Role Analysis', f'SOD_List_Count_Multi_{User} table created')
        except:
            pass

        try:
            tab3_start_row += len(sod_list_count_multi) + 3
            count_conflicts_by_permissions = merged_df.groupby(['Permission 1', 'Permission 2', 'Conflict Details']).size().reset_index(name='Count')
            count_conflicts_by_permissions.to_excel(writer, sheet_name=tab3_sheet_name, startrow=tab3_start_row,  index=False)
        except Exception as e:
            print(e)

        insert_logs(User, company, WebSocketID,  'Role Analysis', f'{tab3_sheet_name} added')

        tab4 = [
            ["Excution Time", None, f'{datetime.now()}'],
            [None, None, None],
            ["Description", None, None],
            [None, None, None],
        ]
        test_description = response['response']
        for line in test_description.splitlines():
            tab4.append([line, None, None])
        tab4_df = pd.DataFrame(tab4)
        tab4_df.to_excel(writer, sheet_name='Report Run Information', index=False, header=False)
        insert_logs(User, company, WebSocketID,  'Role Analysis', f'Report Run Information added')

    #insert_logs(User, company, WebSocketID,  'Role Analysis', f'Compressing {output_zip.split(separator)[-1]} file')

    #with zipfile.ZipFile(output_zip, 'w') as zip_object:
        # Add the files to the ZIP archive
        #print(output_path.split('\\I')[1])
    #    sod_file=output_path.split(separator)[-1]
        #pdf_file=output_pdf.split(f'{separator}E')[1]
    #    zip_object.write(output_path, sod_file)
        #zip_object.write(output_pdf,f"E{pdf_file}")
    insert_logs(User, company, WebSocketID,  'Role Analysis', f'{output_path.split(separator)[-1]} file returned')
    return df, output_path
