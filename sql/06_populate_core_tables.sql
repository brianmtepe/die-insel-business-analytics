USE die_insel_analytics;

-- ============================================================
-- DIE INSEL BUSINESS ANALYTICS
-- FILE: 06_populate_core_tables.sql
-- PURPOSE: Transform staging data into analytical tables
-- ============================================================

START TRANSACTION;

-- ------------------------------------------------------------
-- 1. POPULATE PRODUCT DIMENSION
-- ------------------------------------------------------------

INSERT INTO dim_product (
    source_product_id,
    product_name,
    category,
    unit_price,
    created_at
)
SELECT
    TRIM(s.product_id),
    NULLIF(TRIM(s.product_name), ''),
    NULLIF(TRIM(s.category), ''),

    CAST(
        COALESCE(
            NULLIF(TRIM(s.unit_price_kes), ''),
            NULLIF(TRIM(s.demo_unit_price_kes), ''),
            '0'
        ) AS DECIMAL(12,2)
    ),

    CURRENT_TIMESTAMP

FROM stg_products AS s

WHERE NULLIF(TRIM(s.product_id), '') IS NOT NULL

AND NOT EXISTS (
    SELECT 1
    FROM dim_product AS p
    WHERE p.source_product_id = TRIM(s.product_id)
);


-- ------------------------------------------------------------
-- 2. POPULATE SALES FACT TABLE
-- ------------------------------------------------------------

INSERT INTO fact_sales (
    source_sale_id,
    source_product_id,
    transaction_date,
    quantity,
    unit_price,
    sales_amount
)
SELECT
    TRIM(s.transaction_id),
    TRIM(s.product_id),

    CAST(
        REPLACE(TRIM(s.sale_datetime), 'T', ' ')
        AS DATETIME
    ),

    CAST(s.quantity AS DECIMAL(12,3)),
    CAST(s.unit_price_kes AS DECIMAL(12,2)),
    CAST(s.revenue_kes AS DECIMAL(14,2))

FROM stg_sales AS s

INNER JOIN dim_product AS p
    ON p.source_product_id = TRIM(s.product_id)

WHERE NULLIF(TRIM(s.transaction_id), '') IS NOT NULL
  AND NULLIF(TRIM(s.product_id), '') IS NOT NULL
  AND NULLIF(TRIM(s.sale_datetime), '') IS NOT NULL

  AND NOT EXISTS (
      SELECT 1
      FROM fact_sales AS f
      WHERE f.source_sale_id = TRIM(s.transaction_id)
  );


-- ------------------------------------------------------------
-- 3. POPULATE INVENTORY FACT TABLE
-- ------------------------------------------------------------

INSERT INTO fact_inventory (
    source_product_id,
    stock_quantity,
    recorded_at
)
SELECT
    TRIM(s.product_id),

    CAST(
        NULLIF(TRIM(s.physical_closing_stock), '')
        AS DECIMAL(12,3)
    ),

    CAST(
        LEFT(TRIM(s.snapshot_date), 10)
        AS DATETIME
    )

FROM stg_inventory AS s

INNER JOIN dim_product AS p
    ON p.source_product_id = TRIM(s.product_id)

WHERE NULLIF(TRIM(s.product_id), '') IS NOT NULL
  AND NULLIF(TRIM(s.snapshot_date), '') IS NOT NULL
  AND NULLIF(TRIM(s.physical_closing_stock), '') IS NOT NULL

  AND NOT EXISTS (
      SELECT 1
      FROM fact_inventory AS f
      WHERE f.source_product_id = TRIM(s.product_id)
        AND f.recorded_at = CAST(
            LEFT(TRIM(s.snapshot_date), 10)
            AS DATETIME
        )
  );


-- ------------------------------------------------------------
-- 4. POPULATE STOCK MOVEMENTS FACT TABLE
-- ------------------------------------------------------------

INSERT INTO fact_stock_movements (
    source_movement_id,
    source_product_id,
    movement_type,
    movement_quantity,
    movement_date,
    notes
)
SELECT
    TRIM(s.movement_id),
    TRIM(s.product_id),
    NULLIF(TRIM(s.movement_type), ''),
    CAST(s.quantity AS DECIMAL(12,3)),

    CAST(
        REPLACE(TRIM(s.movement_date), 'T', ' ')
        AS DATETIME
    ),

    'Imported from staging data'

FROM stg_stock_movements AS s

INNER JOIN dim_product AS p
    ON p.source_product_id = TRIM(s.product_id)

WHERE NULLIF(TRIM(s.movement_id), '') IS NOT NULL
  AND NULLIF(TRIM(s.product_id), '') IS NOT NULL
  AND NULLIF(TRIM(s.movement_date), '') IS NOT NULL

  AND NOT EXISTS (
      SELECT 1
      FROM fact_stock_movements AS f
      WHERE f.source_movement_id = TRIM(s.movement_id)
  );


-- Commit the data transformation.
COMMIT;


-- ------------------------------------------------------------
-- 5. VERIFY CORE TABLE POPULATION
-- ------------------------------------------------------------

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