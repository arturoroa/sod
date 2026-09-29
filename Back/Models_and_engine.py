from WebSocketManagerConnection import manager
from contextlib import contextmanager
from sqlalchemy import create_engine
from pydantic import BaseModel
from datetime import datetime
import modules.connector
import asyncio
from typing import List
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env', override=True)

@contextmanager
def dynamic_engine(database:str):
    engine = create_engine(
        f"mysql+mysqlconnector://{os.getenv('DB_USER', 'dbuser')}:{os.getenv('DB_PASSWORD', 'roandai.1')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{database}",
        echo=False,
    )
    try:
        yield engine
    finally:
        engine.dispose()

@contextmanager
def dynamic_connection(database:str):
    conn = modules.connector.connect_db(database=database)
    try:
        yield conn
    finally:
        conn.close()

async def insert_logs(user_id, company, WebSocketID, process, action):
    try:
        date_time = datetime.now()
        with dynamic_connection(company) as conn:
            cursor = conn.cursor()
            try:
                query = "INSERT INTO Logs VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (user_id, process, action, f'{date_time}'))
                conn.commit()
            finally:
                cursor.close()
        if WebSocketID is not None:
            payload = {
                'type': 'ws_log',
                'process': process,
                'action': action,
                'timestamp': date_time.isoformat(),
                'company': company,
                'user_id': user_id,
                'websocket_id': WebSocketID,
                'source': 'backend',
            }
            try:
                await manager.send_personal_message(payload, f'{company}_{user_id}_{WebSocketID}')
            except:
                pass
    except Exception as e:
        print(f'Insert Logs Error: {e}')

def insert_logs_dash(user_id, company, WebSocketID, process, action, flag=True):
    try:
        date_time = datetime.now()
        with dynamic_connection(company) as conn:
            cursor = conn.cursor()
            try:
                query = "INSERT INTO Logs VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (user_id, process, action, f'{date_time}'))
                conn.commit()
            finally:
                cursor.close()
        if WebSocketID is not None:
            payload = {
                'type': 'ws_log',
                'process': process,
                'action': action,
                'timestamp': date_time.isoformat(),
                'company': company,
                'user_id': user_id,
                'websocket_id': WebSocketID,
                'source': 'backend',
            }
            if flag:
                try:
                    asyncio.create_task(manager.send_personal_message(payload, f'{company}_{user_id}_{WebSocketID}'))
                except:
                    pass
            else:
                try:
                    asyncio.run(manager.send_personal_message(payload, f'{company}_{user_id}_{WebSocketID}'))
                except:
                    try:
                        asyncio.create_task(manager.send_personal_message(payload, f'{company}_{user_id}_{WebSocketID}'))
                    except:
                        pass
    except Exception as e:
        print(f'Insert Logs Error: {e}')


def create_logs_table(company):
    try:
        with dynamic_connection(company) as conn:
            cursor = conn.cursor()
            try:
                logs_query = f'''CREATE TABLE {company}.Logs(
                    UserID VARCHAR(50) NOT NULL,
                    Process VARCHAR(255) NOT NULL,
                    Action TEXT NOT NULL,
                    ActionDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
                );'''
                cursor.execute(logs_query)
                conn.commit()
            finally:
                cursor.close()
    except Exception as e:
        print(e)

class SessionData(BaseModel):
    UserID: str
    Type: str
    Company: str
    Email: str
    Phone: str
    Active: str
    WebSocketID: str | None = None

class SessionDataFilter(SessionData):
    filter: str | None = None

class SessionDataFiltered(SessionData):
    Option: int

class SODRuleBase(BaseModel):
    RiskId: int
    SecurityObjectLabel: str

class SODRule(SODRuleBase):
    Enabled: bool
    TableType: bool

class UpdateSODRuleSet(SessionData):
    SODRule: SODRule

class RemoveSODRules(SessionData):
    SODRules: List[SODRuleBase]

class DashResponse(BaseModel):
    url_complementation: str