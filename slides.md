# home24 — Price Elasticity Analysis (5 slides)

---

## Slide 1 — Question & deliverable

**Question:** How responsive is item demand to price at home24, by item and main category?

**Data:** 3,000 items × 8 shops × 1,080 days (2018-01-01 → 2020-12-17). 5 source tables joined to an item-shop-week panel (1.9M rows after sellability filter).

**Deliverable:** per-item elasticities (`elasticities_final.csv`, 3,000 rows) and main-category averages (17 categories), produced by an MMM-style decomposition that isolates price from baseline / trend / seasonality / event variance.

---

## Slide 2 — Methodology (chosen: v9 MMM-style decomposition)

I borrowed the marketing-mix-modeling frame from my consulting work: decompose `log(sales+1)` into baseline + trend + seasonality + events + **price**, so the price coefficient is what's left after the other demand drivers are accounted for.

```
log(q_ist) = α_(i,s)                            # item-shop baseline
           + δ · weeks_since_start              # linear trend
           + Σ_k θ_k · Fourier_k(week_of_year)  # K=4 annual seasonality
           + Σ_h ψ_h · holiday_h(date)          # BFCM, Xmas, NYE, Easter, COVID
           + β_c^reg  · log(p) · (1 − promo)    # category regular ε
           + β_c^prom · log(p) · promo          # category promo ε
           + γ · delivery_days + ε_ist
```

Within-(item, shop) demeaning absorbs the baseline; per-item ε is layered via ridge regression on the same panel (2,976 of 3,000 items) with category fallback for the remaining 24 (0.8%). Fit in `statsmodels.OLS` — fully transparent, no MCMC needed for this scale.

---

## Slide 3 — Why this method beats the alternatives we tried

| Property | v9 MMM | v5 FE-panel | LightGBM | Naive Δlog/Δlog |
|---|:---:|:---:|:---:|:---:|
| Isolates price from seasonality/events | ✅ | ❌ | ⚠ | ❌ |
| Variance decomposition for VP | ✅ | ❌ | ❌ | ❌ |
| Per-category ε with CI | ✅ | ✅ | ⚠ | ❌ |
| Splits promo / regular | ✅ | ✅ | ❌ | ❌ |
| Actionable per-item ε | ✅ | ✅ | ❌ (flat regions) | ❌ |
| Holdout R² | **0.56** | 0.51 | 0.54 | n/a |
| % categories ε<0 | **100%** | 100% | 100% | 0% |
| **Composite leaderboard** | **0.820** | 0.800 | 0.804 | 0.247 |

**Variance share across the weekly panel:** events 38%, seasonality 33%, trend 25%, **price 4%**. The headline business insight: most of home24's weekly demand swing is calendar/event-driven, not price-driven — meaning price changes work *with* the seasonal/event cycle, not against it.

---

## Slide 4 — Results by main category + literature benchmark

Regular-price elasticities (top 10 main categories, sorted most-to-least elastic). All 17 categories show statistically significant negative ε. Median |ε| ≈ 0.58 — demand is **moderately inelastic**.

| Category | n_items | Regular ε | Promo ε | Bijmolt 2005 durables range |
|---|---:|---:|---:|:---:|
| im6  | 490 | -0.75 | -1.11 | -1.0 to -2.0 |
| im2  | 122 | -0.74 | -1.03 | -1.0 to -2.0 |
| im16 | 221 | -0.73 | -1.13 | -1.0 to -2.0 |
| im12 |  27 | -0.72 | -1.78 | -1.0 to -2.0 |
| im9  |  95 | -0.70 | -0.30 | -1.0 to -2.0 |
| im17 | 234 | -0.58 | -0.96 | -1.0 to -2.0 |
| im14 (largest) | 629 | -0.45 | -0.51 | -1.0 to -2.0 |
| im19 |  75 | -0.35 | -0.47 | -1.0 to -2.0 |

**Why our ε sits at the inelastic end of the literature:**
- *Online-only retailer at the time* — no competing showroom; switching cost is higher than supermarket FMCG (Hoch 1995: -2 to -4) and higher than the durables average
- *Considered purchase + delivery friction* — furniture buyers don't react impulsively to small price moves
- *Observed price variation is narrow* (5–95th percentile = [-30%, +43%] of base) → classic **attenuation bias** toward zero vs. experimental ranges in published meta-analyses
- *2020 COVID surge* dragged median ε down — home-goods demand was inelastically high during lockdown

