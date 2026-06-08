"""Editorial Pricing Lab — design tokens + CSS for the home24 elasticity dashboard.

Aesthetic direction: Stripe Press x FT Alphaville x Linear docs. Display serif for
headlines (Fraunces), Geist Sans for UI, Geist Mono for tabular numerics.
Red (#E60023) is used surgically as accent line / key-metric ink, never as fill.
Surfaces: warm cream alt (#FAFAF7) on white, 1px ruled separators instead of shadows.
Subtle SVG-noise grain overlay on body gives printed-paper feel.

Single source of truth: any colour/typography in the app should pull from PALETTE/TYPE
here. Charts import CHART_PALETTE from this module.
"""
from __future__ import annotations

# ---- Tokens ----------------------------------------------------------------
PALETTE = {
    "ink":         "#0C0C0D",
    "ink_2":       "#4A4A4D",
    "ink_3":       "#8A8A8C",
    "paper":       "#FFFFFF",
    "paper_2":     "#FAFAF7",   # warm cream
    "rule":        "#E8E8E2",
    "rule_strong": "#D1D1CB",
    "red":         "#E60023",
    "red_deep":    "#A60019",
    "red_tint":    "#FFEEF0",
    "ok":          "#1F7A4D",
    "warn":        "#B65C00",
    "cool":        "#1E5DAB",   # reserved for benchmark/literature
}

# Lead red for "current/highlighted"; supporting series in graphite scale + one cool.
CHART_PALETTE = [
    "#E60023",  # primary - the focus series
    "#0C0C0D",  # ink - secondary
    "#6A6A6E",  # mid graphite
    "#A8A8A4",  # warm gray
    "#1E5DAB",  # cool benchmark
    "#1F7A4D",  # ok-state
    "#B65C00",  # warn-state
    "#A60019",  # deep red
]

TYPE = {
    "display": "'Fraunces', 'EB Garamond', Georgia, serif",
    "ui":      "'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "mono":    "'Geist Mono', ui-monospace, 'JetBrains Mono', Menlo, monospace",
}

# SVG noise data URI - 4% opacity grain
GRAIN_SVG = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'>"
    "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/>"
    "<feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.04 0'/></filter>"
    "<rect width='100%' height='100%' filter='url(%23n)'/></svg>"
)

# ---- CSS -------------------------------------------------------------------
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');

:root {{
    --ink: {PALETTE['ink']};
    --ink-2: {PALETTE['ink_2']};
    --ink-3: {PALETTE['ink_3']};
    --paper: {PALETTE['paper']};
    --paper-2: {PALETTE['paper_2']};
    --rule: {PALETTE['rule']};
    --rule-strong: {PALETTE['rule_strong']};
    --red: {PALETTE['red']};
    --red-deep: {PALETTE['red_deep']};
    --red-tint: {PALETTE['red_tint']};
    --ok: {PALETTE['ok']};
    --warn: {PALETTE['warn']};
    --cool: {PALETTE['cool']};
    --t-display: {TYPE['display']};
    --t-ui: {TYPE['ui']};
    --t-mono: {TYPE['mono']};
}}

/* Body + paper grain */
html, body, .stApp {{
    font-family: var(--t-ui);
    color: var(--ink);
    background: var(--paper);
    font-feature-settings: 'ss01', 'cv11';
}}
.stApp::before {{
    content: ""; position: fixed; inset: 0; pointer-events: none;
    background-image: url("{GRAIN_SVG}"); opacity: 0.4; z-index: 0;
    mix-blend-mode: multiply;
}}
/* Only the main block container lifts above the grain; do NOT z-index every
   streamlit element - that breaks BaseWeb popovers (selectbox dropdowns). */
.block-container, section[data-testid="stSidebar"] {{ position: relative; z-index: 1; }}

/* Layout: full width with breathing room. Streamlit's default max-width caps
   content at ~700px which leaves huge gutters on wide monitors. Override. */
.block-container, [data-testid="stMainBlockContainer"] {{
    max-width: 1480px !important;
    padding-top: 3.5rem !important;
    padding-bottom: 4rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
}}
[data-testid="stAppViewContainer"] > .main {{
    padding-left: 0 !important; padding-right: 0 !important;
}}

/* BaseWeb popovers (selectbox dropdowns) must float above everything else.
   Streamlit portals these to <body> so they bypass block-container z-index. */
div[data-baseweb="popover"], div[data-baseweb="menu"], div[data-baseweb="select"] {{
    z-index: 100000 !important;
}}
div[data-baseweb="popover"] {{
    pointer-events: auto !important;
}}

