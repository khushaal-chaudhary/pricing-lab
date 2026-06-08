# Models Explained — From First Principles

A walk through every model in the pipeline (v0 → v10b), starting from "what is regression" and ending with "why v9 wins." Written so a non-technical reader can follow the logic, and a technical reader gets the substance.

---

## Part 1 — The base

### 1.1 The question

The panel covers 3,000 items sold across 8 shops over three years. The business question is one number per item:

> If we raise this item's price by 10%, how many fewer units will sell next week?

That number is called **price elasticity of demand**, written ε. By convention it's negative — higher price → fewer units.

- **ε = −0.5** means: 10% price increase → 5% volume drop. Demand is *inelastic* (people don't react strongly).
- **ε = −2.0** means: 10% price increase → 20% volume drop. Demand is *elastic* (people are very price-sensitive).
- **|ε| = 1** is the dividing line. Below it, raising price grows revenue. Above it, cutting price grows revenue.

### 1.2 The data

Five tables, joined into one big spreadsheet ("the panel") where every row is **one item, in one shop, in one week**:

| Column | Where it comes from | What it tells us |
|---|---|---|
| `sales_count` | sales table | units sold that week — **the prediction target** |
| `price` | prices table | shelf price that week — **the lever** |
| `promo` | derived from prices | 1 if discounted, 0 if regular |
| `item_key`, `shop_id` | items + shops | which SKU, which shop |
| `main_category`, `sub_category` | items hierarchy | category structure (17 mains, 81 subs) |
| `date` | sales | week-of-year, holiday flags, trend |
| `delivery_days` | items | logistics friction |
| `is_sellable` | sellability calendar | was the item actually on offer that week |

After dropping rows where the item wasn't sellable, the panel is **~1.9 million rows**.

### 1.3 The fundamental challenge — confounders

A naive "price went down → sales went up" reading gets the wrong answer. Why?

Because **price moves don't happen in a vacuum**. The price gets cut when:
- It's Black Friday (demand was going to spike anyway)
- It's end-of-season clearance (demand was about to die)
- A competitor launched something new (demand was leaking)
- The category is in its seasonal peak (sofas in autumn, garden in spring)

A naive "price down, sales up" reading during Black Friday credits the price cut for the **entire** demand spike — most of which would have happened anyway because it's Black Friday.

These backstage drivers are called **confounders**. The whole game in elasticity modelling is **separating the price effect from the confounder effects**. Every model in the leaderboard is a different attempt at this separation.

---

## Part 2 — Regression in plain English

### 2.1 What a regression is

A regression is a recipe for predicting one number (the **output**, called Y) from other numbers (the **inputs**, called X). The recipe is just a weighted sum:

```
Y = β₀ + β₁·X₁ + β₂·X₂ + ... + βₙ·Xₙ + error
```

- The β's are **coefficients** — the weights the algorithm learns from the data.
- β₀ is the **intercept** — what Y is when all X's are zero.
- The **error** is whatever the model couldn't explain.

The algorithm picks the β's that make the model's predictions match the observed Y as closely as possible (smallest squared errors).

### 2.2 Why log-price and log-sales

The target coefficient means **"a 10% price change produces an X% sales change."** That's a percentage-to-percentage relationship, called **elasticity**.

The math trick: take logs of both sides, and the coefficient on `log(price)` directly *is* the elasticity. So the regression is:

```
log(sales) = β₀ + ε · log(price) + (other stuff) + error
```

The value of ε recovered is the elasticity. No conversion needed. This is why every model in the leaderboard uses `log(price)` as an input — it's the form that makes ε pop out cleanly.

(Side note: the regression uses `log(sales + 1)` rather than `log(sales)` so that zero-sales weeks don't break the logarithm. This introduces a small distortion that v10b's Tweedie objective avoids — more on that later.)

### 2.3 What R² means

After the model is fit, R² answers: **how much of the variation in Y did the model explain?**

- **R² = 1.0** means the model perfectly explains every wiggle in the data.
- **R² = 0** means the model explains nothing — you'd do just as well predicting the average.
- **R² < 0** means the model is **worse than predicting the average** on new data (the holdout). It happens when the model overfits the training data and extrapolates wildly on the test set.

R² is computed on the **holdout** — the last 8 weeks of the panel that the model didn't see during fitting. This tests whether the model learned something real, or just memorised the training weeks.

### 2.4 Why R² alone is the wrong target for this problem

This is the most important conceptual point in the project.

The goal is not to **forecast** sales. The goal is to estimate **one number per item** — its elasticity. A model can predict sales beautifully while having a completely wrong elasticity coefficient. How? By using features that *steal* the price signal:

- If the model has access to "last week's sales" as a feature, it'll predict this week's sales mostly from that, and the price coefficient collapses to near-zero — because most of the variance is already explained by the lag.
- If the model uses a complex non-linear interaction between price and season, the season term may absorb the price effect during peak weeks.

The pipeline's leaderboard scoring is built to catch this trap. R² gets weight **0.4**, not **1.0**. The other 0.6 of the weight goes to:
- **% of categories with ε < 0** (face validity — does it have the right sign?)
- **Coverage** (does it produce an ε for all 3,000 items?)
- **Bootstrap CI** (is the ε stable across resamples?)

A model that predicts sales well but produces ε ≈ 0 fails three of these four — and loses on composite even if it wins on R².

---

## Part 3 — The partial-out approach (Frisch–Waugh–Lovell)

This is the trick at the heart of v9 and v10. Once you grasp it, every other model becomes a variation on "did you partial out properly or not."

### 3.1 The intuition

Imagine you want to know how much **studying** improves a student's exam score. You have data on study hours, exam scores, and *also* how much each student slept the night before.

Sleep is a confounder: well-rested students both study better *and* test better. If you regress score on study-hours alone, you'll overstate the study effect because well-rested students are sneaking extra credit into the slope.

The partial-out approach does this in three steps:

1. **Predict score from sleep alone.** Whatever's left over (the residual) is "exam score *after sleep is accounted for*."
2. **Predict study-hours from sleep alone.** Whatever's left over is "study-hours *after sleep is accounted for*."
3. **Regress the score residual on the study residual.** The slope you get is the study effect *holding sleep constant*.

This three-step recipe gives the same answer as a single big regression that includes both sleep and study as predictors — but it makes the logic explicit. It's the **Frisch–Waugh–Lovell theorem**, proved in 1933.

### 3.2 Applied to elasticity

Mapped to this problem:
- Y = `log(sales)`
- T = `log(price)` (the **treatment** — the lever whose effect is being estimated)
- W = everything else: item-shop baseline, trend, seasonality, holidays, promo, delivery days

The recipe:

1. **Predict log(sales) from W alone.** What's left is the part of sales that **W can't explain** — the part that has to come from price or noise.
2. **Predict log(price) from W alone.** What's left is the part of price that **W can't explain** — the part that's "free" of seasonal/promotional/calendar influence.
3. **Regress residual-sales on residual-price.** The slope is ε, cleanly identified against everything in W.

This is why **v9's ε is defensible** in a meeting. It's the price coefficient *after every other systematic driver has had its share*. The leftover slope can't be confounded by seasonality (it's already partialed out) or events (also partialed out) or item popularity (FE absorbs it).

