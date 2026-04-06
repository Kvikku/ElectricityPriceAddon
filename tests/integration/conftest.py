"""Shared fixtures for integration tests.

These tests require `pytest-homeassistant-custom-component` to be installed
(see requirements_integration.txt). They run against a real in-process Home
Assistant instance and do NOT use the sys.modules mocking from tests/conftest.py.
"""

from __future__ import annotations

import datetime as dt_module
from collections.abc import Generator
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import patch

from custom_components.norway_electricity.coordinator import ElectricityPriceCoordinator

# ---------------------------------------------------------------------------
# Sample price data factory
# ---------------------------------------------------------------------------


def make_raw_prices(base_hour: int = 0, date_str: str = "2026-03-20", count: int = 24) -> list[dict[str, Any]]:
    """Return a list of raw API price dicts (as returned by hvakosterstrommen.no)."""
    prices = []
    for i in range(count):
        hour = base_hour + i
        start = datetime.fromisoformat(f"{date_str}T{hour:02d}:00:00+01:00")
        end = start + timedelta(hours=1)
        nok = round(0.10 + i * 0.02, 4)
        prices.append(
            {
                "NOK_per_kWh": nok,
                "EUR_per_kWh": round(nok * 0.09, 4),
                "EXR": 11.11,
                "time_start": start.isoformat(),
                "time_end": end.isoformat(),
            }
        )
    return prices


TODAY_RAW = make_raw_prices(date_str="2026-03-20")
TOMORROW_RAW = make_raw_prices(date_str="2026-03-21")


# ---------------------------------------------------------------------------
# Patch helper: mock _fetch_prices so no real HTTP requests are made
# ---------------------------------------------------------------------------


def patch_fetch_prices(
    today: list[dict[str, Any]] | None = None,
    tomorrow: list[dict[str, Any]] | None = None,
) -> Generator:
    """Context manager that patches coordinator._fetch_prices with canned data."""
    today_data = today if today is not None else TODAY_RAW
    tomorrow_data = tomorrow
    today_date = dt_module.date.fromisoformat("2026-03-20")

    async def _fake_fetch(self: ElectricityPriceCoordinator, date: dt_module.date):
        if date == today_date:
            return self._parse_prices(today_data)
        return self._parse_prices(tomorrow_data) if tomorrow_data else None

    return patch(
        "custom_components.norway_electricity.coordinator.ElectricityPriceCoordinator._fetch_prices",
        new=_fake_fetch,
    )
