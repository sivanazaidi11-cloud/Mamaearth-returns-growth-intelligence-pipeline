"""
Part 2 — Cleaning, EDA and verified findings for the Mamaearth project.

Run from repository root:
    python analysis/clean_and_eda.py

The script never edits the source CSVs. It creates a cleaned in-memory
DataFrame, computes verified metrics, and writes narrator/findings.json.
"""

from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
NARRATOR_DIR = ROOT / "narrator"


def load_source_data():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    orders = pd.read_csv(DATA_DIR / "orders.csv")
    return customers, products, orders


def clean_orders(orders: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = orders.copy()

    # Standardize data types.
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["discount_pct"] = pd.to_numeric(df["discount_pct"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["returned"] = pd.to_numeric(df["returned"], errors="coerce")

    # Standardize payment-method labels without changing the source CSV.
    df["payment_method"] = (
        df["payment_method"].astype("string").str.strip().str.upper()
    )

    # Blank discount and rating are missing, not zero.
    missing_discount = int(df["discount_pct"].isna().sum())
    missing_rating = int(df["rating"].isna().sum())

    # Remove exact duplicate business rows. order_id is excluded because
    # O0176-O0180 intentionally repeat earlier orders with new IDs.
    business_cols = [
        "customer_id", "product_id", "order_date", "quantity",
        "discount_pct", "payment_method", "rating", "returned"
    ]
    duplicate_mask = df.duplicated(subset=business_cols, keep="first")
    duplicate_order_ids = df.loc[duplicate_mask, "order_id"].tolist()
    df = df.loc[~duplicate_mask].copy()

    # Transparent imputation rule: median of the non-missing values.
    discount_median = float(df["discount_pct"].median())
    rating_median = float(df["rating"].median())
    df["discount_pct"] = df["discount_pct"].fillna(discount_median)
    df["rating"] = df["rating"].fillna(rating_median)

    return df, {
        "source_order_rows": int(len(orders)),
        "duplicate_rows_removed": int(duplicate_mask.sum()),
        "duplicate_order_ids_removed": duplicate_order_ids,
        "missing_discount_pct_before_imputation": missing_discount,
        "missing_rating_before_imputation": missing_rating,
        "discount_imputation_value": discount_median,
        "rating_imputation_value": rating_median,
    }


def build_analysis_frame(customers, products, orders):
    df = orders.merge(
        customers[["customer_id", "city", "city_tier", "acquisition_source"]],
        on="customer_id", how="left"
    ).merge(
        products[["product_id", "product_name", "category", "price"]],
        on="product_id", how="left"
    )

    df["gross_value"] = df["quantity"] * df["price"]
    df["discount_amount"] = df["gross_value"] * df["discount_pct"] / 100.0
    df["net_revenue"] = df["gross_value"] - df["discount_amount"]
    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    return df


def build_findings(df, cleaning_meta):
    payment = (
        df.groupby("payment_method")
        .agg(orders=("order_id", "count"),
             returned_orders=("returned", "sum"),
             net_revenue=("net_revenue", "sum"))
        .reset_index()
    )
    payment["return_rate_pct"] = payment["returned_orders"] / payment["orders"] * 100
    payment = payment.sort_values("return_rate_pct", ascending=False)

    monthly = (
        df.groupby("month")
        .agg(orders=("order_id", "count"),
             returned_orders=("returned", "sum"),
             net_revenue=("net_revenue", "sum"))
        .reset_index()
        .sort_values("month")
    )
    monthly["return_rate_pct"] = monthly["returned_orders"] / monthly["orders"] * 100

    category = (
        df.groupby("category")
        .agg(orders=("order_id", "count"),
             returned_orders=("returned", "sum"),
             net_revenue=("net_revenue", "sum"))
        .reset_index()
    )
    category["return_rate_pct"] = category["returned_orders"] / category["orders"] * 100
    category = category.sort_values("net_revenue", ascending=False)

    city_tier = (
        df.groupby("city_tier")
        .agg(orders=("order_id", "count"),
             returned_orders=("returned", "sum"),
             net_revenue=("net_revenue", "sum"))
        .reset_index()
    )
    city_tier["return_rate_pct"] = city_tier["returned_orders"] / city_tier["orders"] * 100

    acquisition = (
        df.groupby("acquisition_source")
        .agg(orders=("order_id", "count"),
             customers=("customer_id", "nunique"),
             returned_orders=("returned", "sum"),
             net_revenue=("net_revenue", "sum"))
        .reset_index()
    )
    acquisition["return_rate_pct"] = acquisition["returned_orders"] / acquisition["orders"] * 100

    product = (
        df.groupby(["product_id", "product_name", "category"])
        .agg(orders=("order_id", "count"),
             returned_orders=("returned", "sum"),
             net_revenue=("net_revenue", "sum"))
        .reset_index()
    )
    product["return_rate_pct"] = product["returned_orders"] / product["orders"] * 100
    product = product.sort_values(["return_rate_pct", "orders"], ascending=[False, False])

    total_orders = len(df)
    returned_orders = int(df["returned"].sum())
    return_rate = returned_orders / total_orders * 100
    total_revenue = float(df["net_revenue"].sum())

    top_product = product.iloc[0]
    top_category = category.iloc[0]
    top_payment = payment.iloc[0]
    best_payment = payment.sort_values("return_rate_pct").iloc[0]

    findings = {
        "dataset": {
            "customers": int(len(df["customer_id"].unique())),
            "products": int(len(df["product_id"].unique())),
            "source_orders": cleaning_meta["source_order_rows"],
            "cleaned_orders": total_orders,
            "duplicate_rows_removed": cleaning_meta["duplicate_rows_removed"],
        },
        "cleaning": cleaning_meta,
        "overall": {
            "net_revenue_inr": round(total_revenue, 2),
            "returned_orders": returned_orders,
            "return_rate_pct": round(return_rate, 2),
            "average_order_value_inr": round(total_revenue / total_orders, 2),
        },
        "monthly_revenue": [
            {
                "month": r["month"],
                "orders": int(r["orders"]),
                "net_revenue_inr": round(float(r["net_revenue"]), 2),
                "returned_orders": int(r["returned_orders"]),
                "return_rate_pct": round(float(r["return_rate_pct"]), 2),
            }
            for _, r in monthly.iterrows()
        ],
        "return_rate_by_payment": [
            {
                "payment_method": r["payment_method"],
                "orders": int(r["orders"]),
                "returned_orders": int(r["returned_orders"]),
                "return_rate_pct": round(float(r["return_rate_pct"]), 2),
                "net_revenue_inr": round(float(r["net_revenue"]), 2),
            }
            for _, r in payment.iterrows()
        ],
        "category_performance": [
            {
                "category": r["category"],
                "orders": int(r["orders"]),
                "returned_orders": int(r["returned_orders"]),
                "return_rate_pct": round(float(r["return_rate_pct"]), 2),
                "net_revenue_inr": round(float(r["net_revenue"]), 2),
            }
            for _, r in category.iterrows()
        ],
        "city_tier_performance": [
            {
                "city_tier": int(r["city_tier"]),
                "orders": int(r["orders"]),
                "returned_orders": int(r["returned_orders"]),
                "return_rate_pct": round(float(r["return_rate_pct"]), 2),
                "net_revenue_inr": round(float(r["net_revenue"]), 2),
            }
            for _, r in city_tier.iterrows()
        ],
        "acquisition_performance": [
            {
                "acquisition_source": r["acquisition_source"],
                "orders": int(r["orders"]),
                "customers": int(r["customers"]),
                "returned_orders": int(r["returned_orders"]),
                "return_rate_pct": round(float(r["return_rate_pct"]), 2),
                "net_revenue_inr": round(float(r["net_revenue"]), 2),
            }
            for _, r in acquisition.iterrows()
        ],
        "high_return_products": [
            {
                "product_id": r["product_id"],
                "product_name": r["product_name"],
                "category": r["category"],
                "orders": int(r["orders"]),
                "returned_orders": int(r["returned_orders"]),
                "return_rate_pct": round(float(r["return_rate_pct"]), 2),
                "net_revenue_inr": round(float(r["net_revenue"]), 2),
            }
            for _, r in product.head(5).iterrows()
        ],
        "verified_observations": {
            "highest_return_payment_method": top_payment["payment_method"],
            "highest_return_payment_rate_pct": round(float(top_payment["return_rate_pct"]), 2),
            "lowest_return_payment_method": best_payment["payment_method"],
            "lowest_return_payment_rate_pct": round(float(best_payment["return_rate_pct"]), 2),
            "highest_revenue_category": top_category["category"],
            "highest_revenue_category_inr": round(float(top_category["net_revenue"]), 2),
            "highest_return_product": top_product["product_name"],
            "highest_return_product_rate_pct": round(float(top_product["return_rate_pct"]), 2),
        },
    }
    return findings


def main():
    customers, products, raw_orders = load_source_data()
    clean_orders_df, cleaning_meta = clean_orders(raw_orders)
    df = build_analysis_frame(customers, products, clean_orders_df)
    findings = build_findings(df, cleaning_meta)

    NARRATOR_DIR.mkdir(exist_ok=True)
    output = NARRATOR_DIR / "findings.json"
    output.write_text(json.dumps(findings, indent=2), encoding="utf-8")

    print("Cleaning and EDA complete.")
    print(f"Source orders: {len(raw_orders)}")
    print(f"Duplicate rows removed: {cleaning_meta['duplicate_rows_removed']}")
    print(f"Cleaned orders: {len(df)}")
    print(f"Net revenue: ₹{findings['overall']['net_revenue_inr']:,.2f}")
    print(f"Return rate: {findings['overall']['return_rate_pct']:.2f}%")
    print(f"Verified findings written to: {output}")


if __name__ == "__main__":
    main()
