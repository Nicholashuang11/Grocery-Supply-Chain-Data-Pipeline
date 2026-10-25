
from sqlalchemy import text,create_engine, MetaData, Table, insert, URL
from dotenv import load_dotenv
import os
import csv
load_dotenv()
url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("GROCERY_POSTGRES_USER"),
    password=os.getenv("GROCERY_POSTGRES_PASSWORD"),
    host=os.getenv("localhost"),
    port=int(os.getenv("GROCERY_POSTGRES_PORT")),
    database=os.getenv("GROCERY_POSTGRES_DB")
)

engine = create_engine(url)
try:
     with engine.connect as conn:
        result = conn.execute(text("SELECT 1"))
        print("Connection successful!", flush=True)
        print("Test result:", result.scalar(), flush=True)

except Exception as e:
    print(f"Connection failed: {e}", flush=True)

TABLE_NAME={
    "suppliers":"suppliers.csv",
    "products":"products.csv",
    "warehouses":"warehouses.csv",
    "inventory_opening_balances":"inventory_opening_balances.csv",
    "purchase_orders":"purchase_orders.csv",
    "purchase_order_lines":"purchase_order_lines.csv",
    "inventory_movements":"inventory_movements.csv",
}

metadata = MetaData()
with engine.begin() as conn:
    for table_name, filename in TABLE_NAME.items():
            table = Table(
                table_name,
                metadata,
                autoload_with=conn
            )
            with open(f"dataset/{filename}", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                rows = list(reader)
            rows = [
                {
                    key: (value if value != "" else None)
                    for key, value in row.items()
                }
                for row in rows
            ]

            if not rows:
                print(f"{table_name}: no rows to insert")
                continue
            conn.execute(insert(table), rows)
            print(f"{table_name}: inserted {len(rows)} rows")

    print("Import completed!")
engine.dispose()