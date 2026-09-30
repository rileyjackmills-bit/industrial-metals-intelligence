from __future__ import annotations

# Single-file Streamlit deployment: all project logic is intentionally inlined
# so GitHub/Streamlit Cloud does not depend on local package structure.

# ===== Inlined from src/config.py =====
from dataclasses import dataclass

@dataclass(frozen=True)
class MetalConfig:
    name: str
    symbol: str
    unit: str
    accent: str
    yfinance_ticker: str
    ticker_note: str
    search_terms: str

METALS = {
    "Copper": MetalConfig(
        name="Copper",
        symbol="Cu",
        unit="USD/lb",
        accent="#B87333",
        yfinance_ticker="HG=F",
        ticker_note="COMEX Copper futures",
        search_terms="copper mine supply demand Chile Peru China LME",
    ),
    "Aluminium": MetalConfig(
        name="Aluminium",
        symbol="Al",
        unit="USD/t",
        accent="#A7B2C1",
        yfinance_ticker="ALI=F",
        ticker_note="CME Aluminium futures when available",
        search_terms="aluminium aluminum smelter bauxite China power LME",
    ),
    "Nickel": MetalConfig(
        name="Nickel",
        symbol="Ni",
        unit="index / proxy",
        accent="#6FA89B",
        yfinance_ticker="NICK.L",
        ticker_note="Nickel-linked ETP proxy; replace with licensed LME/OTC feed for production use",
        search_terms="nickel Indonesia Philippines stainless battery supply demand LME",
    ),
}

WEATHER_REGIONS = {
    "Copper": [
        {"name": "Antofagasta, Chile", "lat": -23.6509, "lon": -70.3975, "type": "Mining / logistics"},
        {"name": "Atacama, Chile", "lat": -27.3668, "lon": -70.3323, "type": "Mining"},
        {"name": "Arequipa, Peru", "lat": -16.4090, "lon": -71.5375, "type": "Mining / logistics"},
    ],
    "Aluminium": [
        {"name": "Boké, Guinea", "lat": 10.9322, "lon": -14.2906, "type": "Bauxite"},
        {"name": "Weipa, Australia", "lat": -12.6268, "lon": 141.8787, "type": "Bauxite"},
        {"name": "Yunnan, China", "lat": 25.0389, "lon": 102.7183, "type": "Hydro / smelting"},
    ],
    "Nickel": [
        {"name": "Sulawesi, Indonesia", "lat": -2.0000, "lon": 121.0000, "type": "Mining / processing"},
        {"name": "Halmahera, Indonesia", "lat": 1.3121, "lon": 127.8093, "type": "Mining / processing"},
        {"name": "Surigao, Philippines", "lat": 9.7860, "lon": 125.4920, "type": "Mining / ports"},
    ],
}

CATEGORY_KEYWORDS = {
    "Supply": ["mine", "output", "production", "strike", "closure", "smelter", "refinery", "shortage", "quota", "ore"],
    "Demand": ["demand", "consumption", "manufacturing", "construction", "ev", "battery", "stainless", "grid", "orders"],
    "Policy": ["tariff", "sanction", "export", "ban", "quota", "regulation", "government", "tax", "permit"],
    "Logistics": ["port", "freight", "shipping", "rail", "truck", "storm", "flood", "route", "warehouse"],
    "Macro": ["dollar", "rates", "inflation", "china", "pmi", "growth", "recession", "stimulus", "fed"],
}

BULLISH_WORDS = ["cut", "shortage", "disruption", "strike", "closure", "decline", "lower output", "ban", "tight", "deficit", "surge in demand"]
BEARISH_WORDS = ["surplus", "increase output", "ramp up", "weak demand", "slowdown", "inventory rise", "oversupply", "glut", "decline in demand"]

# ===== Inlined from src/market_data.py =====

import math
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"


def _demo_series(metal: str, days: int = 420) -> pd.DataFrame:
    """Deterministic fallback data so the UI never breaks if a public feed is down."""
    seeds = {"Copper": 11, "Aluminium": 23, "Nickel": 37}
    start_prices = {"Copper": 4.25, "Aluminium": 2500.0, "Nickel": 16000.0}
    rng = np.random.default_rng(seeds[metal])
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    drift = {"Copper": 0.00035, "Aluminium": 0.00015, "Nickel": -0.00005}[metal]
    vol = {"Copper": 0.013, "Aluminium": 0.010, "Nickel": 0.018}[metal]
    rets = rng.normal(drift, vol, len(dates))
    close = start_prices[metal] * np.exp(np.cumsum(rets))
    high = close * (1 + rng.uniform(0.001, 0.018, len(dates)))
    low = close * (1 - rng.uniform(0.001, 0.018, len(dates)))
    open_ = close * (1 + rng.normal(0, vol / 3, len(dates)))
    volume = rng.integers(40_000, 180_000, len(dates))
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


