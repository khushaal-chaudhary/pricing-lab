# Deliverable CSVs — column guide

Two files ship as the headline deliverable:

- **`elasticities_final.csv`** — per-item price elasticities (3,000 rows)
- **`elasticities_by_main_category.csv`** — main-category headline (17 rows)

Both are produced by `finalize.py` and rebuilt automatically whenever the underlying model artefacts in `model_outputs/` change.

---

## `elasticities_final.csv` (3,000 rows × 12 columns)

One row per item. Columns:

| Column | Type | Source | Description |
|---|---|---|---|
| `item_key` | int | masterdata | Item identifier (joins to master + sales + prices). |
| `main_category` | str | masterdata | 17 levels — `im1`…`im20`. |
| `sub_category` | str | masterdata | 81 levels — `sc01`…`sc81`. |
| `brnd` | str | masterdata | 123 brand identifiers. |
| **`elasticity_item`** | float | v6 ridge + v9 fallback (`source` logs which) | **Per-item ε — the headline deliverable. 100% negative.** |
| `source` | str | finalize.py | Which layer produced `elasticity_item` on this row. Values: `item_ridge`, `category_fe_positive_fallback`, `category_fe_low_n`. |
| `n_obs` | int | v6 fit | Number of weekly observations the per-item ridge had to work with. |
| `cat_reg_elasticity` | float | v9 MMM | Category regular-price ε inherited from the item's main_category. |
| `cat_promo_elasticity` | float | v9 MMM | Category promo ε (separate slope for weeks the item was on discount). |
| `cat_se` | float | v9 MMM | Standard error of `cat_reg_elasticity`. |
| **`elasticity_reconciled`** | float | MinT on v9 + sign-fallback | Hierarchically-coherent ε. **100% negative** after sign-fallback. |
| `reconciled_source` | str | finalize.py | Which level produced `elasticity_reconciled`. Values: `item`, `sub_category`, `main_category`, `portfolio`. |

### How `elasticity_item` is built (the blend)

v9 fits ε **per category**, not per item — it doesn't produce 3,000 per-item slopes. So the per-item layer comes from v6 (ridge per-item regression on the same panel as v9). The blend:

| `source` value | Rows | Logic |
|---|---:|---|
| `item_ridge` | 2,693 | v6 ridge converged with ≥ 50 obs and produced a negative slope → use it. |
| `category_fe_positive_fallback` | 283 | v6 ridge produced a *positive* slope (data thinness — not real Veblen behaviour in mass-market furniture) → replace with the item's main_category v9 ε. |
| `category_fe_low_n` | 24 | v6 ridge had < 50 obs to fit on → replace with the item's main_category v9 ε. |

This guarantees `elasticity_item` is 100% negative by construction. The substitution is logged so a reviewer can audit every row.

### How `elasticity_reconciled` is built (MinT + sign-fallback)

MinT reconciliation (Wickramasuriya 2019) projects independently-fit ε at item / sub_category / main_category / portfolio onto a coherent set — the sales-weighted average of item ε within a category exactly equals the category ε after reconciliation.

**Caveat:** MinT minimises trace variance with **no sign constraint**. Raw reconciled output has 282 positive item-ε (noisy children survive reconciliation because the reconciled value lies between a noisy positive raw estimate and a negative parent without always crossing zero). `finalize.py` applies a sign-fallback ladder at write time:

```
if item-level reconciled ε < 0  →  use it                          (2,703 rows)
elif sub_category reconciled ε < 0  →  use sub_cat value           (287 rows)
elif main_category reconciled ε < 0  →  use main_cat value         (10 rows)
else  →  use portfolio reconciled ε (always negative)              (0 rows in current data)
```

After this pass: 3,000 / 3,000 negative. `reconciled_source` records which level each row came from. The same logic runs at read-time inside the dashboard simulator (`app/lib.py:get_eps`).

### Distribution

```
elasticity_item            median = -0.573    5th–95th pct = [-1.42, -0.11]
elasticity_reconciled      median = -0.570    5th–95th pct = [-1.42, -0.10]
```

The two columns agree closely — reconciliation does not materially shift the marginal distribution; it imposes hierarchical coherence on top.

---

## `elasticities_by_main_category.csv` (17 rows × 5 columns)

Pure v9 output — no blend, no reconciliation. This is the headline number quoted in the slides and the dashboard simulator's `main_category` level.

| Column | Type | Description |
|---|---|---|
| `main_category` | str | `im1`…`im20` (17 distinct values). |
| `elasticity` | float | Regular-price ε from v9 — separate slope from `promo_elasticity`. **100% negative.** |
| `promo_elasticity` | float | Promo-week ε from v9 (interaction term: `promo × log_price × main_category`). |
| `se` | float | Analytic standard error of `elasticity` from the OLS fit. |
| `n_items` | int | Number of items in this main_category. |

### Distribution

```
elasticity        median = -0.583    range = [-0.754, -0.348]
promo_elasticity  median = -0.960    range = [-1.776, -0.302]
```

11 of 17 categories have promo ε ≥ |1| (elastic on promo).

---

## Recommended model — v9 MMM-style decomposition

Both files derive from v9 (with v6 as the per-item layer in `elasticities_final.csv`). v9 was selected over v4 / v7 / v10 / v11 on a composite metric weighting holdout R², face validity (% categories ε < 0), portfolio coverage, and bootstrap-CI stability. See `leaderboard.md` and the `notebook.ipynb` §15 for the full comparison.

**Honest range across credible models:** `[-2.30, -0.58]`.
- v9 (this file) sits at the inelastic end on the full 3,000-item panel.
- v4 Poisson on the top-500 items lands at -2.30 (inside Bijmolt 2005 durables range).
- v10 DML and v11 Tweedie confirm v9's sign and bound the magnitude from below.

The dashboard surfaces both numbers — `elasticities_final.csv` is the deployable artefact; v4's magnitude is cited in the model-comparison view.
