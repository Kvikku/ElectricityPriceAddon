"""Constants for the Norway Electricity Prices integration."""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

DOMAIN = "norway_electricity"

API_URL_TEMPLATE = "https://www.hvakosterstrommen.no/api/v1/prices/{year}/{month}-{day}_{area}.json"

PRICE_AREAS: dict[str, str] = {
    "NO1": "Oslo / Øst-Norge",
    "NO2": "Kristiansand / Sør-Norge",
    "NO3": "Trondheim / Midt-Norge",
    "NO4": "Tromsø / Nord-Norge",
    "NO5": "Bergen / Vest-Norge",
}

CONF_AREA = "price_area"
CONF_VAT = "vat"
CONF_CHEAP_HOURS = "cheap_hours"
CONF_EXPENSIVE_HOURS = "expensive_hours"

DEFAULT_VAT = True
VAT_MULTIPLIER = 1.25

DEFAULT_CHEAP_HOURS = 6
DEFAULT_EXPENSIVE_HOURS = 6

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
