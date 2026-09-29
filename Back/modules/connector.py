import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


load_dotenv(Path(__file__).parent.parent / '.env', override=True)


def connect_db(user=None, passwd=None, host=None, port=None, database='sod'):
    user=user
    passwd=passwd
    host=host

    port=port
    database=database
    if user is None:
        user = os.getenv('DB_USER', 'root')
    if passwd is None:
        passwd = os.getenv('DB_PASSWORD', 'Aiver@2026')
    if host is None:
        host = os.getenv('DB_HOST', 'localhost')
    if port is None:
        port = int(os.getenv('DB_PORT', '3306'))
    db = mysql.connector.connect(host=host,user=user,password=passwd,database=database,port=port) 
    return db
    
