"""
Part 2 — Required visualizations.

Run from repository root:
    python analysis/clean_and_eda.py
    python analysis/visualize.py
"""

from pathlib import Path
import sys
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from clean_and_eda import load_source_data, clean_orders, build_analysis_frame


def main():
    customers, products, raw_orders = load_source_data()
    clean_orders_df, _ = clean_orders(raw_orders)
    df = build_analysis_frame(customers, products, clean_orders_df)

    out = ROOT / "visualizations"
    out.mkdir(exist_ok=True)

    payment = (
        df.groupby("payment_method")
        .agg(orders=("order_id", "count"), returned=("returned", "sum"))
    )
    payment["return_rate_pct"] = payment["returned"] / payment["orders"] * 100
    payment = payment.sort_values("return_rate_pct", ascending=False)

    plt.figure(figsize=(8, 5))
    plt.bar(payment.index, payment["return_rate_pct"])
    plt.ylabel("Return Rate (%)")
    plt.xlabel("Payment Method")
    plt.title("Return Rate by Payment Method")
    plt.tight_layout()
    plt.savefig(out / "return_rate_by_payment.png", dpi=160)
    plt.close()

    monthly = df.groupby("month")["net_revenue"].sum().sort_index()

    plt.figure(figsize=(9, 5))
    plt.plot(monthly.index, monthly.values, marker="o")
    plt.ylabel("Net Revenue (INR)")
    plt.xlabel("Month")
    plt.title("Monthly Net Revenue Trend")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(out / "monthly_revenue_trend.png", dpi=160)
    plt.close()

    print("Created:")
    print(out / "return_rate_by_payment.png")
    print(out / "monthly_revenue_trend.png")


if __name__ == "__main__":
    main()
