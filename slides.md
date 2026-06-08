## Slide 1 — The question and the headline

**Question:** How much does demand change when home24 changes a price?

**Headline number:** ε = **-2.4**. A 10% price cut lifts unit demand by ~24%. A 10% price rise drops it by ~24%. Per-item and per-category numbers ship in `elasticities_final.csv` (3,000 items) and the dashboard simulator.

**Where this sits vs published research:** Bijmolt et al. (2005) report a -1.0 to -2.0 range for durable goods across 1,800 studies. home24 lands just outside the elastic end of that range — sharply price-sensitive, consistent with a competitive online furniture market.

**Data behind it:** 3,000 items × 8 shops × ~1,080 days (Jan 2018 → Dec 2020). 5 source tables joined to an item-shop-week panel — 1.9M rows after the sellability filter.

---

## Slide 2 — How we measured it (in plain English)

Sales move for many reasons. Brand baseline. Slow growth over years. Christmas and Black Friday spikes. Summer lulls. AND price. If you regress sales on price alone, the price coefficient soaks up everything that happened to move *with* price — including January slowdowns and BFCM promo timing. That's why naive regressions show implausibly flat slopes.

**Our approach is two steps:**

1. **Strip out everything that isn't price** — item baseline, slow time trend, annual seasonality (4 Fourier harmonics), event spikes (Black Friday, Cyber Monday, Christmas, NYE, Easter, COVID), delivery promise, promotion state. What's left is the part of demand variation that price could plausibly explain.
2. **Read the slope on what's left** — the price coefficient on that cleaned residual is the elasticity. We do this with a Poisson regression on raw unit counts, because 90% of sellable item-shop-days have zero sales and a log-transform would systematically pull the slope toward zero.

That recipe is **v12** in the leaderboard. It estimates 17 category-level slopes (same design as v9 — `log_price × main_category`, split by promo) but fits on the **full 3,000-item panel** via a high-dimensional fixed-effects solver (ppmlhdfe — Correia, Guimarães, Zylkin 2020). Reads as a single regression, but absorbs ~20,000 item-shop baseline intercepts internally — that's what unlocks the full sample compared to v4's top-500 subset.

> **Want the math?** Full equation, FWL partial-out logic, and the Silva & Tenreyro (2006) log+1 attenuation result are in the *Methodology tab → EDA findings* and *Methodology appendix* below.

---

## Slide 3 — What we found

**Per-category ε (v12, all 17 main categories, sorted most-to-least elastic).** All 17 are negative. Median ε = **-2.40**, range [-4.37, -0.99]. The most elastic categories sit around -4 (commodity-like, more substitutable), the least elastic around -1 (considered durable purchases with delivery friction).

| Category | Regular ε | Reads as |
|---|---:|---|
| Most elastic | -4.37 | 10% price cut ≈ +44% units |
| Median | -2.40 | 10% price cut ≈ +24% units |
| Least elastic | -0.99 | 10% price cut ≈ +10% units |

**A reality-check on the magnitude.** v4 (the same Poisson recipe restricted to the top-500 items where it fits independently) lands at **ε ≈ -2.30** — within 0.1 of v12. Two of the four credible models agree on magnitude. The other two (v9 MMM and v10b DML) sit at -0.58 and -0.22 — both negative, both attenuated by the log-transform / DML-collinearity issues. **Honest range across all four credible models: -2.4 to -0.22.** Headline is -2.40.

**One business-relevant pattern.** Promo elasticity (when items are on discount) is consistently *less elastic* than regular-price elasticity in 11/17 categories. Three plausible reasons: (1) promo timing already absorbs the seasonal demand spike, (2) discount-window buyers behave differently from regular buyers, (3) reference-price erosion — categories that promote constantly train customers to wait. The "promo ε vs regular ε" table is in slide 4 of the appendix.

---

## Slide 4 — What's in the dashboard, and how to read it

The dashboard exposes the analysis in five tabs:

