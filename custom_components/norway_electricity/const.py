"""Constants for the Norway Electricity Prices integration."""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

DOMAIN = "norway_electricity"

API_URL_TEMPLATE = "https://www.hvakosterstrommen.no/api/v1/prices/{year}/{month}-{day}_{area}.json"

PRICE_AREAS: dict[str, str] = {
    # Norway
    "NO1": "Oslo / Øst-Norge",
    "NO2": "Kristiansand / Sør-Norge",
    "NO3": "Trondheim / Midt-Norge",
    "NO4": "Tromsø / Nord-Norge",
    "NO5": "Bergen / Vest-Norge",
    # Sweden
    "SE1": "Luleå / Norra Sverige",
    "SE2": "Sundsvall / Mellersta Nord Sverige",
    "SE3": "Stockholm / Mellersta Syd Sverige",
    "SE4": "Malmö / Södra Sverige",
    # Denmark
    "DK1": "Jylland / Fyn (Vest-Danmark)",
    "DK2": "Sjælland (Øst-Danmark)",
    # Finland
    "FI": "Finland",
}

CONF_AREA = "price_area"
CONF_VAT = "vat"
CONF_CHEAP_HOURS = "cheap_hours"
CONF_EXPENSIVE_HOURS = "expensive_hours"
CONF_LOW_THRESHOLD = "low_price_threshold"
CONF_HIGH_THRESHOLD = "high_price_threshold"

DEFAULT_VAT = True
VAT_MULTIPLIER = 1.25

DEFAULT_CHEAP_HOURS = 6
DEFAULT_EXPENSIVE_HOURS = 6
DEFAULT_LOW_THRESHOLD: float | None = None
DEFAULT_HIGH_THRESHOLD: float | None = None

CURRENCY_NOK = "NOK/kWh"

EVENT_TOMORROW_AVAILABLE = f"{DOMAIN}_tomorrow_available"


class PriceEntry(TypedDict):
    """A single hourly price entry."""

    start: datetime
    end: datetime
    price: float
    price_eur: float
    hour: int


def serialize_entry(entry: PriceEntry) -> dict[str, str | float | int]:
    """Convert a PriceEntry to a JSON-serializable dict."""
    return {
        "start": entry["start"].isoformat(),
        "end": entry["end"].isoformat(),
        "price": entry["price"],
        "price_eur": entry["price_eur"],
        "hour": entry["hour"],
    }
