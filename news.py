from __future__ import annotations

from datetime import datetime
from urllib.parse import quote_plus

import feedparser

from .config import METALS, CATEGORY_KEYWORDS, BULLISH_WORDS, BEARISH_WORDS


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