def fetch_market_history(metal: str, period: str = "1y") -> Tuple[pd.DataFrame, str, bool]:
    """Return history, source label and whether the source is genuinely live/public."""
    cfg = METALS[metal]
    try:
        import yfinance as yf

        df = yf.download(
            cfg.yfinance_ticker,
            period=period,
            auto_adjust=True,
            progress=False,
            timeout=4,
            threads=False,
        )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df is not None and len(df) > 30 and "Close" in df.columns:
            keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
            df = df[keep].dropna(how="all")
            if len(df) > 30:
                return df, cfg.ticker_note, True
    except Exception:
        pass

    return (
        _demo_series(metal),
        "Demo fallback — public market feed unavailable. Do not quote these prices externally.",
        False,
    )


def enrich_market_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    close = out["Close"].astype(float)
    out["Return"] = close.pct_change()
    out["MA20"] = close.rolling(20).mean()
    out["MA50"] = close.rolling(50).mean()
    out["Vol20"] = out["Return"].rolling(20).std() * np.sqrt(252)
    out["Momentum20"] = close.pct_change(20)
    out["Drawdown"] = close / close.cummax() - 1
    return out


def market_metrics(df: pd.DataFrame) -> dict:
    df = enrich_market_data(df).dropna(subset=["Close"])
    close = float(df["Close"].iloc[-1])

    def pct(n: int) -> float:
        if len(df) <= n:
            return float("nan")
        return (close / float(df["Close"].iloc[-n - 1]) - 1) * 100

    vol = float(df["Vol20"].iloc[-1]) if len(df) else float("nan")
    return {
        "price": close,
        "1d": pct(1),
        "1w": pct(5),
        "1m": pct(21),
        "3m": pct(63),
        "vol": vol * 100 if not math.isnan(vol) else np.nan,
        "ma20": float(df["MA20"].iloc[-1]),
        "ma50": float(df["MA50"].iloc[-1]),
        "momentum": float(df["Momentum20"].iloc[-1] * 100),
        "drawdown": float(df["Drawdown"].iloc[-1] * 100),
        "last_date": pd.Timestamp(df.index[-1]).date().isoformat(),
    }


def _demo_inventory_series(metal: str, days: int = 365) -> pd.DataFrame:
    seeds = {"Copper": 101, "Aluminium": 202, "Nickel": 303}
    base = {"Copper": 165_000, "Aluminium": 520_000, "Nickel": 205_000}[metal]
    slope = {"Copper": -90, "Aluminium": 75, "Nickel": 120}[metal]
    rng = np.random.default_rng(seeds[metal])
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    noise = rng.normal(0, base * 0.006, len(dates)).cumsum()
    values = np.maximum(base + slope * np.arange(len(dates)) + noise, base * 0.22)
    return pd.DataFrame({"Inventory": values}, index=dates)


def load_inventory_series(metal: str) -> tuple[pd.DataFrame, str, bool]:
    """
    Load a user-supplied verified inventory file when present.

    Expected path: data/<metal>_inventory.csv
    Columns: Date, Inventory
    """
    file_path = DATA_DIR / f"{metal.lower()}_inventory.csv"
    if file_path.exists():
        try:
            raw = pd.read_csv(file_path)
            if {"Date", "Inventory"}.issubset(raw.columns) and raw["Inventory"].notna().sum() >= 30:
                raw["Date"] = pd.to_datetime(raw["Date"], errors="coerce")
                raw["Inventory"] = pd.to_numeric(raw["Inventory"], errors="coerce")
                raw = raw.dropna(subset=["Date", "Inventory"]).sort_values("Date")
                if len(raw) >= 30:
                    return (
                        raw.set_index("Date")[["Inventory"]],
                        f"Verified user-supplied CSV: {file_path.name}",
                        True,
                    )
        except Exception:
            pass

    return (
        _demo_inventory_series(metal),
        "Illustrative inventory series — replace with verified exchange/licensed data before external use.",
        False,
    )


