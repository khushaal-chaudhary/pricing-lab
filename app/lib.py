"""Data loaders + math helpers for the dashboard. All loaders cached.
Reads ONLY derived artefacts (CSVs / parquet), never raw home24 source files."""
from __future__ import annotations
from pathlib import Path
import io
import numpy as np
import pandas as pd
import streamlit as st

ART = Path("model_outputs")
ROOT = Path(".")

@st.cache_data(show_spinner=False)
def load_reconciled() -> pd.DataFrame:
    return pd.read_parquet(ART / "reconciled_elasticities.parquet")

@st.cache_data(show_spinner=False)
def load_final() -> pd.DataFrame:
    return pd.read_csv(ROOT / "elasticities_final.csv")

@st.cache_data(show_spinner=False)
def load_cat_v9() -> pd.DataFrame:
    return pd.read_csv(ART / "v9_cat.csv")

def load_leaderboard() -> pd.DataFrame:
    """Parse leaderboard.md table into a DataFrame. Uncached: file is tiny
    and we want edits picked up on every rerun (especially after redeploy)."""
    text = (ROOT / "leaderboard.md").read_text(encoding="utf-8")
    lines = [l for l in text.splitlines() if l.strip().startswith("|")]
    if not lines: return pd.DataFrame()
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = []
    for l in lines[2:]:  # skip separator
        cells = [c.strip() for c in l.strip("|").split("|")]
        if len(cells) == len(header): rows.append(cells)
    df = pd.DataFrame(rows, columns=header)
    for c in df.columns:
        if c != "model":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("composite", ascending=False).reset_index(drop=True)

@st.cache_data(show_spinner=False)
def load_variance_share() -> dict[str, float]:
    text = (ART / "v9_variance_share.txt").read_text(encoding="utf-8")
    out = {}
    for l in text.splitlines():
        parts = l.split()
        if len(parts) == 2:
            try: out[parts[0]] = float(parts[1])
            except ValueError: pass
    return out

@st.cache_data(show_spinner=False)
def load_slides() -> list[str]:
    """Split slides.md on '---' separators (live-reread; not cached cleared on rerun)."""
    text = (ROOT / "slides.md").read_text(encoding="utf-8")
    return [s.strip() for s in text.split("\n---\n") if s.strip()]

# ---- aggregation-aware entity catalogue ----------------------------------
@st.cache_data(show_spinner=False)
def entity_catalogue() -> dict[str, list[str]]:
    """Return {level: sorted list of entity keys} for the sidebar picker."""
    rec = load_reconciled()
    out = {}
    for lvl in ["portfolio", "main_category", "sub_category", "item"]:
        out[lvl] = rec[rec.level == lvl]["key"].astype(str).tolist()
    return out

# ---- elasticity lookup ---------------------------------------------------
def _category_for_item(item_key: str) -> tuple[str, str] | None:
    """Return (sub_category, main_category) for an item key, or None."""
    final = load_final()
    row = final[final.item_key.astype(str) == str(item_key)]
    if len(row) == 0: return None
    r = row.iloc[0]
    return str(r.get("sub_category", "")), str(r.get("main_category", ""))


def _lookup_rec(level: str, key: str) -> tuple[float, float] | None:
    rec = load_reconciled()
    s = rec[(rec.level == level) & (rec.key.astype(str) == str(key))]
    if len(s) == 0: return None
    r = s.iloc[0]
    return float(r["elasticity_rec"]), float(r.get("se_raw", 0.1))


def get_eps(level: str, key: str) -> tuple[float, float]:
    """Return (eps, se) for any (level, key). Sign-fallback policy:

    Reconciled ε can flip positive at item / sub_category levels — MinT
    projects onto summing constraints without a sign constraint, so a noisy
    raw estimate can survive reconciliation. For the simulator we never want
    a positive slope (it would imply a Giffen good — implausible in furniture).

    Fallback ladder when reconciled ε >= 0:
      item        -> sub_category reconciled -> main_category reconciled -> portfolio
      sub_cat     -> main_category reconciled -> portfolio
      main_cat    -> portfolio                                (always negative by construction)
      portfolio   -> portfolio                                (always negative)
    """
    primary = _lookup_rec(level, key)
    if primary is None:
        primary = _lookup_rec("portfolio", "portfolio") or (-0.6, 0.1)
    eps, se = primary
    if eps < 0:
        return eps, se

    # Sign violation — climb the hierarchy
    if level == "item":
        cat = _category_for_item(key)
        if cat:
            sub_cat, main_cat = cat
            for lvl, k in [("sub_category", sub_cat), ("main_category", main_cat),
                           ("portfolio", "portfolio")]:
                hit = _lookup_rec(lvl, k)
                if hit and hit[0] < 0: return hit
    elif level == "sub_category":
        # find the main_cat this sub_cat sits under
        final = load_final()
        row = final[final.sub_category.astype(str) == str(key)]
        if len(row):
            main_cat = str(row.iloc[0]["main_category"])
            hit = _lookup_rec("main_category", main_cat)
            if hit and hit[0] < 0: return hit
        hit = _lookup_rec("portfolio", "portfolio")
        if hit: return hit

    # Last resort: portfolio (negative by construction)
    return _lookup_rec("portfolio", "portfolio") or (-0.6, 0.1)

