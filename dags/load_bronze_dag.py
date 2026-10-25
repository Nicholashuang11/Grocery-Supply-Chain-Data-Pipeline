from airflow.sdk import DAG
from datetime import date, timedelta
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime,timedelta
SCRIPT = "/opt/airflow/scripts/insert_data_bronze_bq.py"
FULL_LOAD = ["suppliers", "products", "warehouses", "purchase_order_lines"]
BY_DATE = ["purchase_orders", "inventory_opening_balances", "inventory_movements"]

default_args={
    "owner":"data engineering",
    "retries":3,
    "retry_delay":timedelta(minutes=5),
}
with DAG(
    dag_id="load_grocery_bronze_bq1",
    default_args=default_args,
    start_date=datetime(2026,10,19),
    schedule="@daily",
    catchup=True,
    tags=["bronze", "grocery"],
)as dag:
    for table in FULL_LOAD + BY_DATE:
        BashOperator(
            task_id=f"load_{table}",
            bash_command=f"python {SCRIPT} --ds {{{{ ds }}}} --run_id '{{{{ run_id }}}}' --table {table}",
        )