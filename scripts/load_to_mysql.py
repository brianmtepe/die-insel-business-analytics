from pathlib import Path
import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# ============================================================
# DIE INSEL — PYTHON TO MYSQL DATA LOADER
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"

DATABASE = os.getenv("MYSQL_DATABASE", "die_insel_analytics")

FILES = {
    "dim_product": "products.csv",
    "fact_inventory": "inventory.csv",
    "fact_sales": "sales.csv",
    "fact_stock_movements": "stock_movements.csv",
}

required = [
    "MYSQL_HOST",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
]

missing = [key for key in required if not os.getenv(key)]

if missing:
    sys.exit(
        "Missing environment variables: "
        + ", ".join(missing)
        + ". Set them in the VS Code terminal and retry."
    )

# ============================================================
# 1. CONNECT TO MYSQL
# ============================================================

connection_url = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["MYSQL_USER"],
    password=os.environ["MYSQL_PASSWORD"],
    host=os.environ["MYSQL_HOST"],
    port=int(os.getenv("MYSQL_PORT", "3306")),
    database=DATABASE,
)

engine = create_engine(
    connection_url,
    pool_pre_ping=True,
)

try:
    with engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT DATABASE(), VERSION()"
            )
        ).one()

        print(f"Connected database: {result[0]}")
        print(f"MySQL version: {result[1]}")

    # ========================================================
    # 2. LOAD AND IMPORT CLEANED DATASETS
    # ========================================================

    import_results = []

    for table, filename in FILES.items():
        path = DATA_DIR / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Required cleaned CSV not found: {path}"
            )

        df = pd.read_csv(path)

        if df.empty:
            raise ValueError(
                f"{filename} has no records. Import stopped."
            )

        # Standardize database column names.
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(r"[^a-z0-9_]", "_", regex=True)
            .str.replace(r"_+", "_", regex=True)
            .str.strip("_")
        )

        if df.columns.duplicated().any():
            raise ValueError(
                f"{filename} contains duplicate column names "
                "after standardization."
            )

        if any(not col for col in df.columns):
            raise ValueError(
                f"{filename} contains an invalid column name."
            )

        # Reject infinite numeric values.
        numeric = df.select_dtypes(include="number")

        if not numeric.empty:
            import numpy as np

            if np.isinf(numeric.to_numpy()).any():
                raise ValueError(
                    f"{filename} contains infinite numeric values."
                )

        # Convert empty strings to SQL NULL.
        df = df.replace(r"^\s*$", None, regex=True)

        # Load into the matching staging table.
        # Replace is deliberate for this reproducible demo import.
        df.to_sql(
            name=f"stg_{table}",
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=500,
            method="multi",
        )

        import_results.append({
            "table": f"stg_{table}",
            "rows_imported": len(df),
            "columns": len(df.columns),
            "source": filename,
        })

        print(
            f"Loaded {filename}: "
            f"{len(df):,} rows, "
            f"{len(df.columns)} columns"
        )

    # ========================================================
    # 3. VERIFY DATABASE ROW COUNTS
    # ========================================================

    print("\nDATABASE IMPORT SUMMARY")

    with engine.connect() as connection:
        for item in import_results:
            table = item["table"]

            count = connection.execute(
                text(f"SELECT COUNT(*) FROM `{table}`")
            ).scalar_one()

            print(f"{table}: {count:,} records")

            if count != item["rows_imported"]:
                raise RuntimeError(
                    f"Row-count mismatch for {table}"
                )

    print("\nSTATUS: All four staging tables loaded successfully.")

except Exception as exc:
    print(f"\nIMPORT FAILED: {exc}")
    raise

finally:
    engine.dispose()