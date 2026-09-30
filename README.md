# Industrial Metals Market Intelligence Platform

A cloud-deployable Streamlit dashboard focused on **Copper, Aluminium and Nickel**.

The project is designed to be strong enough to show on a CV and simple enough to deploy without installing Python locally.

## What is included

- Cross-metal overview for Copper, Aluminium and Nickel
- Public market-price connectors with clearly labelled fallbacks
- 1D / 1W / 1M / 3M performance metrics
- 20-day annualised volatility
- 20-day and 50-day moving averages
- Relative performance comparison
- Transparent 0–100 **Market Tightness Score**
- Inventory analytics framework
- Live 7-day weather monitoring for major production / logistics regions
- Weather-linked disruption-risk score
- Live Google News RSS headline feed
- Headline classification: Supply / Demand / Policy / Logistics / Macro / Market
- Provisional event direction and impact tagging
- Cross-metal comparison page
- Research-note workspace
- Methodology page explaining every major model assumption
- Automatic support for verified inventory CSVs

## Data-source design

The platform is intentionally honest about source quality.

### Market data
The app attempts to use public Yahoo Finance data via `yfinance`:

- Copper: `HG=F` — COMEX copper futures
- Aluminium: `ALI=F` — aluminium futures
- Nickel: `NICK.L` — nickel-linked exchange-traded proxy

If a public feed is temporarily unavailable, the app uses a deterministic demo series and **labels it clearly as DEMO FALLBACK**. Never quote fallback values externally.

### Inventory data
The app ships with illustrative inventory series so the interface works immediately. For a public/CV version, replace these with inventory data you are licensed or permitted to use.

See `data/README.md` for the exact CSV format. Once a valid file is added, the dashboard detects it automatically.

### Weather data
Weather is fetched from Open-Meteo with no API key required. The current build monitors:

**Copper**
- Antofagasta, Chile
- Atacama, Chile
- Arequipa, Peru

**Aluminium**
- Boké, Guinea
- Weipa, Australia
- Yunnan, China

**Nickel**
- Sulawesi, Indonesia
- Halmahera, Indonesia
- Surigao, Philippines

Weather scoring is a screening tool for rainfall, wind and temperature risk. It does **not** claim that a mine or smelter has actually lost production.

### News
Google News RSS is used to surface recent headlines. Keyword rules classify stories into market themes and add a provisional direction/impact tag. The source article should always be read before drawing a market conclusion.

---

# Deploy it without installing anything

## Step 1 — Create a GitHub repository

1. Sign in to GitHub.
2. Click **New repository**.
3. Name it something like `industrial-metals-intelligence`.
4. Set it to **Public** if you want recruiters to be able to inspect the code.
5. Create the repository.

## Step 2 — Upload this folder

On the new repository page:

1. Choose **Add file → Upload files**.
2. Drag in the **contents of this folder**.
3. Make sure GitHub shows `app.py` at the top level of the repository.
4. Commit the upload.

The important top-level structure should look like:

```text
industrial-metals-intelligence/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── data/
│   └── README.md
└── src/
    ├── __init__.py
    ├── config.py
    ├── market_data.py
    ├── news.py
    ├── ui.py
    └── weather.py
```

## Step 3 — Deploy on Streamlit Community Cloud

1. Open Streamlit Community Cloud.
2. Sign in with GitHub.
3. Choose **Create app**.
4. Select your GitHub repository.
5. Branch: `main`.
6. Main file path: `app.py`.
7. Deploy.

There are **no API secrets required** for the current build.

Streamlit will read `requirements.txt`, install the dependencies and host the app for you.

## Step 4 — Put the live link on your CV

Once deployed, use the public Streamlit URL beside the project title on your CV or in your LinkedIn Projects section.

Suggested title:

**Industrial Metals Market Intelligence Platform**

Suggested CV bullet:

> Built a Python-based industrial metals intelligence platform covering copper, aluminium and nickel, integrating market prices, inventory signals, live production-region weather and news analytics into a transparent market-tightness framework.

---

# Best upgrades before sending it to recruiters

The current version is designed as a polished, transparent portfolio build. The biggest improvements would be:

1. Add verified LME / SHFE inventory history that your licence permits you to use.
2. Add a verified nickel price feed rather than an exchange-traded proxy.
3. Add cash-to-3M spreads and forward-curve analytics.
4. Add treatment charges, mine/smelter production and trade-flow indicators.
5. Backtest the tightness score against later market outcomes.
6. Publish dated research notes and post-mortems alongside the dashboard.

These upgrades are more valuable than adding dozens of decorative features.

## Important note

This is an analytical portfolio project, not an investment-advice product. Source labels and model limitations are deliberately visible in the interface so that the project remains defensible in an interview.
