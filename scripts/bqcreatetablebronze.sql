CREATE SCHEMA IF NOT EXISTS `hidden.hidden`;
CREATE OR REPLACE TABLE `hidden.hidden.suppliers`(
    supplier_id STRING PRIMARY KEY NOT ENFORCED,
    supplier_name STRING,
    country_code STRING,
    lead_time_days INT64,
    reliability_score NUMERIC,
    ingested_at TIMESTAMP,
    batch_date DATE,
    run_id STRING
)PARTITION BY batch_date CLUSTER BY supplier_id;

CREATE OR REPLACE TABLE `hidden.hidden.products` (
    product_id STRING PRIMARY KEY NOT ENFORCED,
    supplier_id STRING,
    sku STRING,
    category STRING,
    unit_cost NUMERIC(12, 2),
    reorder_point INT64,
    ingested_at TIMESTAMP,
    batch_date DATE,
    run_id STRING 
)PARTITION BY batch_date CLUSTER BY product_id, supplier_id;

CREATE OR REPLACE TABLE `hidden.hidden.warehouses` (
    warehouse_id STRING PRIMARY KEY NOT ENFORCED,
    warehouse_name STRING,
    region STRING,
    capacity_units INT64,
    ingested_at TIMESTAMP,
    batch_date DATE,
    run_id STRING
)PARTITION BY batch_date CLUSTER BY warehouse_id;

CREATE OR REPLACE TABLE `hidden.hidden.inventory_opening_balances` (
    opening_balance_id STRING PRIMARY KEY NOT ENFORCED,
    product_id STRING,
    warehouse_id STRING,
    balance_date DATE,
    opening_units INT64,
    ingested_at TIMESTAMP,
    batch_date DATE,
    run_id STRING
) PARTITION BY balance_date CLUSTER BY product_id,warehouse_id;

CREATE OR REPLACE TABLE `hidden.hidden.purchase_orders` 
(
    purchase_order_id STRING PRIMARY KEY NOT ENFORCED,
    supplier_id STRING,
    warehouse_id STRING,
    ordered_at DATE,
    expected_at DATE,
    received_at DATE,
    status STRING,
    ingested_at TIMESTAMP,
    batch_date DATE,
    run_id STRING
)PARTITION BY ordered_at CLUSTER BY supplier_id, warehouse_id;

CREATE OR REPLACE TABLE `hidden.hidden.purchase_order_lines` (
    purchase_order_line_id STRING PRIMARY KEY NOT ENFORCED,
    purchase_order_id STRING,
    product_id STRING,
    quantity_ordered INT64,
    quantity_received INT64,
    unit_cost NUMERIC(12, 2),
    ingested_at TIMESTAMP,
    batch_date DATE,
    run_id STRING
)PARTITION BY batch_date CLUSTER BY product_id, purchase_order_id;

CREATE OR REPLACE TABLE `hidden.hidden.inventory_movements` (
    movement_id STRING PRIMARY KEY NOT ENFORCED,
    product_id STRING,
    warehouse_id STRING,
    movement_at DATE,
    movement_type STRING,
    quantity_change INT64,
    purchase_order_line_id STRING,
    transfer_id STRING,
    ingested_at TIMESTAMP,
    batch_date DATE,
    run_id STRING
) PARTITION BY movement_at CLUSTER BY product_id, warehouse_id;