/* ---- Typography ---- */
h1, .stMarkdown h1 {{
    font-family: var(--t-display);
    font-weight: 600;
    font-size: 44px; line-height: 1.05;
    letter-spacing: -0.02em;
    color: var(--ink);
    margin: 0 0 0.5rem 0;
    font-variation-settings: "opsz" 96, "SOFT" 0;
}}
h2, .stMarkdown h2 {{
    font-family: var(--t-display);
    font-weight: 500;
    font-size: 26px; line-height: 1.2;
    letter-spacing: -0.015em;
    color: var(--ink);
    margin: 2.25rem 0 0.75rem 0;
    font-variation-settings: "opsz" 36;
}}
h3, .stMarkdown h3 {{
    font-family: var(--t-ui);
    font-weight: 600; font-size: 14px;
    letter-spacing: 0.01em;
    color: var(--ink); margin: 1.25rem 0 0.5rem 0;
}}
p, .stMarkdown p, li {{
    font-family: var(--t-ui);
    font-size: 14.5px; line-height: 1.55;
    color: var(--ink-2);
}}
code, .stMarkdown code {{
    font-family: var(--t-mono); font-size: 12.5px;
    background: var(--paper-2); padding: 1px 5px; border-radius: 3px;
    color: var(--ink);
}}
.mono {{ font-family: var(--t-mono); font-feature-settings: 'tnum'; }}

/* Eyebrow / micro-cap labels */
.eyebrow {{
    font-family: var(--t-ui);
    font-size: 10.5px; letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--ink-3); font-weight: 600;
}}

/* ---- Cards (no shadow; 1px rule) ---- */
.card {{
    background: var(--paper);
    border: 1px solid var(--rule);
    border-radius: 4px;
    padding: 20px 22px 22px 22px;
    position: relative;
    min-height: 168px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    box-sizing: border-box;
}}
.card.accent::before {{
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: var(--red);
}}
.card.cream {{ background: var(--paper-2); }}

/* Native st.container(border=True) — actually wraps its children. Restyle to match
   our card aesthetic (thin rule, generous padding, no shadow, no rounded corners). */
[data-testid="stVerticalBlockBorderWrapper"] {{
    border: 1px solid var(--rule) !important;
    border-radius: 4px !important;
    background: var(--paper) !important;
    padding: 28px 36px !important;
    margin-top: 1rem !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background: transparent !important;
}}

.metric-label {{
    font-family: var(--t-ui);
    font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--ink-3); font-weight: 600;
    margin-bottom: 10px;
}}
.metric-value {{
    font-family: var(--t-mono);
    font-size: 34px; font-weight: 500; line-height: 1;
    color: var(--ink);
    letter-spacing: -0.01em;
    font-feature-settings: 'tnum';
}}
.metric-value.red {{ color: var(--red); }}
.metric-value.ok  {{ color: var(--ok); }}
.metric-delta {{
    font-family: var(--t-mono);
    font-size: 12px; color: var(--ink-3); margin-top: 8px;
    font-feature-settings: 'tnum';
}}
.metric-delta.up {{ color: var(--ok); }}
.metric-delta.down {{ color: var(--red); }}

/* ---- Sidebar (cream + ruled) ---- */
section[data-testid="stSidebar"] {{
    background: var(--paper-2);
    border-right: 1px solid var(--rule);
}}
section[data-testid="stSidebar"] .block-container {{
    padding-top: 1.75rem;
}}
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label {{
    font-family: var(--t-ui);
    font-size: 10.5px !important;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--ink-3) !important;
    font-weight: 600 !important;
}}
section[data-testid="stSidebar"] hr {{
    border-color: var(--rule); margin: 1.25rem 0;
}}

/* ---- Tabs: underline-only ---- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 28px;
    border-bottom: 1px solid var(--rule);
    background: transparent;
    padding-left: 0;
}}
.stTabs [data-baseweb="tab"],
.stTabs [data-baseweb="tab"] button,
.stTabs button[role="tab"] {{
    background: transparent !important;
    padding: 12px 2px 14px 2px !important;
    font-family: var(--t-ui); font-weight: 500; font-size: 14px;
    color: var(--ink-3) !important;
    border: none !important;
    border-radius: 0 !important;
    outline: none !important;
    box-shadow: none !important;
}}
.stTabs [data-baseweb="tab"]:hover,
.stTabs button[role="tab"]:hover {{
    color: var(--ink-2) !important;
    background: transparent !important;
    box-shadow: none !important;
}}
.stTabs [data-baseweb="tab"]:focus,
.stTabs [data-baseweb="tab"]:focus-visible,
.stTabs button[role="tab"]:focus,
.stTabs button[role="tab"]:focus-visible {{
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
}}
.stTabs [aria-selected="true"] {{
    color: var(--ink) !important;
    box-shadow: inset 0 -2px 0 var(--red) !important;
}}
/* Nuclear reset on every descendant inside .stTabs that could carry a border
   or background. BaseWeb wraps the tab label in 3-4 nested divs/spans; any
   one of them could carry the visible "box" the user sees. */
