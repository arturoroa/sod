import pandas as pd
import pathlib
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

current = pathlib.Path(".").parent.absolute()

load_dotenv(pathlib.Path(__file__).parent.parent / '.env', override=True)

engine = create_engine(
	f"mysql+mysqlconnector://{os.getenv('DB_USER', 'dbuser')}:{os.getenv('DB_PASSWORD', 'roandai.1')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/sod",
	echo=False,
)




SOD=f'{current}\\SOD_RuleSet.xlsx'
df=pd.read_excel(SOD)
df.to_sql(name="Original_SOD_Rule_Set", con=engine, if_exists="replace", index=False)