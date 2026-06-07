"""Per-model explainer cards for the Leaderboard tab.

Content verified against the source-of-truth docs in the original directory
(leaderboard.md iteration log, ACTION_PLAN.md, slides.md). Anything not
attested in those files has been removed; v4-vs-v9 comparison numbers come
from our own compare_v4_v9.py run."""
from __future__ import annotations

# Order = composite rank from leaderboard.md (v9 first, v0 last).
ORDER = [
    "v9_mmm_light", "v7_lightgbm_monotone", "v5_promo_split",
    "v3_fe_category_interaction", "v10a_dml_log", "v10b_dml_tweedie",
    "v4_poisson_fe", "v1_pooled_ols", "v6_ridge_per_item",
    "v2_per_item_ols", "v0_naive_event",
]

CARDS: dict[str, dict[str, str]] = {
    "v9_mmm_light": {
        "tagline": "Marketing-Mix-Modelling-style decomposition - the headline winner.",
        "layman": (
            "Sales move for many reasons: brand baseline, slow growth over years, "
            "Christmas / Black Friday spikes, school holidays, AND price. "
            "If you regress sales on price alone, the price coefficient soaks up "
            "everything that happened to move with price - including January lulls "
            "and BFCM promo timing. v9 carves out every other driver first, then "
            "asks 'what is left for price to explain?' That residual is the elasticity."
        ),
        "features": (
            "Item-shop fixed effects + linear time trend + K=4 Fourier annual "
            "seasonality + holiday dummies (Black Friday / Cyber Monday / Christmas / "
            "NYE / Easter / COVID) + delivery_days + category x log(price) split by "
            "promo. Single OLS on log(sales+1); variance attribution comes from the "
            "design matrix, no per-item retraining. Per-item ε layered via v6 ridge "
            "for 2,976 items, v9 category fallback for the remaining 24."
        ),
        "result": (
            "Holdout R^2 = 0.56, 100% of categories negative, full 3,000-item coverage, "
            "tight CI (0.07). Median portfolio ε = -0.58. Composite = 0.82. "
            "Variance share: events 38% / season 33% / trend 25% / price 4%."
        ),
        "verdict": (
            "Wins on the full composite: decent prediction, perfect sign discipline, "
            "complete coverage, narrow uncertainty. Transparent partial-out makes it "
            "defensible to a VP without hand-waving. The headline number that ships."
        ),
    },
    "v7_lightgbm_monotone": {
        "tagline": "Gradient-boosted trees with a monotonic constraint on price.",
        "layman": (
            "A flexible ML model that can fit non-linear price effects, with a hard "
            "rule baked in: higher price can never predict higher units. The elasticity "
            "is recovered by nudging log_price up by 1% and reading off the change in "
            "predicted units (finite-difference)."
        ),
        "features": (
            "LightGBM with a monotonic constraint on log_price. ε reported via "
            "finite-difference on log_price."
        ),
        "result": (
            "Holdout R^2 = 0.54, 100% cats negative, coverage 2,999, CI 0.20. "
            "Composite = 0.80 (second place)."
        ),
        "verdict": (
            "Excellent predictor, wider CI because the elasticity comes from "
            "finite-differencing a learned surface rather than a closed-form coefficient. "
            "v9 wins for pricing because the coefficient is closed-form interpretable, "
            "not just the prediction."
        ),
    },
    "v5_promo_split": {
        "tagline": "Two slopes: regular-price elasticity vs promo elasticity.",
        "layman": (
            "Customers respond differently to an everyday price vs a 'red sticker' "
            "discount. v5 splits the price coefficient in two: a baseline ε for normal "
            "weeks and a separate ε for promo weeks. The headline ε is the regular-price "
            "slope; the promo coefficient is reported separately."
        ),
        "features": (
            "v3 FE-panel base + category x log(price) x promo interaction. Promo "
            "indicator built ourselves: is_promo = item_price_final below the trailing "
            "60-day item-shop median."
        ),
        "result": (
            "Holdout R^2 = 0.51, 100% cats negative, full coverage, CI 0.07. "
            "Composite = 0.80."
        ),
        "verdict": (
            "The promo-split logic survives into v9. v5 is essentially v9 minus the "
            "trend / seasonality / event decomposition, so it forecasts slightly less "
            "well but its price coefficient is comparable."
        ),
    },
    "v3_fe_category_interaction": {
        "tagline": "Within-item-shop variation with a category-specific price slope.",
        "layman": (
            "Forget cross-item comparisons - they are confounded by quality, brand, "
            "and positioning. v3 only uses how each item's sales move when ITS OWN "
            "price moves, and lets the slope vary by category (so sofas and lamps "
            "do not share an elasticity)."
        ),
        "features": (
            "Item-shop fixed effects + time FE + category x log(price) interaction. "
            "No seasonality, no events, no promo split."
        ),
        "result": (
            "Holdout R^2 = 0.50, 100% cats negative, full coverage, tightest CI of "
            "any model (0.055). Composite = 0.80."
        ),
        "verdict": (
            "Clean econometric baseline. The seasonality and event variance still "
            "leak into the residual; v5 / v9 add those controls and pick up R^2."
        ),
    },
    "v10a_dml_log": {
        "tagline": "Modern causal-ML: Double/Debiased ML with LightGBM nuisances (log target).",
        "layman": (
            "Same idea as v9 (partial everything else out, regress what is left), "
            "but the 'everything else' is learned by a non-linear ML model instead of "
            "a linear regression. In theory it captures arbitrary confounders. In "
            "practice, when log_price is collinear with promo and season, the ML "
            "nuisance over-absorbs price variation and the elasticity attenuates."
        ),
        "features": (
            "LightGBM nuisances for both Y (log-sales) and T (log-price); 5-fold "
            "cross-fitting (Chernozhukov 2018); effect modifier = main_category."
        ),
        "result": (
            "Holdout R^2 = 0.54, 88% cats negative, full coverage, CI 0.09. "
            "Median ε ~ -0.05. Composite = 0.76."
        ),
        "verdict": (
            "Robustness check, not headline. The -0.05 median is a known DML failure "
            "mode under weak treatment exogeneity (Chernozhukov 2018, §4.3): "
            "flexible nuisances steal the treatment signal. v9 + v10 together: truth "
            "is in [-0.58, -0.05], both negative, both inelastic."
        ),
    },
    "v10b_dml_tweedie": {
        "tagline": "DML variant: Tweedie nuisance on raw counts (handles zero-inflation).",
        "layman": (
            "Sales are zero ~90% of item-weeks. Logging needs a +1 shift that biases "
            "the slope (Silva and Tenreyro 2006). v10b uses a Tweedie objective on "
            "raw counts - the right likelihood for zero-inflated counts - and avoids "
            "the log shift entirely."
        ),
        "features": (
            "LightGBM with objective='tweedie' on raw sales count for the Y nuisance; "
            "otherwise identical to v10a."
        ),
        "result": (
            "Holdout R^2 = 0.55, 82% cats negative, full coverage, CI 0.105. "
            "Median ε ~ -0.22. Composite = 0.75."
        ),
        "verdict": (
            "Lands between v9 (-0.58) and v10a (-0.05). Suggests v9's log-shift "
            "explains some of the gap. Reported as a sensitivity, not headline - the "
            "DML attenuation issue still applies."
        ),
    },
    "v4_poisson_fe": {
        "tagline": "Poisson regression - count model with a log link, top-500 items only.",
        "layman": (
            "Sales are counts, not continuous. Poisson is the textbook count model "
            "and uses a log link, so the price coefficient IS the elasticity with no "
            "log-transformation needed. Restricted to the top-500 items because the "
            "MLE refuses to converge on items where most weeks are zero "
            "(quasi-separation)."
        ),
        "features": (
            "Poisson GLM with log link on raw sales counts; item fixed effects per "
            "category; fitted on the top-500 items only."
        ),
        "result": (
            "Holdout R^2 = 0.62 (highest of any model), 100% cats negative, but "
            "coverage only 500 items, CI 0.21. Composite = 0.67. "
            "Head-to-head with v9 on the 500-item overlap (our compare_v4_v9.py): "
            "sign agrees 100% (500/500 items, 15/15 cats); Spearman rank 0.35 across "
            "cats; median |ε| = 2.30 (vs v9 0.58 - a ~4x magnitude gap)."
        ),
        "verdict": (
            "Cleanest signal on a narrow slice. Sign and rank order agree with v9 "
            "but magnitude is ~4x stronger - likely because Poisson handles the "
            "zero-inflation natively while v9 attenuates from the log+1 shift "
            "(Silva and Tenreyro 2006). Useful as an UPPER-bound: v9 -0.58 lower "
            "bound, v4 -2.30 upper bound, truth plausibly -1.0 to -1.5 (inside the "
            "Bijmolt 2005 durables range)."
        ),
    },
    "v1_pooled_ols": {
        "tagline": "Single global elasticity across all items and shops - the strawman.",
        "layman": (
            "Throw every item, every shop, every week into one regression. One number "
            "for the elasticity of furniture. Useful as a sanity baseline; useless as "
            "an actionable pricing signal because it averages a 8,000 EUR sofa with a "
            "15 EUR lamp."
        ),
        "features": (
            "log(sales+1) ~ log(price) + delivery_days + day-of-week + month. "
            "No item or shop fixed effects."
        ),
        "result": (
            "Holdout R^2 = -0.03, sign negative, full coverage, CI tiny but meaningless. "
            "Composite = 0.60."
        ),
        "verdict": (
            "Establishes the floor: anything that does not beat pooled OLS on R^2 "
            "is not adding value over the most naive specification."
        ),
    },
    "v6_ridge_per_item": {
        "tagline": "Per-item OLS with ridge regularisation to tame v2's overfit.",
        "layman": (
            "v2 fit a separate slope per item and overfit catastrophically (R^2 = -201). "
            "v6 adds a ridge penalty: pull every per-item slope toward the prior (zero) "
            "unless the data really demands otherwise."
        ),
        "features": (
            "Per-item log-log regression with an L2 (ridge) penalty on the slope. "
            "Same per-item structure as v2, with regularisation as the only change."
        ),
        "result": (
            "Holdout R^2 = -0.29, 100% cats negative, coverage 2,985, very wide CI "
            "(0.99). Composite = 0.55."
        ),
        "verdict": (
            "Demonstrates why per-item modelling is fragile on sparse furniture data - "
            "even with regularisation, most items lack the within-item price variation "
            "needed to identify an elasticity. v9 still uses v6's per-item slopes for "
            "the 2,976 items where they survive sign-validation, and falls back to the "
            "v9 category ε for the remaining 24."
        ),
    },
    "v2_per_item_ols": {
        "tagline": "Per-item OLS with no regularisation - the cautionary tale.",
        "layman": (
            "A separate regression per item. Sounds principled (every item is unique!), "
            "is actually catastrophic: most items have 20-50 weekly observations and the "
            "fit picks up pure noise. The holdout R^2 of -201 means predictions are "
            "200x worse than just predicting the mean."
        ),
        "features": (
            "Per-item: log_sales ~ log_price + shop FE + month FE. ε clipped to "
            "[-10, 5] to suppress the worst overfits; reported as a sales-weighted "
            "category aggregate."
        ),
        "result": (
            "Holdout R^2 = -201, 100% cats negative (after clipping), CI 1.19. "
            "Composite = 0.54."
        ),
        "verdict": (
            "The textbook example of why you POOL information across items in low-N "
            "settings. v6 ridges this; v3 onward pools entirely. v2 is in the leaderboard "
            "to make the failure visible."
        ),
    },
    "v0_naive_event": {
        "tagline": "Event-study median: Δlog(q) / Δlog(p) around price changes.",
        "layman": (
            "No model. For every week where price changed, compute the ratio of the "
            "log-sales change to the log-price change; take the median across all such "
            "events, by category. The most naive possible 'elasticity' you can write down."
        ),
        "features": (
            "Pre/post window means around each price-change event; log-ratio aggregated "
            "by category. No controls."
        ),
        "result": (
            "Holdout R^2 = NaN (not a forecasting model), 0% cats negative (median "
            "ratio happens to be positive - face-validity failure). Composite = 0.25."
        ),
        "verdict": (
            "Confirms why naive approaches fail: any week with a price change is also "
            "a week with a promo or seasonal shift, so the ratio captures everything "
            "EXCEPT the elasticity. Establishes the no-model baseline."
        ),
    },
}


