# Mamaearth Returns & Growth Intelligence — Part 2

## Python/Pandas Data Wrangling & EDA

This Part 2 pipeline is independent of the SQLite database. It reads the raw CSV files directly from `data/` and can be run independently of Part 1.

### Run order

From the repository root:

```bash
python analysis/clean_and_eda.py
python analysis/visualize.py
```

### Dependencies

```bash
pip install pandas numpy matplotlib
```

### Key acceptance checks

- Raw orders shape: `(180, 9)`
- Payment methods standardize to `CARD`, `COD`, `UPI`
- Five duplicates removed: `O0176`–`O0180`
- Cleaned orders shape: `(175, 9)`
- Missing discounts: 12; filled with `0`
- Missing ratings: 15; median `3.0`
- Cleaned order value total: `97358.30`
- Duplicate-row value delta: `2501.90`
- Quantity outliers: `O0011` and `O0098`
- COD return-rate hypothesis: Confirmed
- Highest-risk segment: COD + Tier-2 at `54.5%`
- All six pairwise correlations: negligible
- Discount vs returned hypothesis: Busted
- Outlier-corrected peak month: March 2026

The source CSVs are not manually cleaned; all transformations happen in `clean_and_eda.py`.