### 3.3 Why this beats "throw everything into one regression"

It doesn't, mathematically — both produce the same coefficient by FWL. But the partial-out framing gives you:

- **A variance decomposition.** Step 1 tells you how much of weekly sales variance is calendar/event/baseline. Step 3 tells you how much is price. This is the table the VP wants.
- **A diagnostic.** You can inspect each residual and check for remaining structure. If the price residual still shows a strong seasonal pattern, your W wasn't rich enough.
- **A robustness story.** "ε is identified against this specific list of controls." That's the sentence an interviewer wants.

---

## Part 4 — Every model, demystified

For each model: **what goes in, what comes out, what it gets right, what it gets wrong, why its leaderboard numbers look the way they do.**

Leaderboard, sorted by composite score:

| Model | Holdout R² | % cats ε<0 | Coverage | Boot CI | Composite |
|---|---:|---:|---:|---:|---:|
| v9 MMM | 0.560 | 100% | 3,000 | 0.07 | **0.820** |
| v7 LightGBM mono | 0.536 | 100% | 2,999 | 0.20 | 0.804 |
| v5 promo-split | 0.508 | 100% | 3,000 | 0.07 | 0.800 |
| v3 FE category | 0.500 | 100% | 3,000 | 0.06 | 0.797 |
| v10a DML log | 0.540 | 88% | 3,000 | 0.09 | 0.757 |
| v10b DML Tweedie | 0.550 | 82% | 3,000 | 0.11 | 0.751 |
| v4 Poisson FE | **0.623** | 100% | 500 | 0.21 | 0.672 |
| v1 pooled OLS | −0.030 | 100% | 3,000 | 0.00 | 0.600 |
| v6 ridge per-item | −0.293 | 100% | 2,985 | 0.99 | 0.549 |
| v2 per-item OLS | −201 | 100% | 2,985 | 1.19 | 0.539 |
| v0 naive event | n/a | 0% | 2,957 | n/a | 0.247 |