.stTabs [data-baseweb="tab-list"] *,
.stTabs [role="tablist"] *,
.stTabs button,
.stTabs button > *,
.stTabs [role="tab"],
.stTabs [role="tab"] > * {{
    border: 0 !important;
    outline: 0 !important;
    box-shadow: none !important;
    background-color: transparent !important;
    background-image: none !important;
}}
/* Re-apply the active-tab red underline (the nuclear reset above wiped it). */
.stTabs [aria-selected="true"] {{
    color: var(--ink) !important;
    box-shadow: inset 0 -2px 0 var(--red) !important;
}}
/* BaseWeb's two underline elements: `tab-highlight` is the sliding indicator
   under the active tab — make it red. `tab-border` is the full-width baseline
   under the entire tab strip — must be the rule colour, NOT red, or it paints
   a wide red bar across every tab. These two were collapsed into one rule
   previously and both came out red. */
.stTabs [data-baseweb="tab-highlight"] {{
    background-color: var(--red) !important;
    height: 2px !important;
}}
.stTabs [data-baseweb="tab-border"] {{
    background-color: var(--rule) !important;
    height: 1px !important;
}}

/* ---- Buttons (ink-on-cream default; red for primary actions) ---- */
.stButton > button {{
    background: var(--paper);
    color: var(--ink);
    border: 1px solid var(--rule-strong);
    border-radius: 4px;
    font-family: var(--t-ui); font-weight: 500; font-size: 13px;
    padding: 8px 14px;
    transition: all 120ms ease;
}}
.stButton > button:hover {{
    border-color: var(--ink);
    background: var(--paper-2);
}}
/* Primary button — modern Streamlit uses data-testid; older builds use kind=. Cover both. */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"],
.stButton > button[data-testid="stBaseButton-primary"] {{
    background: var(--ink) !important;
    color: #FFFFFF !important;
    border-color: var(--ink) !important;
}}
.stButton > button[kind="primary"] *,
.stButton > button[data-testid="baseButton-primary"] *,
.stButton > button[data-testid="stBaseButton-primary"] * {{
    color: #FFFFFF !important;
}}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {{
    background: var(--red) !important;
    border-color: var(--red) !important;
    color: #FFFFFF !important;
}}

/* Inputs */
.stTextInput input, .stSelectbox div[role="combobox"], .stNumberInput input {{
    font-family: var(--t-ui); font-size: 13.5px;
    border-color: var(--rule-strong) !important;
    border-radius: 4px !important;
}}

/* Sliders - red track */
.stSlider [data-baseweb="slider"] [role="slider"] {{
    background: var(--red); border-color: var(--red);
    box-shadow: 0 0 0 4px rgba(230, 0, 35, 0.12);
}}

/* Tables / dataframes */
.stDataFrame, [data-testid="stDataFrame"] {{
    border: 1px solid var(--rule); border-radius: 4px;
}}
.stDataFrame [role="row"] {{
    font-family: var(--t-mono); font-size: 12.5px;
}}

/* Dividers */
hr {{ border: none; border-top: 1px solid var(--rule); margin: 2rem 0; }}

/* Streamlit chrome: keep the header at native height so the show-sidebar
   arrow (which lives inside it) is not clipped. Just make it visually flat. */
header[data-testid="stHeader"] {{
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
}}
#MainMenu, footer, [data-testid="stDecoration"] {{
    visibility: hidden !important; height: 0 !important;
}}
header [data-testid="stToolbar"] {{ visibility: hidden !important; }}

/* Show-sidebar arrow — force-visible across every Streamlit version's testid.
   Streamlit has renamed this element 3 times in the last year; selector list
   covers them all. */
/* Show-sidebar arrow — scope STRICTLY to the collapsed-control element.
   The previous selector list included `aria-label*=sidebar` and a sibling
   structural match that caught every tab/button in the main content area,
   painting borders + the wide red bar across all of them. */
header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"],
header[data-testid="stHeader"] [data-testid="collapsedControl"],
header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stExpandSidebarButton"] {{
    visibility: visible !important;
    opacity: 1 !important;
    display: inline-flex !important;
    pointer-events: auto !important;
    z-index: 999999 !important;
    background: var(--paper) !important;
    border: 1px solid var(--rule-strong) !important;
    border-radius: 4px !important;
    color: var(--ink) !important;
}}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg,
[data-testid="stExpandSidebarButton"] svg {{
    fill: var(--ink) !important;
    color: var(--ink) !important;
    width: 18px !important; height: 18px !important;
}}