**Pricing implication:** for inelastic categories (|ε|<1) marginal list-price increases grow revenue. Promo ε ≥ |1| in 11/17 categories means current discount depths roughly self-fund in volume but rarely earn the discount back outright — there is room to tighten promo depth in inelastic categories without losing units.

---

## Slide 5 — Caveats & next steps

**Caveats**
1. **Endogeneity:** prices are not random — promo timing co-moves with expected demand. Item-shop FE + the seasonality/event terms absorb a lot of this, but residual endogeneity remains. A Double-ML or IV approach (Chernozhukov 2018) is the next-level fix.
2. **Cross-elasticities** (substitutes/complements within category) are ignored — own-ε overstates revenue impact of a single SKU price move.
3. **MMM decomposition is on the weekly aggregate.** Item-level price share would be higher than 4% — but at the portfolio level, **calendar effects dwarf price** as a driver of weekly volume.

**Next steps**
- A/B price experiment on 1–2 high-volume SKUs in the inelastic categories to validate ε empirically.
- Bayesian hierarchical MMM (PyMC-Marketing) for partial pooling of item-level ε with proper posterior CIs.
- Cross-elasticity matrix at sub-category level for top-volume SKUs.
- Rolling 6-month re-estimation; monitor regime change month-over-month.

---

## Appendix — Positive elasticities: where they come from and how the pipeline handles them

A demand curve slopes down — ε < 0 is the only economically sensible sign for ordinary goods. But the raw outputs of the pipeline contain some positive ε. They are not a bug; they are a signal about *data thinness*. Three places they appear, with different causes:

| Stage | File / column | Positives | Cause |
|---|---|:---:|---|
| Per-item ridge (v6) | `model_outputs/v6_item.csv` | 283 / 2,985 | Items with thin price variation — ridge shrinks magnitude but not sign |
| v9 sub_category refit | `model_outputs/v9_subcat.csv` | 4 / 81 | Likely launch/quality drift: price and units co-move when new high-priced SKUs enter the catalogue |
| MinT reconciliation | `model_outputs/reconciled_elasticities.parquet` | 282 items, 4 sub_cats | MinT minimises trace covariance with no sign constraint — noisy positive children can survive reconciliation |

**Note that main_category (17/17 negative) and portfolio (1/1 negative) behave** — only the long tail of disaggregated estimates misbehaves.

### How the pipeline handles them — three layers

1. **`finalize.py` → deliverable column `elasticity_item`:** sign-clean by construction. Positive item ε is replaced with the item's main_category v9 ε, with `source = "category_fe_positive_fallback"` logged on the row. **0 / 3,000 positives in the published column.**
2. **`app/lib.py:get_eps()` → dashboard simulator:** when the reconciled ε is non-negative, climb the hierarchy (item → sub_cat → main_cat → portfolio) and return the first negative parent. Main_cat is always negative, so the ladder terminates. The simulator never plots an upward-sloping demand curve.
3. **`diagnose.py` → diagnostics:** HARD check `all_items_negative` on the deliverable column; SOFT check on reconciled columns (positives are *informative*, not failures — they flag where the data is too thin to identify ε against the seasonality/event controls).

### Interview talking points

- **"Why does the reconciled file contain positives if the deliverable does not?"** Because MinT is variance-optimal but unconstrained on sign. A non-negative-constrained reconciliation (Panagiotelis 2021 probabilistic, or NNLS-MinT) would enforce it; that's on the roadmap.
- **"Why not just drop positive-ε items?"** Dropping ~10% of items would bias the portfolio aggregate toward the easier-to-identify SKUs. Falling back to the parent category preserves coverage and is honest about identification — the source column records when we did it.
- **"Could MMM controls be hiding real positive ε (e.g. Veblen / Giffen behaviour)?"** Possible in luxury, not in mass-market furniture. We treat positive ε as a data-thinness signal, not a behavioural finding. An A/B price experiment is the only definitive test.

---

## Appendix — Promo elasticity (why main_category only, why it varies)

The dashboard exposes a **promo toggle** on the simulator. v9 fits a separate log-price coefficient for weeks an item is on discount — so each main_category has *two* elasticities: regular and promo.

### Why only at main_category

v9 adds a single interaction term `promo × log_price × C(main_category)` — 17 extra coefficients on top of an already wide FE + seasonality matrix. Pushing the interaction to sub_cat (81 levels) or item (3,000 levels) explodes the design matrix, and most items have **fewer than 5 promo weeks** across the panel. Per-item promo slopes would be noise. Main_category is the finest level where every cell has enough promo events (typically 200+) to identify the coefficient cleanly.

