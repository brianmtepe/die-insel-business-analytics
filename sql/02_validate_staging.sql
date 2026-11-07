-- =========================================================
-- DIE INSEL — STAGING DATA VALIDATION
-- =========================================================

USE die_insel_analytics;

-- 1. Confirm staging tables exist.
SHOW TABLES;

-- 2. Verify imported row counts.
SELECT 'stg_products' AS table_name, COUNT(*) AS total_rows
FROM stg_products

UNION ALL

SELECT 'stg_inventory', COUNT(*)
FROM stg_inventory

UNION ALL

SELECT 'stg_sales', COUNT(*)
FROM stg_sales

UNION ALL

SELECT 'stg_stock_movements', COUNT(*)
FROM stg_stock_movements;


-- 3. Inspect actual table definitions.
DESCRIBE stg_products;
DESCRIBE stg_inventory;
DESCRIBE stg_sales;
DESCRIBE stg_stock_movements;


-- 4. Inspect sales records.
SELECT *
FROM stg_sales
LIMIT 10;


-- 5. Inspect inventory records.
SELECT *
FROM stg_inventory
LIMIT 10;


-- 6. Inspect products.
SELECT *
FROM stg_products
LIMIT 10;


-- 7. Inspect stock movements.
SELECT *
FROM stg_stock_movements
LIMIT 10;


-- 8. Retrieve all column names and data types.
SELECT
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_KEY
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'die_insel_analytics'
  AND TABLE_NAME IN (
      'stg_products',
      'stg_inventory',
      'stg_sales',
      'stg_stock_movements'
  )
ORDER BY
    TABLE_NAME,
    ORDINAL_POSITION;