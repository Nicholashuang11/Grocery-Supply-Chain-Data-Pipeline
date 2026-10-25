import argparse
import logging
import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery
from sqlalchemy import URL, create_engine, text

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("bronze")

METADATA_COLS = {"run_id", "batch_date", "ingested_at"}
TABLES = {
    "suppliers": {
        "load_type": "full_load",
        "pk": ["supplier_id"],
        "sql": "SELECT * FROM public.suppliers",
    },
    "products": {
        "load_type": "full_load",
        "pk": ["product_id"],
        "sql": "SELECT * FROM public.products",
    },
    "warehouses": {
        "load_type": "full_load",
        "pk": ["warehouse_id"],
        "sql": "SELECT * FROM public.warehouses",
    },
    "purchase_order_lines": {
        "load_type": "full_load",
        "pk": ["purchase_order_id", "line_number"],
        "sql": "SELECT * FROM public.purchase_order_lines",
    },
    "inventory_opening_balances": {
        "load_type": "by_date",
        "pk": ["balance_date", "warehouse_id", "product_id"],
        "sql": """SELECT * FROM public.inventory_opening_balances
                   WHERE balance_date >= CAST(:s AS date)
                     AND balance_date <  CAST(:s AS date) + INTERVAL '1 day'""",
    },
    "purchase_orders": {
        "load_type": "by_date",
        "pk": ["purchase_order_id"],
        "sql": """SELECT * FROM public.purchase_orders
                   WHERE ordered_at >= CAST(:s AS date)
                     AND ordered_at <  CAST(:s AS date) + INTERVAL '1 day'""",
    },
    "inventory_movements": {
        "load_type": "by_date",
        "pk": ["movement_id"],
        "sql": """SELECT * FROM public.inventory_movements
                   WHERE movement_at >= CAST(:s AS date)
                     AND movement_at <  CAST(:s AS date) + INTERVAL '1 day'""",
    }
}

client = bigquery.Client()
PROJECT = client.project

url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("GROCERY_POSTGRES_USER"),
    password=os.getenv("GROCERY_POSTGRES_PASSWORD"),
    host=os.getenv("GROCERY_POSTGRES_HOST", "localhost"),
    port=int(os.getenv("GROCERY_POSTGRES_PORT")),
    database=os.getenv("GROCERY_POSTGRES_DB"),
)
engine = create_engine(url)
class DQError(Exception):
    pass

def check_schema_change(df, schema, table):
    src = set(df.columns)
    bq = {f.name for f in schema} - METADATA_COLS
    new_in_source = sorted(src - bq)
    missing_in_source = sorted(bq - src)
    if new_in_source or missing_in_source:
        raise DQError(
            f"{table}: schema drift. "
            f"New in source (not in BQ): {new_in_source}"
            f"In BQ but missing from source: {missing_in_source}"
        )
    
def compare_source_to_bq(table_id, ds, expected, table):
    query = f"SELECT COUNT(*) AS n FROM `{table_id}` WHERE batch_date = @ds"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("ds", "DATE", date.fromisoformat(ds))
        ]
    )
    actual = next(iter(client.query(query, job_config=job_config).result())).n
    if actual != expected:
        raise DQError(f"{table}: reconciliation failed. source={expected}, bigquery={actual}")
    log.info("%s: reconciliation OK (%d rows)", table, actual)


def conform(df, schema):
    missing = [f.name for f in schema if f.name not in df.columns]
    if missing:
        raise ValueError(f"DataFrame is missing columns: {missing}")
    for f in schema:
        c, t = f.name, f.field_type
        if t == "STRING":
            df[c] = df[c].astype("string")
        elif t == "INT64":
            df[c] = pd.to_numeric(df[c]).astype("Int64")
        elif t == "NUMERIC":
            q = Decimal(1).scaleb(-(f.scale if f.scale is not None else 9))
            df[c] = df[c].map(lambda x: None if pd.isna(x) else Decimal(str(x)).quantize(q))
        elif t == "DATE":
            df[c] = pd.to_datetime(df[c]).dt.date
        elif t == "TIMESTAMP":
            df[c] = pd.to_datetime(df[c], utc=True)
    return df[[f.name for f in schema]]


def load_table(client, engine, table, ds, run_id):
    cfg = TABLES[table]
    table_id = f"{PROJECT}.grocery_supply_bronze.{table}"
    partition_id = f"{table_id}${ds.replace('-', '')}"
    schema = client.get_table(table_id).schema
    df = pd.read_sql(text(cfg["sql"]), engine, params={"s": ds}, coerce_float=False)
    check_schema_change(df, schema, table)
    if df.empty:
        log.warning("%s: source returned 0 rows for %s, clearing partition", table, ds)
        client.delete_table(partition_id, not_found_ok=True)
        compare_source_to_bq(table_id, ds, 0, table)
        return
    
    df["run_id"] = run_id
    df["batch_date"] = date.fromisoformat(ds)
    df["ingested_at"] = datetime.now(timezone.utc)
    df = conform(df, schema)
    job = client.load_table_from_dataframe(
        df,
        partition_id,
        job_config=bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_TRUNCATE"),
    )
    job.result()
    log.info("%s: df=%d output_rows=%s", table, len(df), job.output_rows)
    compare_source_to_bq(table_id, ds, len(df), table)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ds", required=True)
    parser.add_argument("--run_id", required=True)
    parser.add_argument("--table", required=False)
    args = parser.parse_args()
    tables = [args.table] if args.table else list(TABLES)
    unknown = [t for t in tables if t not in TABLES]
    if unknown:
        sys.exit(f"unknown table(s): {unknown}")
    for t in tables:
        load_table(client, engine, t, args.ds, args.run_id)

if __name__ == "__main__":
    main()