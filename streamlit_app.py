"""home24 Pricing Lab - single-page dashboard with 5 tabs.

Unlisted deploy: password gate against st.secrets['APP_PASSWORD'] (default 'home24-2026').
Set the secret in Streamlit Cloud > App > Settings > Secrets.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="home24 - Pricing Lab",
                    page_icon=":red_circle:",
                    layout="wide",
                    initial_sidebar_state="expanded")

from app.styles import inject, PALETTE
from app.lib import (load_reconciled, load_final, load_cat_v9, load_leaderboard,
                       load_variance_share, load_slides, entity_catalogue,
                       get_eps, get_promo_eps, baseline_for, demand_curve,
                       revenue_curve, confidence_band)
from app.charts import (variance_share_donut, leaderboard_bars,
                          category_elasticity_bars, demand_curve_fig,
                          revenue_curve_fig)
from app.components import metric_card, pull_quote, chip


# ---- Password gate ---------------------------------------------------------
def _gate() -> bool:
    try: target = st.secrets["APP_PASSWORD"]
    except Exception: target = "home24-2026"
    if st.session_state.get("auth_ok"): return True
    inject(st, subtitle="Restricted preview")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Single HTML block for the headline + helper text. Widgets render as
        # separate Streamlit elements *below*, so wrapping them in a <div class="card">
        # produces an empty bordered box — that's the artefact you saw. Render the
        # text as one editorial block; let the inputs sit underneath cleanly.
        st.markdown(
            '<div style="margin-top:3rem; border-left:2px solid var(--red); '
            'padding:4px 0 4px 18px; margin-bottom:18px;">'
            '<div class="metric-label" style="margin-bottom:6px;">Access</div>'
            '<div style="font-family:var(--t-display); font-size:22px; font-style:italic; '
            'color:var(--ink); line-height:1.3; margin-bottom:8px;">Restricted preview.</div>'
            '<div style="font-size:14px; color:var(--ink-2); line-height:1.5;">'
            'Enter the access code from the cover letter.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        pw = st.text_input("Access code", type="password", label_visibility="collapsed",
                            placeholder="Access code")
        if st.button("Enter", type="primary"):
            if pw == target:
                st.session_state["auth_ok"] = True
                st.rerun()
            else:
                st.error("Incorrect code.")
    return False


if not _gate():
    st.stop()


# ---- Sidebar (drives every tab) -------------------------------------------
inject(st, subtitle="Khushaal Chaudhary - Sales Forecasting case study")
cat = entity_catalogue()

with st.sidebar:
    st.markdown("### Aggregation level")
    level = st.radio("Aggregation level",
                      ["portfolio", "main_category", "sub_category", "item"],
                      index=1, label_visibility="collapsed",
                      format_func=lambda x: x.replace("_", " ").title())
    options = cat.get(level, []) or ["portfolio"]
    n_opts = len(options)
    st.markdown(f"### Entity  <span class='chip'>{n_opts:,}</span>", unsafe_allow_html=True)
    entity = st.selectbox(
        "Entity",
        options,
        index=0,
        label_visibility="collapsed",
        placeholder=f"Search {level.replace('_',' ')}s ({n_opts:,})...",
        help="Type to filter. Dropdown auto-completes as you type.",
    )
    # Promo ε is fitted only at main_category in v9 (separate log-price slope
    # for discount weeks). For item / sub_cat we *inherit* the parent main_cat's
    # promo ε — same logic as category fixed effects. The simulator badges the
    # inheritance so it's never confused with a child-level estimate.
    st.markdown("### Promo state")
    promo = st.toggle("On promotion", value=False,
                       help="Switch ε to the promo coefficient. v9 fits promo ε at "
                            "main_category; item / sub_category inherit from the parent.")
    st.markdown("---")
    st.markdown("### Notes")
    st.caption(
        "Reconciled elasticities (MinT, Wickramasuriya 2019) are coherent across "
        "portfolio / main / sub / item levels. Headline category numbers come from "
        "v9 (MMM-style decomposition); per-item from v6 ridge with sign-fallback."
    )


# ---- Tabs ------------------------------------------------------------------
tab_story, tab_lead, tab_mmm, tab_sim, tab_method = st.tabs(
    ["Story", "Leaderboard", "MMM decomposition", "Elasticity simulator", "Methodology"]
)


# === STORY =================================================================
with tab_story:
    slides = load_slides()
    n = len(slides)
    if "slide_i" not in st.session_state: st.session_state["slide_i"] = 0
    i = max(0, min(st.session_state["slide_i"], n - 1))
    col_a, col_b, col_c = st.columns([1, 6, 1])
    with col_a:
        if st.button("Prev", disabled=(i == 0)):
            st.session_state["slide_i"] = i - 1; st.rerun()
    with col_c:
        if st.button("Next", disabled=(i >= n - 1)):
            st.session_state["slide_i"] = i + 1; st.rerun()
    with col_b:
        st.markdown(f'<div class="eyebrow" style="text-align:center;">Slide {i+1} / {n}</div>',
                     unsafe_allow_html=True)
    # Streamlit closes each markdown call as its own DOM block, so wrapping
    # st.markdown(slides[i]) between two raw <div> markdowns produces an empty
    # bordered box. Use st.container(border=True) — native Streamlit border that
    # actually contains the children — then scope a class via the wrapping span.
    with st.container(border=True):
        st.markdown(slides[i], unsafe_allow_html=False)
    st.caption("Slides re-read from slides.md on every render - edit the file and refresh.")


# === LEADERBOARD ===========================================================
with tab_lead:
    lb = load_leaderboard()
    st.markdown("## Model leaderboard")
    st.markdown(
        '<p>Composite score balances predictive R<sup>2</sup>, face-validity '
        '(% categories with negative elasticity), portfolio coverage, and stability. '
        'See methodology tab for the formula and weights.</p>',
        unsafe_allow_html=True
    )
    c1, c2 = st.columns([3, 2])
    with c1:
        st.plotly_chart(leaderboard_bars(lb, "composite"), use_container_width=True)
    with c2:
        st.dataframe(
            lb[["model", "holdout_r2", "pct_cat_neg", "coverage_items", "composite"]],
            hide_index=True, use_container_width=True
        )
    st.markdown(pull_quote(
        "v9 wins not on R&sup2; alone (v8 LightGBM beats it) but on elasticity "
        "credibility - the price coefficient survives after seasonality and events "
        "are partialed out."
    ), unsafe_allow_html=True)


# === MMM DECOMPOSITION =====================================================
with tab_mmm:
    st.markdown("## Variance share at the weekly portfolio level")
    st.markdown(
        '<p>v9 decomposes log(sales+1) into baseline + trend + seasonality + events + price. '
        'Across the panel, calendar effects dominate price as a driver of weekly volume.</p>',
        unsafe_allow_html=True
    )
    shares = load_variance_share()
    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(variance_share_donut(shares), use_container_width=True)
    with c2:
        st.markdown(metric_card("Events share", f"{shares.get('events', 0):.1f}%",
                                  foot="Black Friday / Christmas / NYE / Easter / COVID"),
                      unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(metric_card("Seasonality share", f"{shares.get('season', 0):.1f}%",
                                  foot="K=4 annual Fourier harmonics"),
                      unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(metric_card("Price share", f"{shares.get('price', 0):.1f}%",
                                  foot="What's left after the calendar is taken out",
                                  accent=True, tone="red"),
                      unsafe_allow_html=True)
    st.markdown("## Per-category elasticities (v9)")
    cat_v9 = load_cat_v9()
    st.plotly_chart(category_elasticity_bars(cat_v9), use_container_width=True)


# === ELASTICITY SIMULATOR (headline) =======================================
with tab_sim:
    st.markdown(f"## Elasticity simulator - {level.replace('_', ' ')} / {entity}")
    eps, se = get_eps(level, entity)
    p_now, q_now, label = baseline_for(level, entity)
    # promo toggle: swap regular eps for the promo coefficient. v9 fits promo ε
    # at main_category only; item / sub_cat inherit from the parent main_cat
    # (category-FE inheritance — flagged in the badge below).
    promo_active = False
    promo_inherited_from = None
    eps_regular = eps
    if promo:
        promo_val, parent = get_promo_eps(level, entity)
        if promo_val is not None:
            eps = promo_val
            promo_active = True
            if level != "main_category":
                promo_inherited_from = parent

    # Observed price-variation support in the panel was [-30%, +43%] (5-95th pct).
    # Constant-elasticity demand q = q0 * (p/p0)^eps EXTRAPOLATES linearly in log
    # space - reliable only inside the observed range. We clamp the slider to
    # the empirical support and visually flag out-of-support territory.
    SUPPORT_LO, SUPPORT_HI = -25, 30
    delta = st.slider(
        "Price change (%) - clamped to observed price variation",
        -40, 50, 0, step=1, format="%d%%",
        help=(
            "Calibrated to the 5-95th percentile price variation in the panel "
            "(approx. -30% to +43%). Beyond this band the constant-elasticity "
            "extrapolation is unreliable and is visually shaded as out-of-support."
        ),
    )
    p_sim = p_now * (1 + delta / 100.0)
    q_sim = q_now * (p_sim / p_now) ** eps
    r_now = p_now * q_now; r_sim = p_sim * q_sim

    # Regime explainer - addresses "is positive ε somehow?" confusion
    regime = "inelastic" if -1 < eps < 0 else ("elastic" if eps <= -1 else "anomalous")
    rev_eps = 1 + eps  # revenue elasticity wrt price
    if regime == "inelastic":
        banner = (f"<b>Inelastic regime</b> (|ε| &lt; 1). Price ε = <code>{eps:+.2f}</code> "
                  f"but revenue ε = <code>{rev_eps:+.2f}</code> &mdash; so a price increase "
                  f"<i>raises</i> revenue (textbook: low ε ⇒ pricing power).")
        tone = "red"
    elif regime == "elastic":
        banner = (f"<b>Elastic regime</b> (|ε| ≥ 1). Price ε = <code>{eps:+.2f}</code>, "
                  f"revenue ε = <code>{rev_eps:+.2f}</code> &mdash; a price <i>cut</i> raises revenue.")
        tone = "cool"
    else:
        banner = (f"<b>Anomalous</b>: ε = <code>{eps:+.2f}</code> is non-negative. "
                  f"Treat with caution; this entity has insufficient or confounded price signal.")
        tone = "default"
    promo_prefix = ""
    if promo_active:
        inherit_note = (f" &middot; inherited from <b>{promo_inherited_from}</b>"
                        if promo_inherited_from else "")
        promo_prefix = (
            f'<div style="font-size:12px;color:var(--red);font-weight:600;'
            f'letter-spacing:0.04em;text-transform:uppercase;margin-bottom:4px;">'
            f'Switched to promo ε (regular ε was <code>{eps_regular:+.2f}</code>){inherit_note}'
            f'</div>'
        )
    st.markdown(
        f'<div class="card cream" style="margin: 12px 0 18px 0;">'
        f'<div class="metric-label">Regime diagnosis</div>'
        f'{promo_prefix}'
        f'<div style="font-size:14px;color:var(--ink);line-height:1.5;margin-top:6px;">{banner}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Extrapolation warning when slider leaves observed support
    if delta < SUPPORT_LO or delta > SUPPORT_HI:
        st.markdown(
            f'<div class="card" style="margin: 0 0 14px 0; border-color: var(--warn);">'
            f'<div class="metric-label" style="color: var(--warn);">Extrapolation warning</div>'
            f'<div style="font-size:13.5px;color:var(--ink-2);margin-top:4px;line-height:1.5;">'
            f'A price change of <code>{delta:+d}%</code> is outside the observed '
            f'<code>{SUPPORT_LO}%</code> to <code>{SUPPORT_HI}%</code> range used to fit ε. '
            f'The constant-elasticity model assumes log-linearity to infinity, which is unrealistic: '
            f'competitor response, reference-price effects, and category substitution all kick in at large moves. '
            f'Treat the projection beyond the support band as <em>directional</em>, not as a forecast.'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    # cards row
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(metric_card("Elasticity (ε)", f"{eps:+.2f}",
                                       foot=f"95% CI ±{1.96*se:.2f}",
                                       accent=True, tone="red"), unsafe_allow_html=True)
    with c2: st.markdown(metric_card("Predicted units", f"{q_sim:,.0f}",
                                       foot=f"vs {q_now:,.0f} now ({(q_sim/q_now-1)*100:+.1f}%)"),
                          unsafe_allow_html=True)
    with c3: st.markdown(metric_card("Predicted revenue", f"{r_sim:,.0f}",
                                       foot=f"Δ vs status quo: {(r_sim-r_now):+,.0f}",
                                       tone="ok" if r_sim > r_now else "red"),
                          unsafe_allow_html=True)
    with c4:
        action = ("Raise price" if eps > -1 and delta == 0
                  else "Hold" if abs(delta) < 1
                  else ("Net positive" if r_sim > r_now else "Net negative"))
        st.markdown(metric_card("Verdict", action,
                                  foot=("inelastic - room to raise" if eps > -1 else
                                         "elastic - discount may pay off")),
                      unsafe_allow_html=True)

    # curves
    p_grid = np.linspace(p_now * 0.5, p_now * 1.5, 121)
    q_grid = demand_curve(eps, p_now, q_now, p_grid)
    q_lo, q_hi = confidence_band(eps, se, p_now, q_now, p_grid)
    r_grid = revenue_curve(p_grid, q_grid)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="eyebrow">Demand</div>', unsafe_allow_html=True)
        st.plotly_chart(demand_curve_fig(p_grid, q_grid, q_lo, q_hi,
                                            p_now, q_now, p_sim, q_sim,
                                            SUPPORT_LO, SUPPORT_HI),
                          use_container_width=True)
    with c2:
        st.markdown('<div class="eyebrow">Revenue</div>', unsafe_allow_html=True)
        st.plotly_chart(revenue_curve_fig(p_grid, r_grid, p_now, r_now, p_sim, r_sim,
                                              SUPPORT_LO, SUPPORT_HI),
                          use_container_width=True)

    st.markdown(pull_quote(
        f"At {label}, an elasticity of {eps:+.2f} means a 10% price increase reduces "
        f"weekly units by {10*abs(eps):.1f}% and changes revenue by "
        f"{((1.1**(eps+1))-1)*100:+.1f}%."
    ), unsafe_allow_html=True)


# === METHODOLOGY ===========================================================
with tab_method:
    st.markdown("## Methodology")
    st.markdown(
        '<p>The pipeline ships v0 through v10b (eleven models). v9 - an MMM-style '
        'decomposition with item-shop fixed effects, K=4 Fourier annual seasonality, '
        'holiday dummies, and a category-level log-log price coefficient - wins the '
        'composite leaderboard. v10a (DML with LightGBM nuisance and 5-fold cross-fitting) '
        'and v10b (DML with Tweedie y-stage on raw counts) provide modern causal-ML '
        'counterparts as a robustness check.</p>',
        unsafe_allow_html=True
    )
    st.markdown("### Composite metric")
    st.code("composite = 0.4 * R^2 + 0.3 * (% cats eps<0) + 0.2 * coverage/3000 + 0.1 * (1 - CI/2)")
    st.markdown(
        '<p>R<sup>2</sup> gets the biggest weight but not a dominant one - a model that '
        'forecasts well via autoregressive features can still produce a worthless price '
        'coefficient. The other three terms guard against that failure mode.</p>',
        unsafe_allow_html=True
    )
    st.markdown("### Hierarchical reconciliation")
    st.markdown(
        '<p>Independently-estimated elasticities at item / sub-category / main-category / '
        'portfolio levels are <em>incoherent</em>: the sales-weighted average of item '
        'elasticities within a category does not equal the directly-estimated category '
        'elasticity. MinT reconciliation (Wickramasuriya, Athanasopoulos &amp; Hyndman 2019) '
        'projects all level estimates onto the linear constraint set while minimising '
        'trace variance. The dashboard surfaces reconciled numbers - so the same item ε '
        'aggregates exactly to the category headline.</p>',
        unsafe_allow_html=True
    )