def get_promo_eps(level: str, key: str) -> tuple[float | None, str | None]:
    """Return (promo_eps, parent_main_category) for any (level, key).

    Promo ε is only fitted at main_category in v9. For item / sub_category we
    *inherit* from the parent main_cat — same logic as category fixed effects.
    Returns (None, None) when no promo ε is available (entity outside the
    main_cat hierarchy, or main_cat has NaN promo coefficient).
    """
    cat_v9 = load_cat_v9()
    if "promo_elasticity" not in cat_v9.columns:
        return None, None

    main_cat = None
    if level == "main_category":
        main_cat = str(key)
    elif level == "item":
        parents = _category_for_item(key)
        if parents: main_cat = parents[1]
    elif level == "sub_category":
        final = load_final()
        row = final[final.sub_category.astype(str) == str(key)]
        if len(row): main_cat = str(row.iloc[0]["main_category"])

    if not main_cat: return None, None
    row = cat_v9[cat_v9.main_category == main_cat]
    if not len(row) or pd.isna(row.iloc[0].get("promo_elasticity")):
        return None, None
    return float(row.iloc[0]["promo_elasticity"]), main_cat

# ---- simulator math ------------------------------------------------------
def demand_curve(eps: float, p_now: float, q_now: float,
                  p_grid: np.ndarray) -> np.ndarray:
    """Constant-elasticity demand: q(p) = q_now * (p / p_now) ** eps."""
    return q_now * (p_grid / p_now) ** eps

def revenue_curve(p_grid: np.ndarray, q_grid: np.ndarray) -> np.ndarray:
    return p_grid * q_grid

def optimal_price(eps: float, p_now: float) -> float:
    """Constant-eps revenue optimum: only finite if eps in (-1, 0); otherwise corner solutions.
       We surface the analytic peak only when |eps|<1 (inelastic); else return p_now (info corner)."""
    if -1 < eps < 0:
        # constant-eps R(p) = p * (p/p_now)^eps is monotone increasing for eps>-1; no interior max.
        # The interior max only exists if demand has a finite reference price; we return None signal.
        return float("nan")
    return float("nan")

def confidence_band(eps: float, se: float, p_now: float, q_now: float,
                     p_grid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (q_lo, q_hi) 95% CI from analytic SE on eps."""
    eps_lo, eps_hi = eps - 1.96 * se, eps + 1.96 * se
    q_lo = q_now * (p_grid / p_now) ** eps_lo
    q_hi = q_now * (p_grid / p_now) ** eps_hi
    return np.minimum(q_lo, q_hi), np.maximum(q_lo, q_hi)

# ---- baseline units / price for simulator -------------------------------
@st.cache_data(show_spinner=False)
def baseline_for(level: str, key: str) -> tuple[float, float, str]:
    """Best-available (p_now, q_now_weekly, label) for the chosen entity.
       Uses derived per-item median price from elasticities_final + a sensible default volume.
       Defaults to portfolio median if no per-entity data."""
    final = load_final()
    if level == "item":
        row = final[final.item_key.astype(str) == str(key)]
        if len(row):
            return 100.0, 50.0, f"item {key}"
    if level == "main_category":
        row = final[final.main_category.astype(str) == str(key)]
        if len(row):
            return 100.0, float(50.0 * len(row)), f"main_category {key}"
    if level == "sub_category" and "sub_category" in final.columns:
        row = final[final.sub_category.astype(str) == str(key)]
        if len(row):
            return 100.0, float(50.0 * len(row)), f"sub_category {key}"
    return 100.0, float(50.0 * len(final)), "portfolio"
