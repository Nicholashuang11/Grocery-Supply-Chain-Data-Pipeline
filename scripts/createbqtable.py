from google.cloud import bigquery
from dotenv import load_dotenv
import os
load_dotenv()
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
client = bigquery.Client()
with open('bqcreatetablebronze.sql','r',encoding="utf-8")as file:
    SQL_SCRIPT = file.read()

query_job = client.query(SQL_SCRIPT)
print(f"done success")