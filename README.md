# Grocery Supply Chain Data Pipeline

A local data-engineering project that moves grocery supply-chain data from a **PostgreSQL source database** into a **BigQuery bronze layer**, orchestrated with **Apache Airflow** and run entirely in Docker.

## Architecture

```
PostgreSQL "grocery" (source, port 6402)
      │  insert_data_bronze_bq.py  (run per day by Airflow)
      ▼
BigQuery  <project>.grocery_supply_bronze.*   (bronze layer)
```

- **Source:** Postgres 16 container (`grocery-postgres`) holding the operational tables.
- **Orchestration:** Airflow (api-server, scheduler, dag-processor, triggerer) using `LocalExecutor`, with its own Postgres metadata DB.
- **Target:** BigQuery dataset `grocery_supply_bronze`, with every table carrying audit columns (`ingested_at`, `batch_date`, `run_id`).
- **Admin UI:** pgAdmin for browsing both Postgres databases.

## Dataset

This project uses the **Inventory & Supply Chain Dataset v1.0.0**, a deterministic synthetic operations dataset for inventory balances, supplier performance, lead-time analysis, and fulfillment modeling from Analytics Engineering. (2026). Inventory & Supply Chain Dataset (Version 1.0.0) [Data set]. https://www.analyticsengineering.com/datasets/inventory-supply-chain. 

| Table | Rows |
|---|---:|
| `suppliers` | 250 |
| `products` | 2,500 |
| `warehouses` | 12 |
| `inventory_opening_balances` | 30,000 |
| `purchase_orders` | 18,000 |
| `purchase_order_lines` | 53,967 |
| `inventory_movements` | 138,436 |

## How the Bronze Loader Works

For each table, `insert_data_bronze_bq.py`:

1. Reads the BigQuery table schema and queries Postgres (full table, or only rows for the given date).
2. **Schema drift check:** fails if columns differ between source and BigQuery (ignoring metadata columns).
3. Adds audit columns: `run_id`, `batch_date`, `ingested_at`.
4. Casts the DataFrame to the BigQuery types (`STRING`, `INT64`, `NUMERIC`, `DATE`, `TIMESTAMP`).
5. Loads into the target **partition** with `WRITE_TRUNCATE`, so re-running the same date is **idempotent**.
6. **Reconciliation check:** compares the source row count to the row count in BigQuery for that `batch_date` and fails on mismatch.

If the source returns zero rows for a date, the corresponding partition is cleared and verified as empty.
## Data Model

Seven tables, defined in `createtable.sql` (Postgres) and `bqcreatetablebronze.sql` (BigQuery):

| Table | Description | Load type | BQ partition |
|---|---|---|---|
| `suppliers` | Supplier master data, lead time, reliability score | full load | `batch_date` |
| `products` | Product/SKU catalogue, unit cost, reorder point | full load | `batch_date` |
| `warehouses` | Warehouse master data and capacity | full load | `batch_date` |
| `purchase_order_lines` | Line items per purchase order | full load | `batch_date` |
| `inventory_opening_balances` | Opening stock per product/warehouse/date | by date (`balance_date`) | `balance_date` |
| `purchase_orders` | PO headers with ordered/expected/received dates | by date (`ordered_at`) | `ordered_at` |
| `inventory_movements` | Stock movements (PO receipts, transfers, etc.) | by date (`movement_at`) | `movement_at` |

## Project Structure
```
.
├── docker-compose.yml            # Airflow, both Postgres DBs, pgAdmin
├── Dockerfile                    # Custom Airflow image (referenced by `build: .`)
├── .env                          # Secrets and config (not committed)
├── dags/                         # Airflow DAGs
├── scripts/                      # Scripts mounted into Airflow (e.g. the bronze loader)
├── config/  logs/  plugins/      # Airflow volumes
├── dataset/                      # Source CSV files, one per table
├── createtable.sql               # Postgres DDL (source)
├── createtablelocal.py           # Runs createtable.sql against local Postgres
├── insert_local_db.py            # Loads dataset/*.csv into local Postgres
├── bqcreatetablebronze.sql       # BigQuery DDL (bronze layer)
├── createbqtable.py              # Runs bqcreatetablebronze.sql against BigQuery
└── insert_data_bronze_bq.py      # Postgres → BigQuery bronze loader
```