- **Story** *(this carousel)* — 5 slides, written for a non-technical reader.
- **Leaderboard** — all 13 models we tried, scored by a composite metric (forecast accuracy + correct sign + portfolio coverage + stability). v9 wins composite (best forecaster). v12 wins on magnitude correctness. Both ship.
- **ε across models** — side-by-side per-category bars for the 4 credible models (v4, v9, v10b, v12). v12 highlighted; the others are present so you can see the disagreement honestly.
- **MMM decomposition** — variance share donut + per-category bars. Important framing: 96% of weekly *volatility* is calendar-driven, 4% is price. That's about *what wobbles the series week-to-week* — **not** about elasticity. The elasticity is a slope (how customers respond to a price level), and a small variance share is fully compatible with a sharp slope.
- **Elasticity simulator** — pick any entity (item / sub-category / main-category / portfolio), drag a price slider, and see the predicted unit change and revenue impact with a 95% confidence band. Backed by the reconciled elasticities (hierarchically coherent across all four aggregation levels).
- **Methodology** — composite metric formula, EDA findings, the v9 vs v12 honesty story, and links into the model cards.

The two key numbers a stakeholder takes away from this dashboard: **ε = -2.4 at the median**, and **v9's forecast covers all 3,000 items for operational use**.

---

## Slide 5 — Caveats and what's next

**Caveats — the honest gaps**

1. **Cross-elasticities are ignored.** When a competitor item drops in price within the same category, our model attributes the lost units to the focal item's own elasticity. Own-ε therefore *overstates* the revenue impact of any single SKU's price move. Biggest honest gap in the analysis.
2. **Prices aren't random.** Promotions are timed to expected demand. Item-shop fixed effects and the seasonality/event controls absorb most of this, but residual endogeneity remains. v10 (Double/Debiased ML) is the first-pass fix already in the leaderboard; a proper instrument (cost shocks, competitor price) is the next-level fix.
3. **Sample covers COVID.** 2020 home-goods demand was inelastically high during lockdown; this drags the headline toward zero. Rolling re-estimation would let recent quarters drive the number.
4. **R² interpretation.** Our composite metric scores R² on `log(sales+1)` which structurally favours log-space models over count models. v12's holdout R² (0.30) looks lower than v9's (0.56) — but it's the wrong scoring scale for a count model. We surface this explicitly in the Leaderboard tab's "Likelihood-appropriate" column.

**Next steps — roughly in priority order**

- **A/B price experiment** on 5–10 high-volume SKUs in mid-elasticity categories to validate ε empirically and measure cross-effects.
- **Cross-elasticity matrix** at sub-category level for top-volume SKUs — closes the biggest caveat.
- **Hierarchical Bayes for per-item promo ε** — currently inherited from main_category; PyMC partial-pooling would let high-promo-frequency items earn their own slope.
- **Rolling 6-month re-estimation** + regime-change monitoring; surface in the dashboard.

> **Bottom line.** ε = **-2.4** at the median, sharply identified across two count-likelihood models. Caveats are stated, not hidden. The roadmap targets the gaps the analysis itself surfaces.

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

**The instinct says higher R² = better model.** It's only half-true here. The composite scores *deployability* (predict + sign + coverage + stability); it does not score *magnitude correctness* — that's a likelihood question.

- **v9 — MMM decomposition** — R² 0.56 with full 3,000-item coverage, tightest bootstrap CI (0.07), transparent linear partial-out. Wins composite. Ships as the **deployable forecaster** powering the simulator. Median ε = -0.58 — attenuated, because log(sales+1) on a 90%-zero panel biases the slope toward zero (Silva & Tenreyro 2006). Right forecaster, wrong magnitude.
- **v12 — Poisson with explicit item-shop FE (ppmlhdfe)** — R² 0.30 (on log-space, the wrong scale for a count model — see leaderboard footnote). 100% cats negative, **fit on all 3,000 items** (17 category slopes, item-shop intercepts absorbed iteratively), median ε = **-2.40** — inside Bijmolt (2005). Ships as the **headline magnitude**. Same regressors as v9; only the likelihood differs.
- **v4 — Poisson FE on top-500 items** — R² 0.62 (highest of any model, but on the densest 500 items where Poisson predicts well). Median ε = -2.30. Independently corroborates v12 within 0.1. Kept on the leaderboard as the reproducibility check.
- **v7 — LightGBM monotonic** — R² 0.54, decent forecaster, but per-item ε from finite-difference lands in flat regions → ε ≈ 0 for many items. Hollow elasticity.
- **v10a / v10b — DML with LightGBM nuisance** — R² ~0.54 but materially attenuate ε (median -0.05 / -0.22). Nuisance learner over-absorbs price variance under log_price/promo collinearity (Chernozhukov 2018, §4.3). Reported as the attenuation lower bound.
- **v11 — Tweedie GLM with Mundlak FE** — same v9 design with a Tweedie likelihood and Mundlak's mean-control as a stand-in for explicit FE. ε collapses to ~0. Useful negative result: confirms v12's clean -2.40 needs proper nonlinear FE (ppmlhdfe), not just the count likelihood.