/* ---- Editorial masthead ---- */
.masthead {{
    display: flex; align-items: flex-end; justify-content: space-between;
    padding: 4px 0 22px 0;
    border-bottom: 1px solid var(--ink);
    margin-bottom: 32px;
}}
.masthead-left {{ display: flex; flex-direction: column; gap: 4px; }}
.masthead-kicker {{
    font-family: var(--t-ui);
    font-size: 10.5px; letter-spacing: 0.18em; text-transform: uppercase;
    color: var(--ink-3); font-weight: 600;
}}
.masthead-title {{
    font-family: var(--t-display); font-weight: 600; font-size: 30px;
    line-height: 1; letter-spacing: -0.02em; color: var(--ink);
    font-variation-settings: "opsz" 96;
}}
.masthead-title em {{
    font-style: italic; font-weight: 500;
    color: var(--red);
    font-variation-settings: "opsz" 96, "SOFT" 50;
}}
.masthead-right {{
    text-align: right; font-family: var(--t-mono);
    font-size: 11px; color: var(--ink-3); line-height: 1.5;
    font-feature-settings: 'tnum';
}}
.masthead-right strong {{ color: var(--ink); font-weight: 500; }}

/* Pull-quote / callout block */
.pullquote {{
    border-left: 2px solid var(--red);
    padding: 6px 0 6px 18px;
    margin: 1.5rem 0;
    font-family: var(--t-display); font-size: 18px; font-style: italic;
    color: var(--ink); line-height: 1.45;
}}

/* Tag / chip */
.chip {{
    display: inline-block;
    font-family: var(--t-mono); font-size: 11px;
    padding: 2px 8px; border-radius: 999px;
    background: var(--paper-2); border: 1px solid var(--rule);
    color: var(--ink-2);
}}
.chip.red {{ background: var(--red-tint); border-color: var(--red); color: var(--red-deep); }}
.chip.cool {{ color: var(--cool); border-color: var(--cool); background: white; }}
</style>
"""

# ---- Brand header --------------------------------------------------------
def _masthead_html(issue: str = "Issue 01", subtitle: str = "Case study - Data Scientist (Sales Forecasting)") -> str:
    return f"""<div class="masthead">
      <div class="masthead-left">
        <div class="masthead-kicker">home24 - Pricing Lab</div>
        <div class="masthead-title">Price <em>Elasticity</em></div>
      </div>
      <div class="masthead-right">
        <strong>Khushaal Chaudhary</strong><br/>
        {subtitle}<br/>
        {issue}
      </div>
    </div>"""


def inject(st, *, subtitle: str | None = None, issue: str = "Issue 01") -> None:
    """Call once at the top of every page.
        from app.styles import inject
        inject(st, subtitle="Elasticity Simulator")
    """
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        _masthead_html(issue=issue,
                       subtitle=subtitle or "Case study - Data Scientist (Sales Forecasting)"),
        unsafe_allow_html=True,
    )


# ---- Plotly theme helper -------------------------------------------------
def plotly_layout() -> dict:
    """Default layout dict to merge into every figure for cohesive styling."""
    return dict(
        font=dict(family=TYPE["ui"], size=12, color=PALETTE["ink"]),
        # NO title key — passing title={} or title=dict(text="") to plotly can
        # render the JS literal "undefined" in the top-left. Per-figure title only.
        paper_bgcolor=PALETTE["paper"],
        plot_bgcolor=PALETTE["paper"],
        colorway=CHART_PALETTE,
        margin=dict(l=48, r=24, t=48, b=44),
        xaxis=dict(
            showgrid=False, zeroline=False,
            linecolor=PALETTE["rule_strong"], linewidth=1, mirror=False,
            ticks="outside", ticklen=4, tickcolor=PALETTE["rule_strong"],
            tickfont=dict(family=TYPE["mono"], size=11, color=PALETTE["ink_2"]),
        ),
        yaxis=dict(
            showgrid=True, gridcolor=PALETTE["rule"], gridwidth=1,
            zeroline=False,
            linecolor=PALETTE["rule_strong"], linewidth=1,
            tickfont=dict(family=TYPE["mono"], size=11, color=PALETTE["ink_2"]),
        ),
        legend=dict(
            font=dict(family=TYPE["ui"], size=11, color=PALETTE["ink_2"]),
            bgcolor="rgba(255,255,255,0.7)", borderwidth=0,
        ),
        hoverlabel=dict(
            font=dict(family=TYPE["mono"], size=12),
            bgcolor=PALETTE["ink"], bordercolor=PALETTE["ink"],
            font_color=PALETTE["paper"],
        ),
    )
