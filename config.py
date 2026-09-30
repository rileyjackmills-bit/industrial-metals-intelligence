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
