"""Shared fixtures for integration tests.

These tests require `pytest-homeassistant-custom-component` to be installed
(see requirements_integration.txt). They run against a real in-process Home
Assistant instance and do NOT use the sys.modules mocking from tests/conftest.py.
"""

from __future__ import annotations

import contextlib
import datetime as dt_module
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import patch

from custom_components.norway_electricity.coordinator import ElectricityPriceCoordinator

# ---------------------------------------------------------------------------
# Fixed reference date used across all integration tests.
# dt_util.now() is patched to this value so that coordinator logic and
# entity state computations are deterministic regardless of when CI runs.
# ---------------------------------------------------------------------------
FIXED_NOW = datetime.fromisoformat("2026-03-20T12:00:00+01:00")
FIXED_TODAY = FIXED_NOW.date()
FIXED_TOMORROW = FIXED_TODAY + dt_module.timedelta(days=1)

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
# Patch helper: mock _fetch_prices AND dt_util.now so that:
#   - coordinator logic uses the fixed reference date (2026-03-20)
#   - entity state computations (current_price etc.) use the same fixed time
#   - no real HTTP requests are made
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def patch_fetch_prices(
    today: list[dict[str, Any]] | None = None,
    tomorrow: list[dict[str, Any]] | None = None,
):
    """Context manager that stubs coordinator data fetching with canned prices."""
    today_data = today if today is not None else TODAY_RAW
    tomorrow_data = tomorrow

    async def _fake_fetch(self: ElectricityPriceCoordinator, date: dt_module.date):
        if date == FIXED_TODAY:
            return self._parse_prices(today_data)
        if date == FIXED_TOMORROW:
            return self._parse_prices(tomorrow_data) if tomorrow_data else None
        return None

    with (
        patch(
            "custom_components.norway_electricity.coordinator.ElectricityPriceCoordinator._fetch_prices",
            new=_fake_fetch,
        ),
        patch(
            "custom_components.norway_electricity.coordinator.dt_util.now",
            return_value=FIXED_NOW,
        ),
    ):
        yield