def tightness_score(
    metal: str,
    market_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    weather_risk: float = 0.0,
) -> dict:
    market = enrich_market_data(market_df).dropna(subset=["Close"])
    inv = inventory_df["Inventory"].dropna()

    momentum = float(market["Momentum20"].iloc[-1]) if len(market) else 0.0
    inv_30 = (float(inv.iloc[-1]) / float(inv.iloc[-22]) - 1) if len(inv) > 22 else 0.0
    inv_percentile = float((inv <= inv.iloc[-1]).mean()) if len(inv) else 0.5
    vol = (
        float(market["Vol20"].iloc[-1])
        if "Vol20" in market and len(market) and not pd.isna(market["Vol20"].iloc[-1])
        else 0.25
    )

    # Normalised, intentionally simple components that can be explained in an interview.
    momentum_component = np.clip(50 + momentum * 300, 0, 100)
    inventory_change_component = np.clip(50 - inv_30 * 500, 0, 100)
    inventory_level_component = np.clip((1 - inv_percentile) * 100, 0, 100)
    volatility_component = np.clip(35 + vol * 80, 0, 100)
    weather_component = np.clip(weather_risk, 0, 100)

    score = (
        0.30 * inventory_level_component
        + 0.25 * inventory_change_component
        + 0.20 * momentum_component
        + 0.10 * volatility_component
        + 0.15 * weather_component
    )
    score = float(np.clip(score, 0, 100))

    if score >= 70:
        label = "Tight"
    elif score >= 45:
        label = "Balanced"
    else:
        label = "Loose"

    return {
        "score": score,
        "label": label,
        "Inventory level": float(inventory_level_component),
        "Inventory trend": float(inventory_change_component),
        "Price momentum": float(momentum_component),
        "Volatility": float(volatility_component),
        "Weather risk": float(weather_component),
    }

# ===== Inlined from src/weather.py =====

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def _risk_score(
    precip_7d: float,
    max_wind: float,
    max_temp: float,
    min_temp: float,
    region_type: str,
) -> tuple[float, list[str]]:
    """Transparent screening score for near-term weather-linked operating risk."""
    score = 0.0
    reasons: list[str] = []

    if precip_7d >= 120:
        score += 50
        reasons.append("Very heavy 7-day rainfall")
    elif precip_7d >= 70:
        score += 35
        reasons.append("Heavy 7-day rainfall")
    elif precip_7d >= 35:
        score += 20
        reasons.append("Elevated rainfall")

    if max_wind >= 70:
        score += 35
        reasons.append("Severe wind risk")
    elif max_wind >= 50:
        score += 20
        reasons.append("Strong wind risk")

    if max_temp >= 40:
        score += 20
        reasons.append("Extreme heat")
    elif max_temp >= 36:
        score += 10
        reasons.append("High heat")

    # For hydro-linked aluminium regions this only flags a watch item. It does not
    # claim low reservoir levels or generation constraints.
    if "Hydro" in region_type and precip_7d < 5:
        score += 15
        reasons.append("Very low near-term precipitation in hydro-linked region")

    return min(score, 100.0), reasons or ["No major near-term weather signal"]


def fetch_region_weather(region: Dict) -> Dict:
    params = {
        "latitude": region["lat"],
        "longitude": region["lon"],
        "current": "temperature_2m,precipitation,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "forecast_days": 7,
        "timezone": "auto",
    }
    response = requests.get(OPEN_METEO_URL, params=params, timeout=4)
    response.raise_for_status()
    data = response.json()

    daily = data.get("daily", {})
    precip = [float(x or 0) for x in daily.get("precipitation_sum", [])]
    winds = [float(x or 0) for x in daily.get("wind_speed_10m_max", [])]
    tmax = [float(x) for x in daily.get("temperature_2m_max", []) if x is not None]
    tmin = [float(x) for x in daily.get("temperature_2m_min", []) if x is not None]

    precip_7d = float(sum(precip))
    max_wind = float(max(winds)) if winds else 0.0
    max_temp = float(max(tmax)) if tmax else 0.0
    min_temp = float(min(tmin)) if tmin else 0.0
    risk, reasons = _risk_score(precip_7d, max_wind, max_temp, min_temp, region["type"])

    current = data.get("current", {})
    return {
        **region,
        "current_temp": current.get("temperature_2m"),
        "current_precip": current.get("precipitation"),
        "current_wind": current.get("wind_speed_10m"),
        "dates": daily.get("time", []),
        "precip_daily": precip,
        "temp_max_daily": tmax,
        "temp_min_daily": tmin,
        "wind_daily": winds,
        "precip_7d": precip_7d,
        "max_wind": max_wind,
        "max_temp": max_temp,
        "min_temp": min_temp,
        "risk": risk,
        "reasons": reasons,
        "live": True,
    }