---

### v0 — Naive event-study (composite 0.247, the bottom)

**Goal.** "Just look at what happens to sales when prices change. No regression, no controls."

**Recipe.** For every price change in the data, compute `Δlog(sales) / Δlog(price)`. Take the median across events as the elasticity.

**Why it fails.** It treats every price change as a clean experiment. But the biggest price changes happen during **promotions and clearances**, when demand is moving for its own reasons. The result: **0 out of 17 categories have a negative ε** — the sign is wrong on every single category. The promo timing entirely dominates the price effect.

**What it teaches.** It's the baseline that proves "you can't just take ratios" — you have to control for *when* prices change. Every subsequent model is a different way of adding that control.

---

### v1 — Pooled OLS (R² = −0.03, composite 0.600)

**Goal.** "One single ε for the whole catalogue."

**Recipe.** `log(sales+1) = β₀ + ε · log(price) + error`. One regression on the entire 1.9M-row panel. One number out.

**Inputs.** `log(price)` only.
**Output.** A single ε that applies to every item in every category.

**Why R² is barely negative.** The model has nothing to work with — no FE, no seasonality, no item identity. Its prediction is essentially a flat line through the cloud of points. A flat line at the *training* mean loses to the *holdout* mean by a hair (the holdout's variance slightly exceeds the residual variance), giving R² just below zero.

**Why composite is still 0.60.** The pooled slope happens to come out negative (sign is right → 100% cat-neg). Coverage is full because one ε applies to all 3,000 items. CI is tiny because pooling across millions of rows stabilises the slope. So v1 scores well on three of four composite terms — but it's a single number for the entire catalogue, which is useless as a *per-item* deliverable. It exists in the leaderboard as a "what does pooling alone get you" benchmark.

---

### v2 — Per-item OLS (R² = −201, composite 0.539)

**Goal.** "Fit a separate slope for every item."

**Recipe.** 3,000 separate OLS regressions, one per item. Each uses that item's own 8-shop × 156-week data plus shop and month FE.

**Why R² explodes negatively.** Items in the long tail have *very few* price observations — maybe 10 weeks at 2 different prices. OLS happily fits an interpolating line through those points, producing slopes of `−10` or `+5` (the code clips to `[−10, 5]`). On the holdout, those wild slopes extrapolate to **astronomical predicted sales**, the squared errors are gigantic, and one catastrophic prediction can drag the panel-level R² to **−201**.

R² is **unbounded below** — there is no floor. A single item predicting `exp(50)` units when reality is 5 units overwhelms everything else.

**Why composite is still 0.54.** Sales-weighted aggregation across items pulls the *category* slopes back toward sensible negative values (100% cats neg). Coverage is 99% (24 items had no price variation). It's a usable category-level number — but the per-item ε is unusable noise (CI width 1.19).

**What it teaches.** Without regularisation, "fit one model per item" fails the moment the data is uneven. This is the motivation for v6.

---

### v3 — FE panel with category × log(price) interaction (R² = 0.50, composite 0.797)

**Goal.** "Fit category-specific elasticities while absorbing item-shop level differences via fixed effects."

**Recipe.**
```
log(sales+1) = α_(i,s) + month_FE + Σ_c ε_c · log(price) · 1[cat = c] + error
```

- `α_(i,s)` is a separate intercept for every (item, shop) pair (~16k of them). Absorbs item popularity, shop catchment, etc.
- `month_FE` controls for seasonality coarsely.
- The price term is split *by category* — 17 ε's, one per main_category.

**Why R² is decent (0.50).** FE + month controls explain a chunk of variance. Not as much as v9 because seasonality at the month level is too coarse (it misses the weekly Black Friday spike).

**Why composite is good (0.80).** All 17 categories have negative ε, full coverage, tight CI. v3 is essentially "v9 minus the proper seasonality." Adding K=4 Fourier and holiday dummies gets us v9.

**The lesson.** Fixed effects are the workhorse trick — they absorb the worst cross-sectional confounder (item identity) practically for free. Every well-performing model in the leaderboard has them.

---

### v4 — Poisson GLM on top-500 items (R² = 0.62, composite 0.672)

**Goal.** "Use the *right* likelihood for count data instead of squashing it into a log-linear regression."

**Recipe.** Generalised Linear Model with Poisson likelihood: `sales_count ~ Poisson(exp(α_item + α_shop + ε · log(price) + ...))`. The `log` link makes ε an elasticity automatically.

**Why R² is the highest in the leaderboard.** Poisson handles the count nature of sales properly — it doesn't need the `+1` log-shift hack, it has the right variance structure for zero-inflated counts (well, almost — Tweedie is even better, see v10b).

**Why coverage is only 500.** Per-item FE in a Poisson GLM needs enough non-zero observations per item to identify the FE. Items in the long tail have so many zero-sales weeks that the likelihood is flat — the optimiser can't pin down their FE. The 500-item cap is a *practical* threshold: items with enough sales density to make the fit converge. Also, the design matrix at 3,000 item-FE × 1.9M rows is computationally heavy on `statsmodels`.

**Why it loses despite the highest R².** Coverage 500/3,000 = 0.17 costs it ~0.16 on the composite (which weights coverage at 0.2). A high R² on a curated subset isn't a deliverable for a brief that asks for **all** items.

**What it teaches.** v4 is a **methodological sanity check** — "does a proper count model agree with the log-linear family on the items where it can fit?" The answer is **sign yes, magnitude no** (see comparison below). That divergence is itself the headline story for the elasticity range.

**Head-to-head v4 vs v9 on the 500-item overlap.**

| Metric | v4 (Poisson FE, top-500) | v9 (MMM, full panel) |
|---|---|---|
| Categories with ε < 0 | 15 / 15 | 17 / 17 (15 overlap) |
| Items with ε < 0 (overlap) | **500 / 500** | (same items) |
| Median \|ε\| (category) | **2.30** | 0.58 |
| Median \|ε\| (per-item) | **2.18** | 0.67 |
| Pearson corr (category ε) | 0.27 | |
| Spearman rank (category) | 0.35 | |

**Sign agrees, magnitude doesn't.** v4 is ~4× more elastic than v9. Two plausible reasons:
1. **Log-shift bias.** Log-OLS on `log(sales+1)` is known to bias slopes toward zero on zero-inflated count data (Silva & Tenreyro 2006, "The Log of Gravity"). Poisson with log link has no `+1` hack and may be closer to truth. The Bijmolt 2005 durables literature centres on −1.0 to −2.0 — v4 sits **inside** that range, v9 sits **below** it.
2. **Top-500 over-fit.** High-volume items have more price variation and larger absolute volume swings; their fitted slopes are louder than the panel average. Some of v4's magnitude advantage is the favorable subset.

The honest framing: **v9's −0.58 is a likely lower bound on the magnitude; v4's −2.30 is a likely upper bound; truth probably lives at −1.0 to −1.5**, which matches the literature. v9 still ships as the headline (it's the full-coverage deliverable) but is reported with this range in the methodology slide.

---

### v5 — Promo-split (R² = 0.51, composite 0.800)

**Goal.** "Fit *two* elasticities per category — one for regular weeks, one for promo weeks."

**Recipe.** Same as v3, but split the price coefficient by promo state:

```
... + ε_c^reg · log(price) · (1 − promo) + ε_c^prom · log(price) · promo
```

Two slopes per category, 34 in total.

**Why it matters.** Regular and promo demand respond to price differently — promo-period buyers are deal-hunters (often less price-sensitive in elasticity terms, because mix-shift dominates). Treating them as one slope blurs both. v5 surfaces both numbers.

**Why it doesn't quite top v9.** Promo-split is a *piece* of v9. v9 = v5 + proper Fourier seasonality + holiday dummies + linear trend. v5 still relies on coarse month-FE for seasonality, so the partial-out is less clean. The leaderboard gap (0.800 vs 0.820) is exactly that improvement.

---

### v6 — Ridge per-item (R² = −0.29, composite 0.549)

**Goal.** "Fix v2's blow-up with regularisation."

**Recipe.** Same setup as v2 (one regression per item), but add an L2 penalty on the slope: `min(squared error + λ · ε²)`. The penalty shrinks wild slopes toward zero — items with thin data get pulled back to a reasonable range instead of fitting spikes.

**Why R² climbs from −201 to −0.29.** Ridge does its job — no more catastrophic predictions. But it shrinks slopes *toward zero*, and for items with weak price variation, the slope ends up so shrunk that the model predicts a near-flat line per item. That misses the holiday spikes in the holdout (no seasonality controls), giving moderately bad R².

**Why composite is 0.55 despite negative R².** The aggregated category ε's still come out 100% negative — ridge inherits the right sign even when shrunk. Coverage 99%. CI 0.99 reflects the per-item instability.

**The lesson.** Regularisation cures explosive overfit but doesn't add structure. You still need FE + seasonality to actually predict. v9 has both *and* the ridge per-item is layered on its residuals for the published item-level ε.

---

### v7 — LightGBM with monotonic price constraint (R² = 0.54, composite 0.804)

**Goal.** "Let a flexible ML model figure out the price–demand relationship, but force it to be downward-sloping (monotonic in price)."

**Recipe.**
- Input features: `log(price)`, `promo`, `week_of_year`, `month`, `is_holiday`, `item_FE` (as a categorical), `shop_FE`, `delivery_days`.
- Output: `log(sales+1)`.
- Constraint: the price feature is constrained to have a monotonically decreasing relationship with the output. Higher price → lower predicted sales, always.
- ε for each item is computed by a **finite-difference probe**: predict at the item's current price, then at price × 1.01, take the slope of `log(sales)` vs `log(price)`.

**Why R² is decent (0.54).** Gradient-boosted trees with these features capture non-linear seasonality and interactions natively. They're a good forecasting tool.

**Why the elasticity is hollow.** Trees are piecewise-constant functions. Within most price ranges, the model's prediction surface is **flat** — no slope. The finite-difference probe at `price × 1.01` lands on the same step as `price × 1.0`, giving ε ≈ 0 for many items. The category averages still come out negative (because at the category level you average across many items, some of which sit on a step boundary), but the per-item ε is unreliable — large flat regions punctuated by big jumps.

**Why composite is 0.804 (second place).** Decent R², 100% cat-neg, full coverage. But CI 0.20 (vs v9's 0.07) reflects the finite-difference instability. v9 beats it on every term except R².

**The lesson.** Flexible ML can predict well but doesn't naturally produce a **smooth, interpretable slope**. For an elasticity deliverable, "what is the slope" needs to be a model parameter, not a post-hoc probe.

---

### v8 — LightGBM with lag-sales features (built, dropped from the headline leaderboard)

**Goal.** "Push R² above 0.80 by giving the model the most informative possible feature for next-week's sales: last-week's sales."

**Recipe.** Same LightGBM stack as v7, but with extra features:
- `lag1_sales`, `lag2_sales`, `lag4_sales`, `lag13_sales`, `lag52_sales` — sales counts from prior weeks.
- `roll4_mean`, `roll13_mean`, `roll4_std` — rolling averages and volatility.
- `lag1_log_price`, `d_log_price = log_price − lag1_log_price` — price-change shock.

ε recovered via the same finite-difference probe as v7.

**Why it was built.** Forecasting orthodoxy says lag features are the single biggest signal for any time-series prediction problem. Including them should push R² well past v7's 0.54 — maybe into the 0.80+ territory that "real" forecasting models hit.

**Why it failed cleanly.** R² did indeed climb. But the **per-category ε's collapsed to ~−0.005 to −0.02** — essentially zero. The lag features explain so much of next-week's sales that almost no variance is left for the price coefficient to explain. The price slope, fitted as the residual signal, is effectively ε ≈ 0 across every category.

This is **direct signal theft**: lag-sales are an explicit predictor that absorbs the dependent variable's autocorrelation, leaving the price coefficient nothing to claim.

**How this differs from v10's attenuation.** v8 and v10 share a family of failure ("flexible model with too much information about the outcome steals price signal") but the mechanism and severity differ sharply:

| Aspect | v8 (lag-features OLS) | v10 (DML with LGBM nuisance) |
|---|---|---|
| Lag-sales features used? | **Yes — directly** | No — same controls as v9 |
| Mechanism | Direct theft via autocorrelation feature | Indirect leakage via flexible nuisance learner finding subtle nonlinear correlations between price and W controls |
| Median ε across cats | ~ −0.01 (collapse) | −0.05 (v10a), −0.22 (v10b) |
| Severity | Total — every cat ε ≈ 0 | Partial — sign preserved, magnitude shrunk |
| Theory | None (empirical failure) | Chernozhukov 2018 §4.3 — weak-treatment-exogeneity failure |

v8 is the *extreme* version; v10 is the *principled-method* version that still hits a milder form. The leaderboard keeps v10 (clean theoretical story, partial attenuation) and drops v8 (raw collapse, no new lesson once v10 is there).

**v8 is preserved in the pipeline** (`models_v8.py`, `model_outputs/v8_cat.csv`, `model_outputs/v8_item.csv`) so the artefact trail is honest about what was built. The composite leaderboard reports only the curated set; v8 lives in the iteration log as "tried, learned, dropped."

**The lesson — and the interview line.** "Adding lag-sales features to v7 produces v8: R² climbs, ε collapses. That's the most direct demonstration in the project that R² alone is the wrong target. The composite metric exists precisely because v8 would have won on R² and shipped a worthless ε."

---

### v9 — MMM-style decomposition (R² = 0.56, composite **0.820, winner**)

**Goal.** "Decompose weekly sales into baseline + trend + seasonality + events + price, in that order, so price is the *residual* after everything else is accounted for."

**Recipe.**
```
log(sales+1) = α_(i,s)                              # item-shop baseline
            + δ · weeks_since_start                 # linear trend
            + Σ_k θ_k · Fourier_k(week_of_year)     # K=4 annual seasonality
            + Σ_h ψ_h · holiday_h(date)             # BFCM, Xmas, NYE, Easter, COVID
            + ε_c^reg  · log(price) · (1 − promo)   # regular-week elasticity per cat
            + ε_c^prom · log(price) · promo         # promo-week elasticity per cat
            + γ · delivery_days
            + error
```

**Inputs.** Everything in the panel.
**Outputs.**
- 17 regular ε + 17 promo ε (the category-level deliverable).
- A variance decomposition: how much of weekly sales is calendar vs trend vs events vs price?
- Per-item ε (3,000 of them) layered on top via a ridge regression on the *residuals* — same FWL logic.

**Why it wins on composite (0.820).** It's not the best on any single metric — v4 beats it on R², v10 matches CI tightness. But it's the *only* model that scores well across **all four** composite terms simultaneously:
- R² 0.56 — fourth-highest but well above the failure-mode models.
- 100% cats neg — face validity is intact.
- 3,000-item coverage — full delivery.
- CI 0.07 — tightest in the leaderboard.

**Why the partial-out structure is the secret.** The seasonality + event terms explain ~71% of weekly variance. The price coefficient is fit on what remains. That residual is "the part of demand that *can't* be explained by the calendar" — exactly the variation a pricing decision actually faces.

**The variance decomposition table** (the deliverable the business wants):
- Events: 38%
- Seasonality: 33%
- Trend: 25%
- Price: 4%

The headline business insight: **most of weekly demand swing is calendar-driven, not price-driven.** Pricing strategy should work *with* the calendar, not against it.

---

### v10a — DML with log target (R² = 0.54, composite 0.757)

**Goal.** "Modern causal-ML version of v9. Use LightGBM to flexibly predict both Y and T from W, then run the residual regression."

**Recipe.** Double/Debiased Machine Learning (Chernozhukov 2018):
1. Predict `log(sales+1)` from W (everything except price) using LightGBM.
2. Predict `log(price)` from W using LightGBM.
3. Regress residuals from step 1 on residuals from step 2. The slope is ε.

This is the **same FWL logic as v9** — except steps 1 and 2 use LightGBM instead of linear regression, so they can capture non-linear seasonality and interactions.

5-fold cross-fitting prevents the residuals from being contaminated by overfitting.

**Why R² is comparable to v9 (0.54 vs 0.56).** LightGBM nuisance predictions are roughly as accurate as the linear v9 structure on this panel. The flexibility doesn't help much because v9's controls were already rich.

**Why ε attenuates (median −0.05 vs v9's −0.58).** This is the interesting failure. LightGBM is too greedy at step 1 — it learns to predict sales using week-of-year features that are *correlated with* promo timing, which is *correlated with* price moves. By step 3, the price residual has very little signal left, and the slope shrinks toward zero. This is the **weak treatment exogeneity** failure mode (Chernozhukov 2018, §4.3) — flexible ML nuisance models can "steal" the treatment signal when controls are collinear with the treatment.

**Why composite drops to 0.76.** Only 88% of categories have ε < 0 (two categories now show positive ε after attenuation), CI widens to 0.09. R² and coverage are fine. The attenuation specifically hurts the % cats neg term.

**The interview point.** v10a confirms v9's *sign* and *ordering* of categories (the most elastic categories in v9 are still the most elastic in v10a). It doesn't confirm v9's *magnitude*. That's reported honestly as a "robustness check that hit a known DML failure mode" rather than "v9 was overestimating."

---

### v10b — DML with Tweedie y-stage (R² = 0.55, composite 0.751)

**Goal.** "Same as v10a, but use a Tweedie loss in the y-stage so the model fits raw sales counts directly instead of `log(sales+1)`."

**Recipe.** Same three-step DML, but step 1 uses LightGBM with a **Tweedie objective** (`tweedie_variance_power=1.5`) on raw `sales_count` instead of log-sales.

**Why Tweedie matters.** 90% of sellable item-shop-weeks have zero sales. Log-transforming with `+1` shoves all those zeros to the same value (0), which distorts the variance structure and pulls slopes toward zero. Tweedie has a built-in zero-inflation handling — it's the right likelihood for "lots of zeros plus a continuous tail."

**Why it still attenuates (median −0.22).** Tweedie fixes the y-stage zero-handling but doesn't fix the LightGBM signal-stealing problem. The attenuation is less severe than v10a (−0.22 vs −0.05) — Tweedie's better likelihood does help — but it's still attenuated vs v9.

**Why composite (0.751) is just below v10a.** Marginal R² improvement, but 82% cat-neg (vs v10a's 88%) — three categories now show positive ε. Tweedie's higher resolution on small categories actually reveals more cases where the price signal is too weak to identify cleanly.

**The framing.** Truth most likely lies between v9 (−0.58) and v10b (−0.22). Both are negative, both are inelastic, both are consistent with the Bijmolt (2005) durables literature (which centres around −1.0 to −2.0 — home24 is *more* inelastic than the literature, which makes sense for furniture vs the wider durables category).

---

## Part 5 — Why v9 wins the composite (the cheat sheet)

| Term | Weight | What it asks | v9's score | Why |
|---|---|---|---|---|
| Holdout R² | 0.4 | Can it predict? | 0.56 | Yes, well. Not #1 but well above failure-mode floor. |
| % cats ε < 0 | 0.3 | Right sign on every category? | 100% | Yes. The partial-out structure ensures it. |
| Coverage / 3,000 | 0.2 | Does it ship an ε for every item? | 100% | Yes. Ridge per-item layered on v9 residuals. |
| 1 − CI/2 | 0.1 | Is ε stable across resamples? | tight (CI 0.07) | Best in the leaderboard. |

Every other model fails at least one of these:
- v4: highest R² but fails coverage (500/3,000).
- v7: matches R² but loose CI (0.20) and hollow per-item ε.
- v10: fails % cats neg (DML attenuation).
- v5/v3: nearly tied — they're "v9 minus seasonality" and "v9 minus promo-split." Each missing piece costs ~0.02.

v9 is the model that **doesn't lose** on any term. That's the definition of a robust deliverable.

---

## Part 6 — One question, one model

When an interviewer asks…

| Question | Answer | Model |
|---|---|---|
| "What's the elasticity?" | "−0.58 median, every category negative, inelastic regime." | v9 |
| "How do you know the calendar isn't driving it?" | "Fourier + holidays partial that out before the price coefficient is fit." | v9 |
| "Did you try ML?" | "Yes — v7 LightGBM and v10 DML. They confirm sign and ordering; v10 attenuates due to a known DML failure mode under weak treatment exogeneity." | v7, v10 |
| "Why not the highest R²?" | "v4 Poisson has R² 0.62 but only covers 500 items. R² on a subset isn't a deliverable for a 3,000-item brief." | v4 |
| "How do you handle the long tail of items?" | "Per-item ridge on v9 residuals — the panel-level structure gives the slope; ridge shrinks per-item deviations from it." | v6 layered on v9 |
| "How do you split promo vs regular?" | "Two separate price coefficients per category, fitted jointly with the promo interaction term." | v5/v9 |
| "Are the levels coherent?" | "Yes — MinT reconciliation (Wickramasuriya 2019) projects item / sub / main / portfolio estimates onto the linear summing constraint while minimising trace variance." | post-v9 reconciliation |