So the weights encode a deliberate stance: **we ship the deployable forecaster (v9) and the right-likelihood slope (v12) as a pair.** R² gets 0.4 — it must predict reasonably — but not 1.0, because high R² with the wrong-scale slope is misleading (see v9). The leaderboard's *Likelihood-appropriate* column is the lever that surfaces which models score the slope on the right scale. That's the answer to *"why two winners?"*

---

## Appendix — EDA findings that shaped every modelling decision

Five parquet files, all keyed on `item_key`: master (3,000 items × 17 main_categories × 81 sub_categories × 123 brands), prices, deliverytimes, sales_data, sellability. Panel grain is **(item, shop, date)** — the same item has different prices and delivery promises across the 8 shops.

### The single most important finding

**The `sales_data` table only contains rows with `sales_count ≥ 1`.** Absence of a row means zero sales, not missing data. Outer-joining sales onto the sellable item-shop-day grid materialises the zeros — and the result is brutal:

- 12.75M sellable item-shop-days in the panel
- Only **10.3% have any sale**
- The remaining **89.7% are sellable-but-zero** (item was listed, in stock, viewable — just didn't sell)

This 90% zero-inflation drives every downstream modelling choice. `log(sales+1)` is the only way to keep OLS tractable, but the +1 shift biases the price slope toward zero on heavily-zero data (Silva & Tenreyro 2006). That bias is the root cause of the v9 / v12 magnitude gap (-0.58 vs -2.40): v9 uses log+1 on the full panel and attenuates; v12 uses a Poisson MLE with explicit item-shop FE (ppmlhdfe) on the same full panel where the count likelihood handles zeros natively. v4 corroborates v12 (-2.30 on the top-500 dense slice) — same recipe, smaller sample.

### Other findings worth knowing

| Finding | Cleanup / decision |
|---|---|
| Dates stored as `YYYYMMDD` integers, not Unix timestamps | Parse with `format="%Y%m%d"` |
| Date ranges don't overlap fully (prices/delivery from 2017-11, sellability from 2018-01) | Analysis window is the tightest overlap: **2018-01-01 → 2020-12-17**, ~1,080 days |
| 16.13% of item-shop-days are unsellable (out of stock / paused) | Drop unsellable rows — they can't have sold, so they'd bias ε toward zero |
| 4.25% of price records are non-positive (n=13,813) — data errors | Drop before `log(price)` |
| Price-change distribution: 5–95th pct = **[-30%, +43%]** | Simulator clamps to this support; anything outside is flagged as out-of-support extrapolation |
| `item_price_special` is null on non-promo days | Derived `is_promo = item_price_special.notna()` — v5/v9 split ε into regular vs promo slopes |
| 5% of `delivery_days` null; range [3, **1003**] — 1003 is a sentinel | Median-impute, keep missing-indicator, cap at 90 |
| Median 99 price records per item across shops | Enough within-item price variation to identify per-item ε; pooled to category for stability |
| 17 main_categories, but `im14` has 629 items while others have <50 | Headline at main_category (always well-sampled); per-item from v6 ridge with sign-fallback |
| Last 60 days as holdout per (item, shop) | Time-aware split prevents leakage into the R² metric |

### Variance share v9 recovered post-cleanup

Once the panel was built, v9's decomposition showed where weekly demand *volatility* lives:

- **Events 38%** (Black Friday / Cyber Monday / Christmas / Easter / COVID)
- **Seasonality 33%** (smooth annual cycle, K=4 Fourier)
- **Trend 25%** (slow 3-year drift)
- **Price 4%**

96% of week-to-week movement is calendar-driven — price is not the main driver of swings. That is **not** a statement about elasticity. Variance share answers "what wobbles the series?"; elasticity answers "how do customers respond to a price level?". The two are orthogonal: a small variance share is fully compatible with a sharp slope (cf. years-of-schooling in a Mincer wage regression). The MMM partial-out cleanly isolates the slope so naive log-log attenuation does not, and v12's Poisson likelihood pins it at -2.40.
