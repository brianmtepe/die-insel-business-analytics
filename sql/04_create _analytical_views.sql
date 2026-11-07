USE die_insel_analytics;

-- ============================================================
-- DIE INSEL BUSINESS ANALYTICS
-- FILE: 04_create_analytical_views.sql
-- PURPOSE: Seven reusable reporting views for Power BI
-- ============================================================


-- ------------------------------------------------------------
-- VIEW 1: DAILY SALES PERFORMANCE
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW vw_daily_sales AS
SELECT
    DATE(transaction_date) AS sales_date,

    COUNT(DISTINCT source_sale_id) AS transaction_count,

    ROUND(SUM(quantity), 2) AS units_sold,

    ROUND(SUM(sales_amount), 2) AS revenue_kes,

    ROUND(
        SUM(sales_amount) /
        NULLIF(COUNT(DISTINCT source_sale_id), 0),
        2
    ) AS average_transaction_value_kes

FROM fact_sales

GROUP BY DATE(transaction_date);


-- ------------------------------------------------------------
-- VIEW 2: PRODUCT PERFORMANCE
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW vw_product_performance AS
SELECT
    p.source_product_id AS product_id,

    p.product_name,

    p.category,

    COUNT(DISTINCT s.source_sale_id) AS transaction_count,

    ROUND(COALESCE(SUM(s.quantity), 0), 2) AS units_sold,

    ROUND(
        COALESCE(SUM(s.sales_amount), 0),
        2
    ) AS revenue_kes,

    ROUND(
        COALESCE(SUM(s.sales_amount), 0) /
        NULLIF(SUM(s.quantity), 0),
        2
    ) AS average_selling_price_kes

FROM dim_product AS p

LEFT JOIN fact_sales AS s
    ON s.source_product_id = p.source_product_id

GROUP BY
    p.source_product_id,
    p.product_name,
    p.category;


-- ------------------------------------------------------------
-- VIEW 3: CATEGORY PERFORMANCE
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW vw_category_performance AS
SELECT
    p.category,

    COUNT(DISTINCT p.source_product_id) AS product_count,

    COUNT(DISTINCT s.source_sale_id) AS transaction_count,

    ROUND(COALESCE(SUM(s.quantity), 0), 2) AS units_sold,

    ROUND(
        COALESCE(SUM(s.sales_amount), 0),
        2
    ) AS revenue_kes

FROM dim_product AS p

LEFT JOIN fact_sales AS s
    ON s.source_product_id = p.source_product_id

GROUP BY p.category;


-- ------------------------------------------------------------
-- VIEW 4: LATEST INVENTORY POSITION
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW vw_inventory_position AS
WITH ranked_inventory AS (
    SELECT
        source_product_id,

        stock_quantity,

        recorded_at,

        ROW_NUMBER() OVER (
            PARTITION BY source_product_id
            ORDER BY recorded_at DESC
        ) AS row_num

    FROM fact_inventory
)

SELECT
    p.source_product_id AS product_id,

    p.product_name,

    p.category,

    p.unit_price,

    i.stock_quantity AS physical_closing_stock,

    i.recorded_at AS latest_snapshot_date,

    CASE
        WHEN i.source_product_id IS NULL
            THEN 'No Inventory Record'

        WHEN i.stock_quantity <= 0
            THEN 'Out of Stock'

        ELSE 'In Stock'
    END AS stock_status

FROM dim_product AS p

LEFT JOIN ranked_inventory AS i
    ON i.source_product_id = p.source_product_id
   AND i.row_num = 1;


-- ------------------------------------------------------------
-- VIEW 5: INVENTORY HISTORY
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW vw_inventory_history AS
SELECT
    i.recorded_at AS snapshot_date,

    p.source_product_id AS product_id,

    p.product_name,

    p.category,

    i.stock_quantity AS physical_closing_stock

FROM fact_inventory AS i

LEFT JOIN dim_product AS p
    ON p.source_product_id = i.source_product_id;


-- ------------------------------------------------------------
-- VIEW 6: STOCK MOVEMENT ANALYSIS
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW vw_stock_movement_analysis AS
SELECT
    DATE(m.movement_date) AS movement_date,

    p.source_product_id AS product_id,

    p.product_name,

    p.category,

    m.movement_type,

    COUNT(*) AS movement_count,

    ROUND(
        SUM(m.movement_quantity),
        2
    ) AS total_movement_quantity

FROM fact_stock_movements AS m

LEFT JOIN dim_product AS p
    ON p.source_product_id = m.source_product_id

GROUP BY
    DATE(m.movement_date),
    p.source_product_id,
    p.product_name,
    p.category,
    m.movement_type;


-- ------------------------------------------------------------
-- VIEW 7: EXECUTIVE BUSINESS SUMMARY
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW vw_business_summary AS
SELECT
    (
        SELECT COUNT(*)
        FROM dim_product
    ) AS product_count,

    (
        SELECT COUNT(DISTINCT source_sale_id)
        FROM fact_sales
    ) AS transaction_count,

    (
        SELECT ROUND(
            COALESCE(SUM(quantity), 0),
            2
        )
        FROM fact_sales
    ) AS units_sold,

    (
        SELECT ROUND(
            COALESCE(SUM(sales_amount), 0),
            2
        )
        FROM fact_sales
    ) AS total_revenue_kes,

    (
        SELECT ROUND(
            COALESCE(SUM(sales_amount), 0) /
            NULLIF(COUNT(DISTINCT source_sale_id), 0),
            2
        )
        FROM fact_sales
    ) AS average_transaction_value_kes,

    (
        SELECT COUNT(*)
        FROM fact_inventory
    ) AS inventory_snapshot_count,

    (
        SELECT COUNT(*)
        FROM fact_stock_movements
    ) AS stock_movement_count;
    
    
    USE die_insel_analytics;

-- ============================================================
-- DIE INSEL BUSINESS ANALYTICS
-- VIEW: HOURLY SALES PERFORMANCE
-- PURPOSE: Analyse sales activity by hour of day
-- SOURCE: fact_sales
-- ============================================================
USE die_insel_analytics;

CREATE OR REPLACE VIEW vw_hourly_sales AS

SELECT
    HOUR(transaction_date) AS sale_hour,

    COUNT(DISTINCT source_sale_id)
        AS transaction_count,

    SUM(quantity)
        AS units_sold,

    ROUND(SUM(sales_amount), 2)
        AS revenue_kes,

    ROUND(
        SUM(sales_amount) /
        NULLIF(COUNT(DISTINCT source_sale_id), 0),
        2
    ) AS average_transaction_value_kes

FROM fact_sales

WHERE transaction_date IS NOT NULL

GROUP BY HOUR(transaction_date);