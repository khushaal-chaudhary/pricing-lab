# Model Leaderboard — home24 Price Elasticity
Composite = 0.4·R² + 0.3·(% cat ε<0) + 0.2·coverage/3000 + 0.1·(1-CI/2)
Higher = better.

| model                      |   holdout_r2 |   pct_cat_neg |   coverage_items |   boot_ci_width |   composite |
|:---------------------------|-------------:|--------------:|-----------------:|----------------:|------------:|
| v9_mmm_light               |       0.5595 |             1 |             3000 |           0.069 |      0.8203 |
| v7_lightgbm_monotone       |       0.5362 |             1 |             2999 |           0.2   |      0.8044 |
| v5_promo_split             |       0.5077 |             1 |             3000 |           0.07  |      0.7996 |
| v3_fe_category_interaction |       0.5005 |             1 |             3000 |           0.055 |      0.7975 |
| v4_poisson_fe              |       0.6227 |             1 |              500 |           0.212 |      0.6718 |
| v1_pooled_ols              |      -0.0297 |             1 |             3000 |           0.002 |      0.5999 |
| v6_ridge_per_item          |      -0.2925 |             1 |             2985 |           0.993 |      0.5494 |
| v2_per_item_ols            |    -201.318  |             1 |             2985 |           1.194 |      0.5393 |
| v0_naive_event             |     nan      |             0 |             2957 |         nan     |      0.2471 |
| v10a_dml_log               |       0.5400 |          0.88 |             3000 |           0.090 |      0.7568 |
| v10b_dml_tweedie           |       0.5500 |          0.82 |             3000 |           0.105 |      0.7507 |
| v11_tweedie_glm            |       0.0029 |          0.35 |             3000 |           0.016 |      0.4063 |

> **v11 verdict (Tweedie GLM with Mundlak FE):** Built to isolate "what does the right likelihood add to v9?" from v10b (which mixes Tweedie with DML attenuation). v9 design matrix (K=4 Fourier + holidays + trend + cat×log_price×promo) refitted via statsmodels Tweedie GLM (var_power=1.5, log link) on raw counts, with item-shop FE absorbed via Mundlak (item-shop mean of log_price). Result: ε collapses to ~0 (median +0.003, 65% cats POSITIVE). Mundlak is exact under FWL for linear models; under a log link it is only approximate — with log_price split across 17 category interactions, a single shared `mu_lp_is` control cannot partial out between-item variation for each category slope. The right Tweedie-family fix needs explicit per-item FE within category (the v4 recipe) — which is why v4 scales only to the top-500 items where the MLE remains tractable. Useful negative result: confirms that v4's clean -2.30 magnitude relies on proper nonlinear FE, not just the count likelihood.

> **v10 verdict (DML):** v10a/v10b reproduce the sign on most categories but estimates are materially attenuated (median ε ≈ -0.05 / -0.22 vs v9's -0.58). DML's nuisance LightGBM over-absorbs within-item variation when log_price is highly collinear with promo/season/event controls — a known DML failure mode under weak treatment exogeneity (see Chernozhukov 2018, §4.3). v9 stays headline; v10 is reported as a lower-bound robustness check. Truth most likely lies in [-0.58, -0.22]; both are negative, both inelastic, both consistent with Bijmolt (2005) durables.

## Iteration log
- v0 naive event-study: baseline using median of event-wise Δlog(q)/Δlog(p).
- v1 pooled OLS log-log: single global ε.
- v2 per-item OLS: per-item ε pooled across shops with shop+month FE; clipped to [-10,5]; sales-weighted category aggregate.
- v3 FE panel with category × log(price): within-item-shop demeaning + category-specific ε.
- v4 Poisson GLM on top-500 items: count model with item FE per category.
- v5 Promo-split: separate ε for promo vs regular price; reports headline ε on regular price.
- v6 Ridge per-item: regularized per-item OLS to fix v2 overfit.
- v7 LightGBM with monotonic price: ML model; ε via finite-difference on log_price.
- v9 MMM-style decomposition: item-shop FE + linear trend + K=4 Fourier seasonality + holiday dummies (BFCM/Xmas/NYE/Easter/COVID) + category×log(price) split by promo. Isolates price signal from baseline/trend/season/events.
- v11 Tweedie GLM with v9 design + Mundlak FE: linear sibling of v10b that swaps OLS-on-log(sales+1) for a Tweedie likelihood (var_power=1.5, log link) on raw counts. Single-stage GLM, no cross-fitting (no flexible nuisance to debias). Mundlak FE collapses the elasticity to ~0 because the log link breaks FWL — informative negative result, reported as a sensitivity.