def fetch_weather_for_metal(metal: str) -> List[Dict]:
    """Fetch the monitored regions concurrently so cloud page loads stay snappy."""
    regions = WEATHER_REGIONS[metal]
    output: list[Dict] = []

    with ThreadPoolExecutor(max_workers=min(4, len(regions))) as executor:
        future_map = {executor.submit(fetch_region_weather, region): region for region in regions}
        for future in as_completed(future_map):
            region = future_map[future]
            try:
                output.append(future.result())
            except Exception:
                output.append(
                    {
                        **region,
                        "live": False,
                        "risk": 0.0,
                        "reasons": ["Live weather unavailable"],
                    }
                )

    # Preserve the deliberate order in config.py.
    rank = {r["name"]: i for i, r in enumerate(regions)}
    output.sort(key=lambda row: rank.get(row["name"], 999))
    return output


def aggregate_weather_risk(weather_rows: List[Dict]) -> float:
    live = [float(r.get("risk", 0.0)) for r in weather_rows if r.get("live")]
    return float(sum(live) / len(live)) if live else 0.0

# ===== Inlined from src/news.py =====

from datetime import datetime
from urllib.parse import quote_plus

import feedparser



def classify_headline(title: str) -> tuple[str, str, str]:
    text = title.lower()
    category_scores = {
        category: sum(1 for kw in kws if kw in text)
        for category, kws in CATEGORY_KEYWORDS.items()
    }
    category = max(category_scores, key=category_scores.get)
    if category_scores[category] == 0:
        category = "Market"

    bull = sum(1 for kw in BULLISH_WORDS if kw in text)
    bear = sum(1 for kw in BEARISH_WORDS if kw in text)
    if bull > bear:
        direction = "Potentially supportive"
    elif bear > bull:
        direction = "Potentially negative"
    else:
        direction = "Mixed / unclear"

    impact_keywords = ["strike", "ban", "sanction", "closure", "tariff", "quota", "flood", "earthquake", "war", "force majeure"]
    impact = "High" if any(k in text for k in impact_keywords) else "Medium"
    return category, direction, impact


def fetch_news(metal: str, limit: int = 12) -> list[dict]:
    query = quote_plus(METALS[metal].search_terms)
    url = f"https://news.google.com/rss/search?q={query}&hl=en-GB&gl=GB&ceid=GB:en"
    try:
        feed = feedparser.parse(url)
        rows = []
        for entry in feed.entries[:limit]:
            category, direction, impact = classify_headline(entry.get("title", ""))
            rows.append({
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": getattr(entry.get("source", {}), "title", None) if hasattr(entry.get("source", {}), "title") else entry.get("source", {}).get("title", ""),
                "category": category,
                "direction": direction,
                "impact": impact,
            })
        return rows
    except Exception:
        return []

# ===== Inlined from src/ui.py =====

import streamlit as st


