"""Head-to-head v4 (Poisson FE, top-500) vs v9 (MMM) comparison.
Reports: category-level Pearson + Spearman correlation; sign agreement;
median |ε| ratio; per-item agreement on the v4-coverage subset."""
import pandas as pd
import numpy as np

v4_cat = pd.read_csv("model_outputs/v4_cat.csv").set_index("main_category")
v9_cat = pd.read_csv("model_outputs/v9_cat.csv").set_index("main_category")
v4_item = pd.read_csv("model_outputs/v4_item.csv")
v9_item = pd.read_csv("model_outputs/v9_item.csv")

# Category-level join
cat = v4_cat[["elasticity"]].rename(columns={"elasticity": "v4"}).join(
    v9_cat[["elasticity"]].rename(columns={"elasticity": "v9"}), how="inner"
)
print(f"Categories overlapping: {len(cat)} / {len(v4_cat)} v4, {len(v9_cat)} v9")
print()
print("Per-category comparison:")
print(cat.assign(diff=cat.v4 - cat.v9, ratio_abs=cat.v4.abs()/cat.v9.abs())
       .round(3).sort_values("v9"))
print()
print(f"Pearson corr v4 vs v9 cat eps: {cat.v4.corr(cat.v9):.3f}")
print(f"Spearman corr (rank order):   {cat.v4.corr(cat.v9, method='spearman'):.3f}")
print(f"Both negative: {((cat.v4<0) & (cat.v9<0)).sum()} / {len(cat)}")
print(f"v4 median |eps|: {cat.v4.abs().median():.3f}")
print(f"v9 median |eps|: {cat.v9.abs().median():.3f}")
print(f"v4 / v9 median |eps| ratio: {cat.v4.abs().median()/cat.v9.abs().median():.2f}x")

# Per-item on v4's 500-item coverage
item = v4_item.merge(v9_item, on="item_key", suffixes=("_v4","_v9"))
print()
print(f"Per-item overlap: {len(item)} items")
print(f"Pearson corr per-item eps: {item.elasticity_v4.corr(item.elasticity_v9):.3f}")
print(f"Spearman (rank order):    {item.elasticity_v4.corr(item.elasticity_v9, method='spearman'):.3f}")
print(f"Both negative: {((item.elasticity_v4<0) & (item.elasticity_v9<0)).sum()} / {len(item)}")
print(f"v4 median |eps|: {item.elasticity_v4.abs().median():.3f}")
print(f"v9 median |eps|: {item.elasticity_v9.abs().median():.3f}")
