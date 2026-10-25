CREATE TABLE suppliers (
    supplier_id TEXT PRIMARY KEY,
    supplier_name TEXT,
    country_code TEXT,
    lead_time_days INTEGER,
    reliability_score NUMERIC
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    supplier_id TEXT,
    sku TEXT UNIQUE,
    category TEXT,
    unit_cost NUMERIC(12, 2),
    reorder_point INTEGER,
    CONSTRAINT fk_products_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id)
);

CREATE TABLE warehouses (
    warehouse_id TEXT PRIMARY KEY,
    warehouse_name TEXT,
    region TEXT,
    capacity_units INTEGER
);

CREATE TABLE inventory_opening_balances (
    opening_balance_id TEXT PRIMARY KEY,
    product_id TEXT,
    warehouse_id TEXT,
    balance_date DATE,
    opening_units INTEGER,
    CONSTRAINT fk_inventory_opening_balances_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),
    CONSTRAINT fk_inventory_opening_balances_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(warehouse_id)
);

CREATE TABLE purchase_orders (
    purchase_order_id TEXT PRIMARY KEY,
    supplier_id TEXT,
    warehouse_id TEXT,
    ordered_at DATE,
    expected_at DATE,
    received_at DATE,
    status TEXT,

    CONSTRAINT fk_purchase_orders_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id),

    CONSTRAINT fk_purchase_orders_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(warehouse_id)
);

CREATE TABLE purchase_order_lines (
    purchase_order_line_id TEXT PRIMARY KEY,
    purchase_order_id TEXT,
    product_id TEXT,
    quantity_ordered INTEGER,
    quantity_received INTEGER,
    unit_cost NUMERIC(12, 2),

    CONSTRAINT fk_purchase_order_lines_purchase_order
        FOREIGN KEY (purchase_order_id)
        REFERENCES purchase_orders(purchase_order_id),

    CONSTRAINT fk_purchase_order_lines_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);

CREATE TABLE inventory_movements (
    movement_id TEXT PRIMARY KEY,
    product_id TEXT,
    warehouse_id TEXT,
    movement_at DATE,
    movement_type TEXT,
    quantity_change INTEGER,
    purchase_order_line_id TEXT,
    transfer_id TEXT,

    CONSTRAINT fk_inventory_movements_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT fk_inventory_movements_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(warehouse_id),

    CONSTRAINT fk_inventory_movements_po_line
        FOREIGN KEY (purchase_order_line_id)
        REFERENCES purchase_order_lines(purchase_order_line_id)
);

CREATE INDEX idx_products_supplier
    ON products(supplier_id);

CREATE INDEX idx_opening_balances_warehouse
    ON inventory_opening_balances(warehouse_id);

CREATE INDEX idx_purchase_orders_supplier
    ON purchase_orders(supplier_id);

CREATE INDEX idx_purchase_orders_warehouse
    ON purchase_orders(warehouse_id);

CREATE INDEX idx_po_lines_product
    ON purchase_order_lines(product_id);

CREATE INDEX idx_inventory_movements_product
    ON inventory_movements(product_id);

CREATE INDEX idx_inventory_movement_warehouse
    ON inventory_movements(movement_id);
    
CREATE INDEX idx_inventory_movements_po_line
    ON inventory_movements(purchase_order_line_id);
