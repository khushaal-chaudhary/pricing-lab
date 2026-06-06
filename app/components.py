"""Reusable HTML/Streamlit components: metric cards, pull-quotes, chips."""
from __future__ import annotations
from app.styles import PALETTE


def metric_card(label: str, value: str, foot: str = "",
                  *, accent: bool = False, tone: str = "ink",
                  cream: bool = False) -> str:
    """tone: 'ink' | 'red' | 'ok'; accent adds a red top edge; cream uses paper-2 bg."""
    klass = "card"
    if accent: klass += " accent"
    if cream: klass += " cream"
    val_klass = "metric-value"
    if tone == "red": val_klass += " red"
    elif tone == "ok": val_klass += " ok"
    foot_html = f'<div class="metric-delta">{foot}</div>' if foot else ""
    return f"""<div class="{klass}">
      <div class="metric-label">{label}</div>
      <div class="{val_klass}">{value}</div>
      {foot_html}
    </div>"""


def pull_quote(text: str) -> str:
    return f'<div class="pullquote">{text}</div>'


def chip(text: str, tone: str = "default") -> str:
    klass = "chip"
    if tone in ("red", "cool"): klass += f" {tone}"
    return f'<span class="{klass}">{text}</span>'
