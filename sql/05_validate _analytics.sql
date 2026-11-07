USE die_insel_analytics;

-- ============================================================
-- DIE INSEL BUSINESS ANALYTICS
-- FILE: 05_validate_analytics.sql
-- PURPOSE: Validate data completeness and analytical outputs
-- ============================================================


-- 1. CORE TABLE ROW COUNTS

SELECT
    'dim_product' AS table_name,
    COUNT(*) AS row_count
FROM dim_product

UNION ALL

SELECT
    'fact_sales',
    COUNT(*)
FROM fact_sales

UNION ALL

SELECT
    'fact_inventory',
    COUNT(*)
FROM fact_inventory

UNION ALL

SELECT
    'fact_stock_movements',
    COUNT(*)
FROM fact_stock_movements;


-- 2. STAGING VERSUS CORE ROW COUNTS

SELECT
    'products' AS dataset,
    (SELECT COUNT(*) FROM stg_products) AS staging_rows,
    (SELECT COUNT(*) FROM dim_product) AS core_rows

UNION ALL

SELECT
    'sales',
    (SELECT COUNT(*) FROM stg_sales),
    (SELECT COUNT(*) FROM fact_sales)

UNION ALL

SELECT
    'inventory',
    (SELECT COUNT(*) FROM stg_inventory),
    (SELECT COUNT(*) FROM fact_inventory)

UNION ALL

SELECT
    'stock movements',
    (SELECT COUNT(*) FROM stg_stock_movements),
    (SELECT COUNT(*) FROM fact_stock_movements);


-- 3. SALES REVENUE AND TRANSACTION SUMMARY

SELECT
    COUNT(*) AS sales_records,

    COUNT(DISTINCT source_sale_id) AS distinct_transactions,

    ROUND(SUM(quantity), 2) AS units_sold,

    ROUND(SUM(sales_amount), 2) AS total_revenue_kes,

    ROUND(
        SUM(sales_amount) /
        NULLIF(COUNT(DISTINCT source_sale_id), 0),
        2
    ) AS average_transaction_value_kes,

    MIN(transaction_date) AS first_transaction,

    MAX(transaction_date) AS last_transaction

FROM fact_sales;


-- 4. CHECK FOR SALES WITHOUT A MATCHING PRODUCT

SELECT
    COUNT(*) AS unmatched_sales

FROM fact_sales AS s

LEFT JOIN dim_product AS p
    ON p.source_product_id = s.source_product_id

WHERE p.source_product_id IS NULL;


-- 5. CHECK FOR INVENTORY WITHOUT A MATCHING PRODUCT

SELECT
    COUNT(*) AS unmatched_inventory

FROM fact_inventory AS i

LEFT JOIN dim_product AS p
    ON p.source_product_id = i.source_product_id

WHERE p.source_product_id IS NULL;


-- 6. CHECK FOR MOVEMENTS WITHOUT A MATCHING PRODUCT

SELECT
    COUNT(*) AS unmatched_movements

FROM fact_stock_movements AS m

LEFT JOIN dim_product AS p
    ON p.source_product_id = m.source_product_id

WHERE p.source_product_id IS NULL;


-- 7. INSPECT ALL SEVEN ANALYTICAL VIEWS

SELECT * FROM vw_business_summary;

SELECT *
FROM vw_daily_sales
ORDER BY sales_date DESC
LIMIT 20;

SELECT *
FROM vw_product_performance
ORDER BY revenue_kes DESC
LIMIT 20;

SELECT *
FROM vw_category_performance
ORDER BY revenue_kes DESC;

SELECT *
FROM vw_inventory_position
ORDER BY product_name;

SELECT *
FROM vw_inventory_history
ORDER BY snapshot_date DESC
LIMIT 100;

SELECT *
FROM vw_stock_movement_analysis
ORDER BY movement_date DESC
LIMIT 100;


-- 8. CONFIRM THAT ALL SEVEN VIEWS EXIST

SHOW FULL TABLES
WHERE Table_type = 'VIEW';