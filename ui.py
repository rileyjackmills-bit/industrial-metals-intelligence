from __future__ import annotations

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
