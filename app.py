from __future__ import annotations

import math
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import METALS, WEATHER_REGIONS
from src.market_data import fetch_market_history, market_metrics, enrich_market_data, load_inventory_series, tightness_score
from src.weather import fetch_weather_for_metal, aggregate_weather_risk
from src.news import fetch_news
from src.ui import inject_css, hero, metric_card

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