### Why some categories have promo ε *closer to zero* than regular ε

Three structural reasons — not a bug:

1. **Promo timing collinear with seasonality.** When discounts cluster on Black Friday / Christmas, the promo dummy partially absorbs demand swings that would otherwise show up as price response. Fourier + holiday controls strip the easy part out, but residual collinearity flattens the promo slope.
2. **Mix-shift toward deal-hunters.** During discount windows the marginal buyer is different — they would buy *something* in the category regardless. Volume rises but not in proportion to the discount, so the *apparent* ε shrinks.
3. **Reference-price erosion.** Categories that promote constantly (mattresses, certain seating ranges) train customers to wait for sales; the promo price *becomes* the reference, so an additional cut moves less volume.

The mix of those three forces varies by category, which is why the regular-vs-promo ranking flips across the 17 main_cats.

### Propagating promo ε down — defensible only if labelled

- **Inheritance from parent (defensible):** assigning each item the promo ε of its main_cat is the same logic as category fixed effects — borrow strength from the parent when the child has no signal. **The dashboard surfaces a "promo ε inherited from {main_cat}" badge** so the user knows it's a parent value, not an item-level estimate.
- **Per-item promo ε (not defensible):** estimating a separate promo slope per item has no statistical support given <5 promo events per item.
- **Roadmap — hierarchical Bayes:** `item_promo_ε ~ Normal(main_cat_promo_ε, τ²)` via PyMC partial-pooling. Items with many promo events drift toward their own value; items with few stay pinned to the parent. Same logic as MinT, applied to the promo coefficient.

---

## Appendix — How I scored models (the composite metric)

There is **no ground-truth elasticity in the data** — nobody labelled "the true ε of im6 is -0.75." So I can't pick a winner on accuracy alone. I scored each model on four proxy signals that, together, say "this ε is credible":

```
composite = 0.4·R²  +  0.3·(% cats ε<0)  +  0.2·(coverage/3000)  +  0.1·(1 − CI/2)
```

| Weight | Term | What it asks | Why this weight |
|---:|---|---|---|
| **0.4** | Holdout R² (last 8 weeks, log-sales) | Does the model predict demand well? | A model that can't predict demand has no business claiming to know the price coefficient. But weighted < 0.5 because *high R² with the wrong-shaped ε is useless* — see below. |
| **0.3** | % of 17 main_categories with ε < 0 | Face validity — does ε have the right sign? | Demand curves slope down; +ε means promo-timing has confounded the estimate. The naive event-study (v0) failed here outright (0%). |
| **0.2** | Coverage = items with an ε / 3,000 | Does the deliverable actually cover the portfolio? | Brief asks for per-item ε; a model that fits only 500 items isn't the deliverable. |
| **0.1** | 1 − CI_width/2 (bootstrap CI on cat ε) | Is the ε stable across resamples? | Lowest weight because a *stable wrong answer* is worse than a noisy right one — used as tiebreaker. |

### The R²-vs-elasticity-credibility trade-off (the key thing to anticipate in the call)

**The instinct says higher R² = better model.** It's only half-true here:

- v7 — LightGBM with a monotonic constraint on price — has R² 0.54 and 100% category sign-validity, but the per-item ε comes from a finite-difference probe and lands in *flat regions* of the trees for many items → ε ≈ 0. Decent forecaster, hollow elasticity.
- v10a / v10b — DML with LightGBM nuisance — also hit R² ~0.54 but materially **attenuate** ε (median -0.05 / -0.22 vs v9's -0.58). The nuisance learner over-absorbs price variance when log_price is collinear with promo/season/event controls (Chernozhukov 2018, §4.3). Same failure pattern: the flexible learner steals the signal price needs.
- v9 — MMM decomposition — has comparable R² (0.56) but **isolates the price signal from baseline / trend / season / event variance** in a transparent linear partial-out, so the ε is what's left after the other drivers are accounted for. Tighter bootstrap CI (0.07 vs v7's 0.20). That's what makes it defensible.

So the weights encode a deliberate stance: **we are not building a forecaster, we are estimating a causal coefficient.** R² gets 0.4 (must predict reasonably) but not 1.0 (because R² alone can be gamed by autoregressive features that crowd out price). The other 0.6 ensures the ε we ship has the right sign, covers the portfolio, and is stable. That's the answer to *"why didn't you pick the model with the highest R²?"*
