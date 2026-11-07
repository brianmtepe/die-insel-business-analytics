-- =========================================================
-- DIE INSEL — CORE DATA MODEL
-- =========================================================

USE die_insel_analytics;

CREATE TABLE IF NOT EXISTS dim_product (
    product_key BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    source_product_id VARCHAR(100) NOT NULL,
    product_name VARCHAR(200),
    category VARCHAR(100),
    unit_price DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (product_key),
    UNIQUE KEY uq_dim_product_source_id (source_product_id),
    KEY idx_dim_product_category (category)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS fact_sales (
    sales_key BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    source_sale_id VARCHAR(100),
    source_product_id VARCHAR(100) NOT NULL,
    transaction_date DATETIME,
    quantity DECIMAL(12,3),
    unit_price DECIMAL(12,2),
    sales_amount DECIMAL(14,2),

    PRIMARY KEY (sales_key),
    KEY idx_fact_sales_date (transaction_date),
    KEY idx_fact_sales_product (source_product_id)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS fact_inventory (
    inventory_key BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    source_product_id VARCHAR(100) NOT NULL,
    stock_quantity DECIMAL(12,3),
    recorded_at DATETIME,

    PRIMARY KEY (inventory_key),
    KEY idx_fact_inventory_product (source_product_id),
    KEY idx_fact_inventory_date (recorded_at)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS fact_stock_movements (
    movement_key BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    source_movement_id VARCHAR(100),
    source_product_id VARCHAR(100) NOT NULL,
    movement_type VARCHAR(50),
    movement_quantity DECIMAL(12,3),
    movement_date DATETIME,
    notes VARCHAR(500),

    PRIMARY KEY (movement_key),
    KEY idx_movements_product (source_product_id),
    KEY idx_movements_date (movement_date)
) ENGINE=InnoDB;


-- Confirm final table creation.
SHOW TABLES;