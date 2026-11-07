from pathlib import Path
import numpy as np
import pandas as pd


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

REFERENCE_DIR = ROOT / "data" / "reference"
GENERATED_DIR = ROOT / "data" / "generated"

MENU_PATH = REFERENCE_DIR / "menu_master.csv"

GENERATED_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
DAYS = 90
TARGET_TRANSACTIONS = 2000

rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# 2. LOAD PRODUCT MASTER
# ============================================================

products = pd.read_csv(MENU_PATH)

products["product_id"] = products["product_id"].astype(str)

products["unit_price_kes"] = pd.to_numeric(
    products["unit_price_kes"],
    errors="coerce"
)

if products["product_id"].duplicated().any():
    raise ValueError("Duplicate product IDs found in menu master.")

if products["product_name"].duplicated().any():
    raise ValueError("Duplicate product names found in menu master.")

if products["product_id"].isna().any():
    raise ValueError("Missing product IDs found.")

if products["product_name"].isna().any():
    raise ValueError("Missing product names found.")


# ============================================================
# 3. CREATE DEMONSTRATION PRICES
# ============================================================

# These are assumptions for the synthetic demonstration only.
# They are NOT confirmed restaurant prices.

demo_price_overrides = {
    "Samosa vegetable": 70,
    "Samosa beef": 70,
    "Coca-Cola": 100,
    "Coke Zero": 100,
    "Krest Bitter Lemon": 100,
    "Sprite": 100,
    "Fanta Blackcurrant": 100,
    "Fanta Orange": 100,
    "Fanta Pineapple": 100,
    "Whole fish": 850,
}

products["demo_unit_price_kes"] = products["unit_price_kes"]

for product_name, assumed_price in demo_price_overrides.items():
    mask = products["product_name"].eq(product_name)

    products.loc[mask, "demo_unit_price_kes"] = assumed_price

products["price_source"] = np.where(
    products["unit_price_kes"].notna(),
    "Menu-listed reference",
    "Synthetic demonstration assumption"
)

products["demo_unit_price_kes"] = pd.to_numeric(
    products["demo_unit_price_kes"],
    errors="coerce"
)

if products["demo_unit_price_kes"].isna().any():
    missing = products.loc[
        products["demo_unit_price_kes"].isna(),
        "product_name"
    ].tolist()

    raise ValueError(
        f"Missing demonstration prices for products: {missing}"
    )

if (products["demo_unit_price_kes"] <= 0).any():
    raise ValueError("All demonstration prices must be positive.")


# ============================================================
# 4. SET UP SYNTHETIC DATE RANGE
# ============================================================

end_date = pd.Timestamp.today().normalize()

start_date = end_date - pd.Timedelta(days=DAYS - 1)

dates = pd.date_range(
    start=start_date,
    end=end_date,
    freq="D"
)


# ============================================================
# 5. DEFINE PRODUCT SELECTION WEIGHTS
# ============================================================

# Weights are assumptions for generating demonstration data.
# They are not measured demand estimates.

product_weights = {}

for _, row in products.iterrows():

    name = row["product_name"]
    category = row["category"]
    subcategory = row["subcategory"]

    if name in [
        "Chips",
        "Tusker Lager",
        "Soda",
        "Water Small",
        "Pilsner",
        "Sausage",
    ]:
        weight = 5.0

    elif category == "Beverage":
        weight = 3.0

    elif subcategory in ["Chicken", "Snacks and sides"]:
        weight = 2.5

    else:
        weight = 1.0

    product_weights[row["product_id"]] = weight


# ============================================================
# 6. DEFINE TRANSACTION VOLUME BY DAY
# ============================================================

# Synthetic daily volumes:
# weekdays generally lower, weekends generally higher.

transaction_ids = [
    f"DEMO-TXN-{i:06d}"
    for i in range(1, TARGET_TRANSACTIONS + 1)
]

transactions_per_day = rng.multinomial(
    TARGET_TRANSACTIONS,
    np.repeat(1 / len(dates), len(dates))
)

# Give weekends a modest synthetic uplift by reallocating
# the daily transaction probabilities.

weekday_weights = np.array([
    1.0 if date.dayofweek < 4 else 1.5
    for date in dates
], dtype=float)

weekday_probabilities = weekday_weights / weekday_weights.sum()

transactions_per_day = rng.multinomial(
    TARGET_TRANSACTIONS,
    weekday_probabilities
)


# ============================================================
# 7. GENERATE SALES TRANSACTION LINES
# ============================================================

sales_records = []

transaction_counter = 1

payment_methods = [
    "M-Pesa",
    "Cash",
    "Card",
]

payment_probabilities = [
    0.65,
    0.30,
    0.05,
]

