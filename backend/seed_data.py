import os
import sys
import pandas as pd
from sqlalchemy import text

CSV_PATH = "C:/Users/LENOVO/source/repos/specialized-projects(2)/data/SampleSuperstore.csv"

def main():
    if not os.path.exists(CSV_PATH):
        print("CSV not found:", CSV_PATH)
        sys.exit(1)

    try:
        # Import DB helpers from the package root (backend container exposes these at /app)
        from db import get_dataset_by_name, create_dataset, insert_orders, ENGINE
    except Exception as e:
        print("Failed to import db helpers:", e)
        sys.exit(2)

    df = pd.read_csv(CSV_PATH, encoding="latin-1")
    normalized = df.rename(
        columns={
            "Order ID": "order_id",
            "Order Date": "order_date",
            "Customer ID": "customer_id",
            "Customer Name": "customer_name",
            "Region": "region",
            "Category": "category",
            "Sales": "sales",
            "Profit": "profit",
            "Discount": "discount",
        }
    )

    ds = get_dataset_by_name("default_sample_superstore")
    if ds:
        dataset_id = ds["id"]
        print("Found dataset:", dataset_id)
    else:
        dataset_id = create_dataset(
            name="default_sample_superstore",
            source_type="seed",
            created_by="system",
            is_active=True,
        )
        print("Created dataset:", dataset_id)

    # Check existing orders count for the dataset
    with ENGINE.begin() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM orders_fact WHERE dataset_id = CAST(:id AS UUID)"),
            {"id": dataset_id},
        ).scalar()

    print("Existing orders count:", count)
    if count and int(count) > 0:
        print("No action: orders already present")
        return

    # Insert orders
    try:
        inserted = insert_orders(dataset_id, normalized)
        print("Inserted records:", inserted)
    except Exception as e:
        print("Failed to insert orders:", e)
        sys.exit(3)


if __name__ == "__main__":
    main()
