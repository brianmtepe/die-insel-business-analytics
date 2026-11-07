from pathlib import Path
import json

import numpy as np
import pandas as pd


# ============================================================
# 1. PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

GENERATED = ROOT / "data" / "generated"
PROCESSED = ROOT / "data" / "processed"
DOCUMENTATION = ROOT / "documentation"

PROCESSED.mkdir(parents=True, exist_ok=True)
DOCUMENTATION.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. LOAD SOURCE DATA
# ============================================================

products = pd.read_csv(
    GENERATED / "demo_products_raw.csv"
)

sales = pd.read_csv(
    GENERATED / "demo_sales_raw.csv"
)

inventory = pd.read_csv(
    GENERATED / "demo_inventory_raw.csv"
)

movements = pd.read_csv(
    GENERATED / "demo_stock_movements_raw.csv"
)


# ============================================================
# 3. DEFINE REQUIRED COLUMNS
# ============================================================

required_product_columns = {
    "product_id",
    "product_name",
    "category",
    "subcategory",
    "unit_price_kes",
    "demo_unit_price_kes",
    "price_source",
}

required_sales_columns = {
    "transaction_id",
    "sale_datetime",
    "product_id",
    "product_name",
    "category",
    "quantity",
    "unit_price_kes",
    "revenue_kes",
    "payment_method",
}

required_inventory_columns = {
    "snapshot_date",
    "product_id",
    "opening_stock",
    "purchases",
    "units_sold",
    "wastage",
    "expected_closing_stock",
    "physical_closing_stock",
    "stockout_flag",
}

required_movement_columns = {
    "movement_id",
    "movement_date",
    "product_id",
    "movement_type",
    "quantity",
}

def require_columns(df, required, dataset_name):

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"{dataset_name} is missing columns: {sorted(missing)}"
        )


require_columns(
    products,
    required_product_columns,
    "Products"
)

require_columns(
    sales,
    required_sales_columns,
    "Sales"
)

require_columns(
    inventory,
    required_inventory_columns,
    "Inventory"
)

require_columns(
    movements,
    required_movement_columns,
    "Movements"
)


# ============================================================
# 4. STANDARDISE TEXT FIELDS
# ============================================================

def clean_text(series):

    cleaned = series.astype("string").str.strip()

    cleaned = cleaned.replace(
        {
            "": pd.NA,
            "nan": pd.NA,
            "None": pd.NA,
        }
    )

    return cleaned


for column in [
    "product_id",
    "product_name",
    "category",
    "subcategory",
    "price_source",
]:
    products[column] = clean_text(products[column])


for column in [
    "transaction_id",
    "product_id",
    "product_name",
    "category",
    "payment_method",
]:
    sales[column] = clean_text(sales[column])


for column in [
    "product_id",
]:
    inventory[column] = clean_text(inventory[column])

for column in [
    "movement_id",
    "product_id",
    "movement_type",
]:
    movements[column] = clean_text(movements[column])


# ============================================================
# 5. PARSE DATES
# ============================================================

sales["sale_datetime"] = pd.to_datetime(
    sales["sale_datetime"],
    errors="coerce"
)

inventory["snapshot_date"] = pd.to_datetime(
    inventory["snapshot_date"],
    errors="coerce"
).dt.normalize()

movements["movement_date"] = pd.to_datetime(
    movements["movement_date"],
    errors="coerce"
).dt.normalize()


# ============================================================
# 6. CONVERT NUMERIC FIELDS
# ============================================================

product_numeric_columns = [
    "unit_price_kes",
    "demo_unit_price_kes",
]

for column in product_numeric_columns:
    products[column] = pd.to_numeric(
        products[column],
        errors="coerce"
    )


sales_numeric_columns = [
    "quantity",
    "unit_price_kes",
    "revenue_kes",
]

for column in sales_numeric_columns:
    sales[column] = pd.to_numeric(
        sales[column],
        errors="coerce"
    )


inventory_numeric_columns = [
    "opening_stock",
    "purchases",
    "units_sold",
    "wastage",
    "expected_closing_stock",
    "physical_closing_stock",
]

for column in inventory_numeric_columns:
    inventory[column] = pd.to_numeric(
        inventory[column],
        errors="coerce"
    )


movements["quantity"] = pd.to_numeric(
    movements["quantity"],
    errors="coerce"
)


# ============================================================
# 7. VALIDATE PRODUCT MASTER
# ============================================================

if products["product_id"].isna().any():
    raise ValueError("Product master contains missing IDs.")

if products["product_name"].isna().any():
    raise ValueError("Product master contains missing names.")

if products["product_id"].duplicated().any():
    raise ValueError("Product master contains duplicate IDs.")

if products["product_name"].duplicated().any():
    raise ValueError("Product master contains duplicate names.")

if products["category"].isna().any():
    raise ValueError("Product master contains missing categories.")