def inject_css():
    st.markdown(
        """
<style>
:root {
  --bg: #0B0F14;
  --panel: #111821;
  --panel2: #0F151D;
  --border: rgba(255,255,255,.085);
  --muted: #91A0B2;
  --text: #F3F6F9;
}
html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.stApp { background: radial-gradient(circle at 15% 0%, rgba(184,115,51,.08), transparent 27%), var(--bg); }
.block-container { max-width: 1480px; padding-top: 1.4rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: #090D12; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
#MainMenu, footer, header { visibility: hidden; }
.hero {
  border: 1px solid var(--border); background: linear-gradient(135deg, rgba(255,255,255,.03), rgba(255,255,255,.01));
  border-radius: 22px; padding: 24px 28px; margin-bottom: 16px; box-shadow: 0 18px 55px rgba(0,0,0,.22);
}
.eyebrow { color: #A9B7C7; font-size: 12px; text-transform: uppercase; letter-spacing: .18em; font-weight: 700; }
.hero h1 { margin: 8px 0 8px 0; font-size: 40px; line-height: 1.06; letter-spacing: -.035em; }
.hero p { margin: 0; color: var(--muted); font-size: 15px; max-width: 900px; }
.metric-card {
  border: 1px solid var(--border); background: linear-gradient(180deg, rgba(255,255,255,.032), rgba(255,255,255,.012));
  border-radius: 18px; padding: 18px 18px 16px 18px; min-height: 120px; box-shadow: 0 12px 30px rgba(0,0,0,.15);
}
.metric-label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .10em; font-weight: 700; }
.metric-value { color: var(--text); font-size: 28px; font-weight: 760; margin-top: 8px; letter-spacing: -.02em; }
.metric-sub { color: var(--muted); font-size: 12px; margin-top: 4px; }
.pill { display:inline-block; padding: 4px 9px; border-radius:999px; border:1px solid var(--border); font-size:11px; color:#C8D2DD; background:rgba(255,255,255,.025); }
.section-title { font-size: 18px; font-weight: 750; margin: 10px 0 2px 0; }
.section-sub { color: var(--muted); font-size: 13px; margin-bottom: 8px; }
.news-card { border:1px solid var(--border); border-radius:16px; padding:15px 16px; margin-bottom:10px; background:rgba(255,255,255,.018); }
.news-title { font-weight:650; line-height:1.35; font-size:14px; margin:6px 0; }
.news-meta { color: var(--muted); font-size:11px; }
.small-note { color:var(--muted); font-size:11px; line-height:1.45; }
hr { border-color: var(--border) !important; }
div[data-testid="stMetric"] { border: 1px solid var(--border); border-radius: 15px; padding: 14px 15px; background: rgba(255,255,255,.018); }
div[data-testid="stMetricLabel"] { color: var(--muted); }
button[kind="secondary"] { border-radius: 12px !important; }
[data-baseweb="tab-list"] { gap: 8px; }
[data-baseweb="tab"] { border-radius: 12px 12px 0 0; padding: 10px 14px; }
</style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, eyebrow: str = "Industrial metals intelligence"):
    st.markdown(
        f"""
<div class="hero">
  <div class="eyebrow">{eyebrow}</div>
  <h1>{title}</h1>
  <p>{subtitle}</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, sub: str = ""):
    st.markdown(
        f"""
<div class="metric-card">
  <div class="metric-label">{label}</div>
  <div class="metric-value">{value}</div>
  <div class="metric-sub">{sub}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

# ===== Streamlit application =====

import math
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="Metals Intelligence", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
inject_css()

PLOT_BG = "rgba(0,0,0,0)"
GRID = "rgba(255,255,255,.07)"
TEXT = "#C8D2DD"


def chart_layout(fig, height=400, margin=None):
    fig.update_layout(
        height=height,
        paper_bgcolor=PLOT_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT, size=12),
        margin=margin or dict(l=12, r=12, t=34, b=12),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


@st.cache_data(ttl=900, show_spinner=False)
def get_market(metal):
    return fetch_market_history(metal, "1y")


@st.cache_data(ttl=1800, show_spinner=False)
def get_weather(metal):
    return fetch_weather_for_metal(metal)


@st.cache_data(ttl=900, show_spinner=False)
def get_news(metal):
    return fetch_news(metal)


# Sidebar
st.sidebar.markdown("### ◈ METALS INTELLIGENCE")
st.sidebar.caption("Copper · Aluminium · Nickel")
page = st.sidebar.radio("Navigate", ["Overview", "Metal Deep Dive", "Weather & Disruption", "News Intelligence", "Compare", "Methodology"], label_visibility="collapsed")
st.sidebar.markdown("---")
selected_metal = st.sidebar.selectbox("Focus metal", list(METALS.keys()), index=0)
st.sidebar.markdown("---")
if st.sidebar.button("↻ Refresh live data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption(f"Session refresh: {datetime.now().strftime('%d %b %Y · %H:%M')}")
st.sidebar.caption("Independent analytics project · verify exchange/licensed feeds before publishing market-sensitive claims.")

# Load shared datasets
market_store = {}
metrics_store = {}
weather_store = {}
score_store = {}
source_store = {}
for metal in METALS:
    market_df, source_note, market_live = get_market(metal)
    market_store[metal] = market_df
    source_store[metal] = {"label": source_note, "live": market_live}
    metrics_store[metal] = market_metrics(market_df)
    w = get_weather(metal)
    weather_store[metal] = w
    inv, inv_note, inv_verified = load_inventory_series(metal)
    score_store[metal] = tightness_score(metal, market_df, inv, aggregate_weather_risk(w))


if page == "Overview":
    hero(
        "Industrial Metals Market Intelligence",
        "A clean decision dashboard for copper, aluminium and nickel — combining market data, momentum, inventories, weather-linked disruption risk and news intelligence.",
    )

    cols = st.columns(3)
    for i, metal in enumerate(METALS):
        m = metrics_store[metal]
        s = score_store[metal]
        with cols[i]:
            st.markdown(f"### {METALS[metal].symbol} · {metal}")
            c1, c2 = st.columns(2)
            with c1:
                metric_card("Latest price", f"{m['price']:,.2f}", METALS[metal].unit)
            with c2:
                metric_card("Tightness", f"{s['score']:.0f}/100", s['label'])
            c3, c4, c5 = st.columns(3)
            c3.metric("1D", f"{m['1d']:+.2f}%")
            c4.metric("1M", f"{m['1m']:+.2f}%")
            c5.metric("Vol (20D)", f"{m['vol']:.1f}%")
            status = "LIVE / PUBLIC" if source_store[metal]["live"] else "DEMO FALLBACK"
            st.caption(f"{status} · {source_store[metal]['label']}")

    st.markdown("### Cross-metal price performance")
    perf = pd.DataFrame()
    for metal, df in market_store.items():
        s = df["Close"].dropna().astype(float)
        s = s / s.iloc[0] * 100
        perf[metal] = s
    fig = px.line(perf, labels={"value": "Indexed performance", "index": "Date", "variable": "Metal"})
    chart_layout(fig, 390)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    left, right = st.columns([1.45, 1])
    with left:
        st.markdown("### Tightness model breakdown")
        rows = []
        for metal, score in score_store.items():
            for factor in ["Inventory level", "Inventory trend", "Price momentum", "Volatility", "Weather risk"]:
                rows.append({"Metal": metal, "Factor": factor, "Score": score[factor]})
        df_scores = pd.DataFrame(rows)
        fig = px.bar(df_scores, x="Metal", y="Score", color="Factor", barmode="group", range_y=[0, 100])
        chart_layout(fig, 380)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with right:
        st.markdown("### Weather-linked disruption watch")
        for metal in METALS:
            risk = aggregate_weather_risk(weather_store[metal])
            st.metric(metal, f"{risk:.0f}/100", "average monitored-region risk")
        st.caption("Weather risk is a screening indicator based on 7-day rainfall, wind and temperature thresholds. It is not a production-loss forecast.")

elif page == "Metal Deep Dive":
    metal = selected_metal
    cfg = METALS[metal]
    df = enrich_market_data(market_store[metal])
    metrics = metrics_store[metal]
    inv, inv_note, inv_verified = load_inventory_series(metal)
    score = score_store[metal]

    hero(f"{cfg.symbol} · {metal}", f"Market structure, momentum, inventory signals and a transparent physical-tightness framework for {metal.lower()}.", eyebrow="Metal deep dive")

    a,b,c,d,e = st.columns(5)
    a.metric("Latest", f"{metrics['price']:,.2f}", cfg.unit)
    b.metric("1W", f"{metrics['1w']:+.2f}%")
    c.metric("1M", f"{metrics['1m']:+.2f}%")
    d.metric("20D vol", f"{metrics['vol']:.1f}%")
    e.metric("Tightness", f"{score['score']:.0f}/100", score['label'])
    status = "LIVE / PUBLIC" if source_store[metal]["live"] else "DEMO FALLBACK"
    st.caption(f"Market source: {status} · {source_store[metal]['label']}")

    tabs = st.tabs(["Price & momentum", "Inventory", "Tightness model", "Research note"])
    with tabs[0]:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close", line=dict(width=2.2)))
        fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], name="20D MA", line=dict(width=1.2, dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="50D MA", line=dict(width=1.2, dash="dash")))
        chart_layout(fig, 460)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        c1, c2 = st.columns(2)
        with c1:
            r = df["Return"].dropna() * 100
            fig2 = px.histogram(r, nbins=45, labels={"value":"Daily return (%)"})
            chart_layout(fig2, 300)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        with c2:
            fig3 = px.line(df, y="Vol20", labels={"Vol20": "Annualised volatility", "index":"Date"})
            chart_layout(fig3, 300)
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with tabs[1]:
        if inv_verified:
            st.success(inv_note)
        else:
            st.info(inv_note + " Add data/<metal>_inventory.csv to upgrade this panel automatically.")
        fig = px.area(inv, y="Inventory", labels={"Inventory":"Inventory", "index":"Date"})
        chart_layout(fig, 430)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        latest = float(inv["Inventory"].iloc[-1])
        m1 = (latest / float(inv["Inventory"].iloc[-22]) - 1) * 100
        pctl = (inv["Inventory"] <= latest).mean() * 100
        c1,c2,c3 = st.columns(3)
        c1.metric("Latest inventory" if inv_verified else "Illustrative inventory", f"{latest:,.0f}")
        c2.metric("30D change", f"{m1:+.1f}%")
        c3.metric("1Y percentile", f"{pctl:.0f}th")

    with tabs[2]:
        st.markdown("#### Custom market tightness framework")
        st.caption("Weighted score: inventory level 30% · inventory trend 25% · price momentum 20% · weather 15% · volatility 10%.")
        breakdown = pd.DataFrame({"Factor": ["Inventory level", "Inventory trend", "Price momentum", "Volatility", "Weather risk"], "Score": [score["Inventory level"], score["Inventory trend"], score["Price momentum"], score["Volatility"], score["Weather risk"]]})
        fig = px.bar(breakdown, x="Score", y="Factor", orientation="h", range_x=[0,100])
        chart_layout(fig, 360)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f"**Current model read:** {score['score']:.0f}/100 — {score['label']}.**")
        st.caption("This is an analytical screening score, not an investment recommendation or price forecast.")

    with tabs[3]:
        st.markdown("#### Analyst note template")
        st.text_area("Thesis", value=f"{metal}: summarise what changed in price, inventories, supply/demand and weather risk. State what would confirm or invalidate the thesis.", height=130)
        st.text_area("Catalysts to watch", value="• Major producer guidance\n• Inventory changes\n• China demand indicators\n• Policy / trade changes\n• Weather / logistics disruptions", height=140)
        st.download_button("Download note template", data=f"{metal} Market Note\n\nThesis:\n\nCatalysts:\n\nRisks:\n\nWhat would change my view:\n", file_name=f"{metal.lower()}_market_note.txt")

elif page == "Weather & Disruption":
    metal = selected_metal
    hero("Weather & Disruption Intelligence", f"Near-term weather monitoring across key {metal.lower()} production, processing and logistics regions.", eyebrow=f"{metal} · operational risk")
    rows = weather_store[metal]
    live_rows = [r for r in rows if r.get("live")]
    if not live_rows:
        st.warning("Live Open-Meteo data is unavailable in this environment. The dashboard will fetch it automatically when internet access is available.")
    cols = st.columns(len(rows))
    for col, r in zip(cols, rows):
        with col:
            st.markdown(f"### {r['name']}")
            st.caption(r["type"])
            if r.get("live"):
                st.metric("Weather risk", f"{r['risk']:.0f}/100")
                st.metric("7D precipitation", f"{r['precip_7d']:.1f} mm")
                st.metric("Max wind", f"{r['max_wind']:.0f} km/h")
                st.caption(" · ".join(r["reasons"]))
            else:
                st.metric("Weather risk", "—")
                st.caption("Live data unavailable")

    if live_rows:
        all_daily = []
        for r in live_rows:
            for date, p in zip(r["dates"], r["precip_daily"]):
                all_daily.append({"Date": date, "Region": r["name"], "Rainfall (mm)": p})
        rain = pd.DataFrame(all_daily)
        fig = px.bar(rain, x="Date", y="Rainfall (mm)", color="Region", barmode="group")
        chart_layout(fig, 420)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        map_df = pd.DataFrame([{"Region": r["name"], "lat": r["lat"], "lon": r["lon"], "Risk": r["risk"]} for r in live_rows])
        st.map(map_df, latitude="lat", longitude="lon", size="Risk", zoom=1)
    st.caption("Weather logic is intentionally transparent. It flags near-term operational risk; it does not infer actual mine/smelter downtime without corroborating company or news evidence.")

elif page == "News Intelligence":
    metal = selected_metal
    hero("News Intelligence", f"A live headline layer for {metal.lower()}, tagged by supply, demand, policy, logistics and macro themes.", eyebrow=f"{metal} · event monitor")
    news = get_news(metal)
    if not news:
        st.warning("Live RSS news is unavailable here. When the app has internet access, this page will populate automatically.")
    else:
        filters = st.multiselect("Filter category", ["Supply", "Demand", "Policy", "Logistics", "Macro", "Market"], default=[])
        shown = [n for n in news if not filters or n["category"] in filters]
        for n in shown:
            st.markdown(
                f"""
<div class="news-card">
  <span class="pill">{n['category']}</span> <span class="pill">{n['impact']} impact</span> <span class="pill">{n['direction']}</span>
  <div class="news-title"><a href="{n['link']}" target="_blank">{n['title']}</a></div>
  <div class="news-meta">{n['published']}</div>
</div>
                """,
                unsafe_allow_html=True,
            )
        st.caption("Direction/impact tags are keyword-based screening labels only. Read the source before making any market judgement.")

elif page == "Compare":
    hero("Cross-Metal Comparison", "Compare market momentum, volatility, inventory signals and weather-linked disruption risk across the three focus metals.", eyebrow="Relative-value lens")
    compare = []
    for metal in METALS:
        m = metrics_store[metal]
        s = score_store[metal]
        compare.append({
            "Metal": metal,
            "Price": m["price"],
            "1D %": m["1d"],
            "1M %": m["1m"],
            "3M %": m["3m"],
            "Volatility %": m["vol"],
            "Tightness": s["score"],
            "Weather risk": s["Weather risk"],
        })
    cmp = pd.DataFrame(compare).set_index("Metal")
    st.dataframe(cmp.style.format({"Price":"{:,.2f}", "1D %":"{:+.2f}", "1M %":"{:+.2f}", "3M %":"{:+.2f}", "Volatility %":"{:.1f}", "Tightness":"{:.0f}", "Weather risk":"{:.0f}"}), use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(cmp.reset_index(), x="Metal", y="Tightness", range_y=[0,100])
        chart_layout(fig, 330)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with c2:
        fig = px.scatter(cmp.reset_index(), x="Volatility %", y="1M %", size="Tightness", text="Metal")
        chart_layout(fig, 330)
        fig.update_traces(textposition="top center")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

elif page == "Methodology":
    hero("Methodology & Data Architecture", "A transparent framework so the project is defensible in an interview, reproducible on GitHub and easy to upgrade to licensed exchange feeds.", eyebrow="How the platform works")
    st.markdown("""
### 1 · Market layer
The public-market connector attempts to pull data via `yfinance`. Copper uses COMEX copper futures; aluminium uses the available aluminium futures symbol; nickel uses a nickel-linked exchange-traded proxy because clean free daily LME nickel history is not reliably available. Every source is labelled explicitly, and a clearly marked demo fallback keeps the UI usable if a public feed is unavailable.

### 2 · Inventory layer
The bundled inventory series is **illustrative** so the project works immediately. Replace it with verified LME / SHFE / exchange inventory history or a licensed data feed before quoting inventory values externally.

### 3 · Weather layer
Open-Meteo is used for live, no-key 7-day weather data in selected mining, processing and logistics regions. The disruption score is based on rainfall, wind and temperature thresholds. It is a screening signal, not a production-loss forecast.

### 4 · News layer
Google News RSS provides headlines. A simple transparent keyword model classifies each event as Supply, Demand, Policy, Logistics, Macro or Market, then adds a provisional direction and impact label.

### 5 · Tightness model
**Inventory level 30% · Inventory trend 25% · Price momentum 20% · Weather 15% · Volatility 10%.**  
The weights are intentionally explicit and editable. A later version should add cash/3M spreads, open interest, treatment charges, production guidance, trade flows and demand indicators.

### 6 · Portfolio-quality upgrade path
1. Connect a verified LME / exchange data source.  
2. Add cash-to-3M spread and forward-curve analytics.  
3. Add verified mine/smelter production and trade-flow datasets.  
4. Backtest the tightness score against subsequent returns and inventory changes.  
5. Publish fortnightly research notes with dated hypotheses and post-mortems.  
6. Link the live Streamlit app and GitHub repository on your CV.
    """)