def render_card(model: str) -> str:
    """Return styled HTML for one model's explainer card."""
    c = CARDS.get(model, {})
    if not c:
        return f'<div class="card"><div class="metric-label">{model}</div><div>(no explainer)</div></div>'
    return f"""
<div class="card" style="padding:24px 28px;">
  <div class="metric-label" style="color:var(--red);">{model}</div>
  <div style="font-family:var(--t-display); font-size:22px; font-style:italic;
              color:var(--ink); line-height:1.3; margin:6px 0 18px 0;">
    {c['tagline']}
  </div>
  <div class="metric-label" style="margin-top:6px;">In plain English</div>
  <div style="font-size:14px; color:var(--ink); line-height:1.6; margin-bottom:14px;">{c['layman']}</div>
  <div class="metric-label">Features &amp; treatment</div>
  <div style="font-size:13.5px; color:var(--ink-2); line-height:1.6; margin-bottom:14px;">{c['features']}</div>
  <div class="metric-label">Result</div>
  <div style="font-size:13.5px; color:var(--ink-2); line-height:1.6; margin-bottom:14px;">{c['result']}</div>
  <div class="metric-label" style="color:var(--red);">Verdict vs v9</div>
  <div style="font-size:13.5px; color:var(--ink); line-height:1.6; font-weight:500;">{c['verdict']}</div>
</div>
"""
