"""Plotly figure factories. Every figure uses styles.plotly_layout() so the
chart system stays cohesive with the editorial design language."""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from app.styles import plotly_layout, PALETTE, CHART_PALETTE


def _apply(fig: go.Figure, *, height: int = 360) -> go.Figure:
    fig.update_layout(**plotly_layout(), height=height)
    # Force-clear any title — plotly renders the JS literal "undefined" when
    # title is None/unset on some versions.
    fig.update_layout(title_text="", title_font_size=1)
    # Ensure every trace has a string name (None → "undefined" in legend).
    for tr in fig.data:
        if getattr(tr, "name", None) is None:
            tr.name = ""
    return fig


def variance_share_donut(shares: dict[str, float]) -> go.Figure:
    labels = list(shares.keys()); values = list(shares.values())
    colors = [PALETTE["ink"], PALETTE["ink_2"], PALETTE["ink_3"], PALETTE["red"]][:len(labels)]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=colors, line=dict(color=PALETTE["paper"], width=2)),
        textinfo="label+percent",
        textfont=dict(family="Geist Mono", size=12, color=PALETTE["ink"]),
        sort=False, direction="clockwise",
    ))
    return _apply(fig, height=320)


def leaderboard_bars(df: pd.DataFrame, metric: str = "composite") -> go.Figure:
    df = df.sort_values(metric, ascending=True)
    headline_pair = {"v9_mmm_light", "v12_poisson_fe"}
    colors = [PALETTE["red"] if m in headline_pair else PALETTE["ink_2"]
              for m in df["model"]]
    fig = go.Figure(go.Bar(
        x=df[metric], y=df["model"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.3f}" for v in df[metric]],
        textposition="outside", textfont=dict(family="Geist Mono", size=11),
        hovertemplate="<b>%{y}</b><br>" + metric + "=%{x:.3f}<extra></extra>",
    ))
    fig.update_xaxes(title_text=metric)
    fig.update_yaxes(title_text="")
    return _apply(fig, height=380)


def category_elasticity_bars(cat_df: pd.DataFrame) -> go.Figure:
    df = cat_df.sort_values("elasticity")
    fig = go.Figure()
    fig.add_bar(
        x=df["elasticity"], y=df["main_category"], orientation="h",
        marker=dict(color=PALETTE["red"], line=dict(width=0)),
        name="regular ε",
        text=[f"{v:.2f}" for v in df["elasticity"]],
        textposition="outside", textfont=dict(family="Geist Mono", size=11),
    )
    if "promo_elasticity" in df.columns:
        fig.add_bar(
            x=df["promo_elasticity"], y=df["main_category"], orientation="h",
            marker=dict(color=PALETTE["ink"], line=dict(width=0)),
            name="promo ε", opacity=0.55,
        )
    fig.update_layout(barmode="overlay", legend=dict(orientation="h", y=-0.18))
    fig.add_vline(x=-1, line=dict(color=PALETTE["cool"], width=1, dash="dot"))
    fig.add_annotation(x=-1, y=1.02, yref="paper", text="unit-elastic", showarrow=False,
                       font=dict(family="Geist Mono", size=10, color=PALETTE["cool"]))
    return _apply(fig, height=460)


def _add_support_shade(fig: go.Figure, p_now: float,
                         support_lo_pct: float, support_hi_pct: float) -> None:
    """Shade the price region outside the observed empirical support."""
    p_lo = p_now * (1 + support_lo_pct / 100.0)
    p_hi = p_now * (1 + support_hi_pct / 100.0)
    fig.add_vrect(x0=p_now * 0.5, x1=p_lo,
                  fillcolor="rgba(182, 92, 0, 0.06)", line_width=0, layer="below")
    fig.add_vrect(x0=p_hi, x1=p_now * 1.6,
                  fillcolor="rgba(182, 92, 0, 0.06)", line_width=0, layer="below")
    fig.add_vline(x=p_lo, line=dict(color=PALETTE["warn"], width=1, dash="dot"))
    fig.add_vline(x=p_hi, line=dict(color=PALETTE["warn"], width=1, dash="dot"))
    fig.add_annotation(x=p_lo, y=1.04, yref="paper", text="observed support",
                        showarrow=False, xanchor="left",
                        font=dict(family="Geist Mono", size=10, color=PALETTE["warn"]))


def demand_curve_fig(p_grid: np.ndarray, q_grid: np.ndarray, q_lo: np.ndarray, q_hi: np.ndarray,
                      p_now: float, q_now: float, p_sim: float, q_sim: float,
                      support_lo_pct: float = -25, support_hi_pct: float = 30) -> go.Figure:
    fig = go.Figure()
    _add_support_shade(fig, p_now, support_lo_pct, support_hi_pct)
    # CI band
    fig.add_trace(go.Scatter(
        x=np.concatenate([p_grid, p_grid[::-1]]),
        y=np.concatenate([q_hi, q_lo[::-1]]),
        fill="toself", fillcolor="rgba(230,0,35,0.10)", line=dict(width=0),
        name="95% CI", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=p_grid, y=q_grid, mode="lines",
        line=dict(color=PALETTE["red"], width=2.5), name="demand q(p)",
        hovertemplate="p=%{x:.2f}<br>q=%{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[p_now], y=[q_now], mode="markers+text",
        marker=dict(color=PALETTE["ink"], size=10, symbol="circle"),
        text=["current"], textposition="top right",
        textfont=dict(family="Geist Mono", size=10, color=PALETTE["ink"]),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=[p_sim], y=[q_sim], mode="markers+text",
        marker=dict(color=PALETTE["red"], size=12, symbol="diamond",
                     line=dict(width=2, color=PALETTE["paper"])),
        text=["simulated"], textposition="top right",
        textfont=dict(family="Geist Mono", size=10, color=PALETTE["red"]),
        showlegend=False, hoverinfo="skip",
    ))
    fig.update_xaxes(title="price (relative)")
    fig.update_yaxes(title="weekly units")
    return _apply(fig, height=380)


def revenue_curve_fig(p_grid: np.ndarray, r_grid: np.ndarray,
                       p_now: float, r_now: float, p_sim: float, r_sim: float,
                       support_lo_pct: float = -25, support_hi_pct: float = 30) -> go.Figure:
    fig = go.Figure()
    _add_support_shade(fig, p_now, support_lo_pct, support_hi_pct)
    fig.add_trace(go.Scatter(
        x=p_grid, y=r_grid, mode="lines",
        line=dict(color=PALETTE["ink"], width=2.5), name="revenue R(p)",
        fill="tozeroy", fillcolor="rgba(12,12,13,0.04)",
        hovertemplate="p=%{x:.2f}<br>R=%{y:.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[p_now], y=[r_now], mode="markers", marker=dict(color=PALETTE["ink"], size=9),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=[p_sim], y=[r_sim], mode="markers", marker=dict(color=PALETTE["red"], size=11, symbol="diamond"),
        showlegend=False, hoverinfo="skip",
    ))
    fig.update_xaxes(title="price (relative)")
    fig.update_yaxes(title="weekly revenue")
    return _apply(fig, height=380)