for date, daily_transaction_count in zip(
    dates,
    transactions_per_day
):

    for _ in range(daily_transaction_count):

        transaction_id = (
            f"DEMO-TXN-{transaction_counter:06d}"
        )

        transaction_counter += 1

        hour = int(
            rng.choice(
                [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
                p=[
                    0.01, 0.02, 0.04, 0.07, 0.09, 0.08,
                    0.06, 0.06, 0.08, 0.12, 0.13, 0.12, 0.12
                ]
            )
        )

        minute = int(rng.integers(0, 60))

        sale_datetime = (
            date
            + pd.Timedelta(hours=hour, minutes=minute)
        )

        payment_method = rng.choice(
            payment_methods,
            p=payment_probabilities
        )

        # One transaction can contain multiple distinct products.
        number_of_products = int(
            rng.choice([1, 2, 3, 4, 5], p=[0.30, 0.34, 0.22, 0.10, 0.04])
        )

        selected_products = products.sample(
            n=number_of_products,
            replace=False,
            weights=products["product_id"].map(
                product_weights
            ),
            random_state=int(rng.integers(0, 1_000_000))
        )

        for _, product in selected_products.iterrows():

            quantity = int(
                rng.choice(
                    [1, 2, 3, 4],
                    p=[0.66, 0.23, 0.08, 0.03]
                )
            )

            unit_price = float(
                product["demo_unit_price_kes"]
            )

            revenue = round(
                quantity * unit_price,
                2
            )

            sales_records.append({
                "transaction_id": transaction_id,
                "sale_datetime": sale_datetime,
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "category": product["category"],
                "quantity": quantity,
                "unit_price_kes": unit_price,
                "revenue_kes": revenue,
                "payment_method": payment_method,
            })


sales_raw = pd.DataFrame(sales_records)


# ============================================================
# 8. GENERATE SYNTHETIC INVENTORY PURCHASE MOVEMENTS
# ============================================================

# Inventory units are illustrative.
# This simplified model uses product units and does not represent
# kitchen ingredient recipes or restaurant procurement records.

movement_records = []

for product_id in products["product_id"]:

    for date in dates:

        if rng.random() < 0.10:

            quantity_purchased = int(
                rng.integers(3, 25)
            )

            movement_records.append({
                "movement_id": (
                    f"MOV-{len(movement_records) + 1:07d}"
                ),
                "movement_date": date,
                "product_id": product_id,
                "movement_type": "Purchase",
                "quantity": quantity_purchased,
            })


movements_raw = pd.DataFrame(
    movement_records,
    columns=[
        "movement_id",
        "movement_date",
        "product_id",
        "movement_type",
        "quantity",
    ]
)


# ============================================================
# 9. GENERATE DAILY INVENTORY SNAPSHOTS
# ============================================================

sales_by_day_product = (
    sales_raw.groupby(
        [
            pd.to_datetime(sales_raw["sale_datetime"]).dt.normalize(),
            "product_id",
        ]
    )["quantity"]
    .sum()
    .to_dict()
)

purchases_by_day_product = {}

if not movements_raw.empty:

    purchases_by_day_product = (
        movements_raw.groupby(
            [
                pd.to_datetime(
                    movements_raw["movement_date"]
                ).dt.normalize(),
                "product_id",
            ]
        )["quantity"]
        .sum()
        .to_dict()
    )


inventory_records = []

for product_id in products["product_id"]:

    opening_stock = int(rng.integers(15, 60))

    for date in dates:

        purchased = purchases_by_day_product.get(
            (date, product_id),
            0
        )

        sold = sales_by_day_product.get(
            (date, product_id),
            0
        )

        opening = opening_stock

        available = opening + purchased

        # In this synthetic model, demand is allowed to exceed
        # available stock. This creates stock-out scenarios.
        sold_from_stock = min(sold, available)

        stockout_flag = sold > available

        expected_closing = max(
            available - sold_from_stock,
            0
        )

        wastage = (
            int(rng.integers(0, 2))
            if rng.random() < 0.02
            else 0
        )

        expected_closing = max(
            expected_closing - wastage,
            0
        )

        # Physical count may differ from expected stock.
        discrepancy = (
            int(rng.choice([-2, -1, 1, 2]))
            if rng.random() < 0.02
            else 0
        )

        physical_closing = max(
            expected_closing + discrepancy,
            0
        )

        inventory_records.append({
            "snapshot_date": date,
            "product_id": product_id,
            "opening_stock": opening,
            "purchases": purchased,
            "units_sold": sold,
            "wastage": wastage,
            "expected_closing_stock": expected_closing,
            "physical_closing_stock": physical_closing,
            "stockout_flag": bool(stockout_flag),
        })

        opening_stock = physical_closing


inventory_raw = pd.DataFrame(inventory_records)


# ============================================================
# 10. INTRODUCE CONTROLLED QUALITY ISSUES
# ============================================================

# These records are intentionally added to test cleaning.
# They are not valid sales records.

if len(sales_raw) >= 5:

    # Duplicate one complete record.
    duplicate_record = sales_raw.iloc[[0]].copy()

    sales_raw = pd.concat(
        [sales_raw, duplicate_record],
        ignore_index=True
    )

    # Add an invalid quantity.
    sales_raw.loc[
        len(sales_raw) - 1,
        "quantity"
    ] = 0

    # Add one row with a missing payment method.
    missing_payment_record = sales_raw.iloc[[1]].copy()

    missing_payment_record["payment_method"] = np.nan

    sales_raw = pd.concat(
        [sales_raw, missing_payment_record],
        ignore_index=True
    )


# ============================================================
# 11. SAVE RAW DEMONSTRATION FILES
# ============================================================

products.to_csv(
    GENERATED_DIR / "demo_products_raw.csv",
    index=False
)

sales_raw.to_csv(
    GENERATED_DIR / "demo_sales_raw.csv",
    index=False
)

movements_raw.to_csv(
    GENERATED_DIR / "demo_stock_movements_raw.csv",
    index=False
)

inventory_raw.to_csv(
    GENERATED_DIR / "demo_inventory_raw.csv",
    index=False
)


# ============================================================
# 12. PRINT GENERATION SUMMARY
# ============================================================

print("=" * 60)
print("SYNTHETIC DATA GENERATION COMPLETE")
print("=" * 60)

print(f"Date range: {start_date.date()} to {end_date.date()}")

print(f"Products: {len(products):,}")

print(
    "Unique transactions:",
    sales_raw["transaction_id"].nunique()
)

print(f"Raw sales lines: {len(sales_raw):,}")

print(f"Inventory snapshots: {len(inventory_raw):,}")

print(f"Stock movements: {len(movements_raw):,}")

print(f"Raw sales revenue: KES {sales_raw['revenue_kes'].sum():,.2f}")

print(f"Output directory: {GENERATED_DIR}")