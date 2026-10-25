import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(
    host="localhost",
    port="6402",
    dbname=os.getenv("GROCERY_POSTGRES_DB"),
    user=os.getenv("GROCERY_POSTGRES_USER"),
    password=os.getenv("GROCERY_POSTGRES_PASSWORD")
)

with open('createtable.sql','r',encoding="utf-8")as file:
    CREATE_TABLE_SCRIPT = file.read()


cur=conn.cursor()
cur.execute(CREATE_TABLE_SCRIPT)
conn.commit()
cur.close()
conn.close()