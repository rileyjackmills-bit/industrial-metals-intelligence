from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

import requests

from .config import WEATHER_REGIONS

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