if products["demo_unit_price_kes"].isna().any():
    raise ValueError("Missing synthetic demonstration prices.")

if (products["demo_unit_price_kes"] <= 0).any():
    raise ValueError("Non-positive demonstration price found.")


# ============================================================
# 8. CAPTURE RAW QUALITY ISSUES
# ============================================================

raw_sales_rows = len(sales)

raw_duplicate_sales = int(
    sales.duplicated().sum()
)

raw_missing_payment = int(
    sales["payment_method"].isna().sum()
)

raw_invalid_quantity = int(
    (sales["quantity"] <= 0).sum()
)

raw_missing_date = int(
    sales["sale_datetime"].isna().sum()
)

raw_missing_transaction_id = int(
    sales["transaction_id"].isna().sum()
)


# ============================================================
# 9. DEDUPLICATE SALES
# ============================================================

# Remove only exact duplicate rows.
# Multiple legitimate product lines can share a transaction ID.

sales = sales.drop_duplicates().copy()


# ============================================================
# 10. REMOVE UNUSABLE SALES ROWS
# ============================================================

sales = sales.dropna(
    subset=[
        "transaction_id",
        "sale_datetime",
        "product_id",
        "quantity",
        "unit_price_kes",
        "revenue_kes",
    ]
).copy()


# ============================================================
# 11. VALIDATE PRODUCT REFERENCES
# ============================================================

valid_product_ids = set(products["product_id"])

unknown_products = ~sales["product_id"].isin(
    valid_product_ids
)

unknown_product_count = int(
    unknown_products.sum()
)

sales = sales.loc[~unknown_products].copy()


# ============================================================
# 12. VALIDATE QUANTITIES AND PRICES
# ============================================================

sales = sales.loc[
    (sales["quantity"] > 0)
    & (sales["quantity"] % 1 == 0)
    & (sales["unit_price_kes"] > 0)
    & (sales["revenue_kes"] >= 0)
].copy()


# ============================================================
# 13. STANDARDISE PRODUCT ATTRIBUTES
# ============================================================

product_lookup = products.set_index("product_id")

sales["product_name"] = sales["product_id"].map(
    product_lookup["product_name"]
)

sales["category"] = sales["product_id"].map(
    product_lookup["category"]
)

sales["subcategory"] = sales["product_id"].map(
    product_lookup["subcategory"]
)

sales["price_source"] = sales["product_id"].map(
    product_lookup["price_source"]
)


# ============================================================
# 14. RECONCILE REVENUE
# ============================================================

sales["calculated_revenue_kes"] = (
    sales["quantity"] * sales["unit_price_kes"]
).round(2)

sales["revenue_difference_kes"] = (
    sales["revenue_kes"]
    - sales["calculated_revenue_kes"]
).round(2)

revenue_mismatch_count = int(
    (
        sales["revenue_difference_kes"].abs() > 0.01
    ).sum()
)

# In this synthetic dataset, revenue is defined as quantity × price.
# We recalculate revenue after retaining the mismatch count.

sales["revenue_kes"] = sales[
    "calculated_revenue_kes"
]


# ============================================================
# 15. HANDLE MISSING PAYMENT METHOD
# ============================================================

# Unknown is preferable to inventing a payment method.

sales["payment_method"] = (
    sales["payment_method"]
    .fillna("Unknown")
)

sales["payment_method"] = (
    sales["payment_method"]
    .replace("", "Unknown")
)


# ============================================================
# 16. CLEAN INVENTORY
# ============================================================

inventory = inventory.dropna(
    subset=[
        "snapshot_date",
        "product_id",
    ]
).copy()

inventory = inventory.loc[
    inventory["product_id"].isin(valid_product_ids)
].copy()

inventory = inventory.drop_duplicates(
    subset=[
        "snapshot_date",
        "product_id",
    ],
    keep="last"
).copy()

inventory_numeric_columns = [
    "opening_stock",
    "purchases",
    "units_sold",
    "wastage",
    "expected_closing_stock",
    "physical_closing_stock",
]

for column in inventory_numeric_columns:
    inventory = inventory.loc[
        inventory[column].notna()
        & (inventory[column] >= 0)
        & (inventory[column] % 1 == 0)
    ].copy()

inventory["stockout_flag"] = (
    inventory["stockout_flag"]
    .astype(str)
    .str.lower()
    .map({
        "true": True,
        "false": False,
        "1": True,
        "0": False,
    })
)

inventory = inventory.dropna(
    subset=["stockout_flag"]
).copy()

inventory["stockout_flag"] = (
    inventory["stockout_flag"].astype(bool)
)


# ============================================================
# 17. CLEAN STOCK MOVEMENTS
# ============================================================

movements = movements.dropna(
    subset=[
        "movement_id",
        "movement_date",
        "product_id",
        "movement_type",
        "quantity",
    ]
).copy()

movements = movements.drop_duplicates(
    subset=["movement_id"],
    keep="first"
).copy()

