from pathlib import Path
import matplotlib.pyplot as plt
from clean_and_eda import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "visualizations"
OUT.mkdir(parents=True, exist_ok=True)

results = run_pipeline(verbose=True)
payment = results["payment_return"].sort_values("return_rate_pct", ascending=False)

# 1. Return rate by payment method
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(payment.index, payment["return_rate_pct"])
for bar, value in zip(bars, payment["return_rate_pct"]):
    ax.text(bar.get_x() + bar.get_width()/2, value + 0.8, f"{value:.1f}%", ha="center")
ax.set_xlabel("Payment Method")
ax.set_ylabel("Return Rate (%)")
ax.set_title("COD Returns at 44.4% — 3x Card")
fig.tight_layout()
fig.savefig(OUT / "return_rate_by_payment.png", dpi=150)
plt.close(fig)

# 2. Outlier-corrected monthly revenue trend
monthly = results["monthly_excluding"]
peak_month = monthly.idxmax()
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(monthly.index, monthly.values, marker="o")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (₹)")
ax.set_title(f"Outlier-Corrected Monthly Revenue — Peak: {peak_month}")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout()
fig.savefig(OUT / "monthly_revenue_trend.png", dpi=150)
plt.close(fig)

print("\n=== TASK 11: VISUALIZATIONS ===")
print(f"Saved: {OUT / 'return_rate_by_payment.png'}")
print(f"Saved: {OUT / 'monthly_revenue_trend.png'}")
