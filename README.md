# Pricing Lab

Single-page Streamlit dashboard for a price-elasticity case study on a 3,000-item retail panel, by **Khushaal Chaudhary**.

Demand response is estimated via a v9 MMM-style decomposition (item-shop FE + linear trend + K=4 Fourier seasonality + holiday dummies + category × log(price)). DML (v10a/v10b) and a per-item ridge (v6) provide robustness; MinT reconciliation (Wickramasuriya 2019) keeps portfolio / main / sub / item elasticities mathematically coherent.

## Tabs

1. **Story** — slides carousel (reads `slides.md` live)
2. **Leaderboard** — composite scoring of v0 → v10b
3. **MMM decomposition** — variance share + per-category elasticities
4. **Elasticity simulator** — price slider, demand + revenue curves, 95% CI band
5. **Methodology** — composite formula, MinT explainer, leaderboard scoring

## Local run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy

Public-but-unlisted on Streamlit Community Cloud:

1. Push this repo to GitHub (public).
2. https://share.streamlit.io → **New app** → repo + branch + `streamlit_app.py`.
3. **Advanced settings → Secrets**:
   ```toml
   APP_PASSWORD = "your-access-code-here"
   ```
4. Share the URL + access code in the cover letter only.

## Data hygiene

This repo contains **derived artefacts only**:
- `elasticities_final.csv` — 3,000 item-level ε with sign-fallback to category
- `model_outputs/reconciled_elasticities.parquet` — MinT-reconciled ε at all four levels
- `model_outputs/v9_cat.csv` — v9 per-main_category ε
- `model_outputs/v9_variance_share.txt` — portfolio-level variance decomposition
- `leaderboard.md`, `slides.md` — model leaderboard + storyboard

Raw panel data **never enters this repo** (see `.gitignore`).

