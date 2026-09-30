from __future__ import annotations

import math
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from .config import METALS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