movements = movements.loc[
    movements["product_id"].isin(valid_product_ids)
].copy()

movements = movements.loc[
    (movements["quantity"] > 0)
    & (movements["quantity"] % 1 == 0)
].copy()


# ============================================================
# 18. ADD DATE ATTRIBUTES
# ============================================================

sales["sale_date"] = (
    sales["sale_datetime"].dt.date
)

sales["sale_hour"] = (
    sales["sale_datetime"].dt.hour
)

sales["day_of_week"] = (
    sales["sale_datetime"].dt.day_name()
)


# ============================================================
# 19. SELECT FINAL PRODUCT MASTER COLUMNS
# ============================================================

products_final = products[
    [
        "product_id",
        "product_name",
        "category",
        "subcategory",
        "unit_price_kes",
        "demo_unit_price_kes",
        "price_status",
        "price_source",
    ]
].copy()


# ============================================================
# 20. SELECT FINAL SALES COLUMNS
# ============================================================

sales_final = sales[
    [
        "transaction_id",
        "sale_datetime",
        "sale_date",
        "sale_hour",
        "day_of_week",
        "product_id",
        "product_name",
        "category",
        "subcategory",
        "quantity",
        "unit_price_kes",
        "revenue_kes",
        "payment_method",
        "price_source",
    ]
].copy()


# ============================================================
# 21. SELECT FINAL INVENTORY COLUMNS
# ============================================================

inventory_final = inventory[
    [
        "snapshot_date",
        "product_id",
        "opening_stock",
        "purchases",
        "units_sold",
        "wastage",
        "expected_closing_stock",
        "physical_closing_stock",
        "stockout_flag",
    ]
].copy()


# ============================================================
# 22. SELECT FINAL MOVEMENT COLUMNS
# ============================================================

movements_final = movements[
    [
        "movement_id",
        "movement_date",
        "product_id",
        "movement_type",
        "quantity",
    ]
].copy()


# ============================================================
# 23. FINAL ASSERTIONS
# ============================================================

if sales_final.empty:
    raise ValueError("No valid sales rows remain.")

if products_final["product_id"].duplicated().any():
    raise ValueError("Duplicate product IDs in final product master.")

if sales_final["product_id"].isna().any():
    raise ValueError("Missing product IDs in final sales data.")

if not sales_final["product_id"].isin(
    products_final["product_id"]
).all():
    raise ValueError("Orphan product IDs in final sales data.")

if (sales_final["quantity"] <= 0).any():
    raise ValueError("Invalid sales quantities remain.")

if (sales_final["unit_price_kes"] <= 0).any():
    raise ValueError("Invalid sales prices remain.")

if not np.allclose(
    sales_final["revenue_kes"],
    sales_final["quantity"] * sales_final["unit_price_kes"],
    atol=0.01,
):
    raise ValueError("Revenue reconciliation failed.")


# ============================================================
# 24. SAVE PROCESSED DATASETS
# ============================================================

products_final.to_csv(
    PROCESSED / "products.csv",
    index=False
)

sales_final.to_csv(
    PROCESSED / "sales.csv",
    index=False
)

inventory_final.to_csv(
    PROCESSED / "inventory.csv",
    index=False
)

movements_final.to_csv(
    PROCESSED / "stock_movements.csv",
    index=False
)


# ============================================================
# 25. GENERATE QUALITY REPORT
# ============================================================

quality_report = {
    "dataset_type": "Synthetic demonstration data",
    "raw_sales_rows": int(raw_sales_rows),
    "clean_sales_rows": int(len(sales_final)),
    "exact_duplicate_sales_rows": int(raw_duplicate_sales),
    "raw_missing_payment_rows": int(raw_missing_payment),
    "raw_invalid_quantity_rows": int(raw_invalid_quantity),
    "raw_missing_date_rows": int(raw_missing_date),
    "raw_missing_transaction_id_rows": int(
        raw_missing_transaction_id
    ),
    "unknown_product_rows_removed": int(
        unknown_product_count
    ),
    "revenue_mismatch_rows_detected": int(
        revenue_mismatch_count
    ),
    "clean_unique_transactions": int(
        sales_final["transaction_id"].nunique()
    ),
    "clean_product_count": int(
        products_final["product_id"].nunique()
    ),
    "clean_inventory_rows": int(
        len(inventory_final)
    ),
    "clean_stock_movement_rows": int(
        len(movements_final)
    ),
    "clean_sales_revenue_kes": float(
        sales_final["revenue_kes"].sum()
    ),
}

with open(
    DOCUMENTATION / "data_quality_report.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        quality_report,
        file,
        indent=4
    )

print("=" * 60)
print("VALIDATION AND CLEANING COMPLETE")
print("=" * 60)

for key, value in quality_report.items():
    print(f"{key}: {value}")

print(f"\nProcessed files saved to: {PROCESSED}")



