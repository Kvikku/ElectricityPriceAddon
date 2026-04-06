"""Data coordinator for Norway Electricity Prices."""

from __future__ import annotations

import datetime as dt
import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    API_URL_TEMPLATE,
    CONF_AREA,
    CONF_VAT,
    DEFAULT_VAT,
    DOMAIN,
    EVENT_TOMORROW_AVAILABLE,
    VAT_MULTIPLIER,
    PriceEntry,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=30)


class ElectricityPriceData:
    """Structured container for electricity price data."""

    def __init__(
        self,
        today: list[PriceEntry],
        tomorrow: list[PriceEntry] | None,
    ) -> None:
        self.today = today
        self.tomorrow = tomorrow

    @property
    def all_prices(self) -> list[PriceEntry]:
        """Return today + tomorrow combined."""
        if self.tomorrow:
            return self.today + self.tomorrow
        return list(self.today)

    def current_price(self, now: dt.datetime | None = None) -> PriceEntry | None:
        """Return the price entry for the current hour."""
        now = now or dt_util.now()
        for entry in self.all_prices:
            if entry["start"] <= now < entry["end"]:
                return entry
        return None

    def next_hour_price(self, now: dt.datetime | None = None) -> PriceEntry | None:
        """Return the price entry for the next hour."""
        return self.future_hour_price(1, now)

    def future_hour_price(self, hours_ahead: int, now: dt.datetime | None = None) -> PriceEntry | None:
        """Return the price entry for N hours from now."""
        now = now or dt_util.now()
        target = now + timedelta(hours=hours_ahead)
        for entry in self.all_prices:
            if entry["start"] <= target < entry["end"]:
                return entry
        return None

    def prices_sorted(self, entries: list[PriceEntry] | None = None) -> list[PriceEntry]:
        """Return entries sorted cheapest first."""
        source = entries if entries is not None else self.today
        return sorted(source, key=lambda e: e["price"])

    def average_price(self, entries: list[PriceEntry] | None = None) -> float:
        """Return average price for given entries (default: today)."""
        source = entries if entries is not None else self.today
        if not source:
            return 0.0
        return sum(e["price"] for e in source) / len(source)

    def min_entry(self, entries: list[PriceEntry] | None = None) -> PriceEntry | None:
        """Return the cheapest entry."""
        source = entries if entries is not None else self.today
        return min(source, key=lambda e: e["price"]) if source else None

    def max_entry(self, entries: list[PriceEntry] | None = None) -> PriceEntry | None:
        """Return the most expensive entry."""
        source = entries if entries is not None else self.today
        return max(source, key=lambda e: e["price"]) if source else None

    def price_level(self, now: dt.datetime | None = None) -> str:
        """Return a categorical level for the current price relative to today."""
        current = self.current_price(now)
        if not current or not self.today:
            return "unknown"
        price = current["price"]
        sorted_prices = sorted(e["price"] for e in self.today)
        count = len(sorted_prices)
        rank = sum(1 for p in sorted_prices if p < price)
        percentile = rank / count

        if percentile < 0.1:
            return "very_cheap"
        if percentile < 0.35:
            return "cheap"
        if percentile < 0.65:
            return "normal"
        if percentile < 0.9:
            return "expensive"
        return "very_expensive"

    def cheapest_hours(self, n: int) -> list[PriceEntry]:
        """Return the N cheapest hours today."""
        return self.prices_sorted()[:n]

    def most_expensive_hours(self, n: int) -> list[PriceEntry]:
        """Return the N most expensive hours today."""
        return self.prices_sorted()[-n:]

    def best_consecutive_window(self, hours: int) -> list[PriceEntry] | None:
        """Find the cheapest consecutive block of N hours from all available prices."""
        prices = self.all_prices
        if len(prices) < hours:
            return None

        # Sort by start time to ensure correct consecutive ordering
        prices_sorted_time = sorted(prices, key=lambda e: e["start"])

        best_cost = float("inf")
        best_window: list[PriceEntry] | None = None

        for i in range(len(prices_sorted_time) - hours + 1):
            window = prices_sorted_time[i : i + hours]
            # Verify they are actually consecutive hours
            is_consecutive = all(window[j + 1]["start"] == window[j]["end"] for j in range(len(window) - 1))
            if not is_consecutive:
                continue
            cost = sum(e["price"] for e in window)
            if cost < best_cost:
                best_cost = cost
                best_window = window

        return best_window


class ElectricityPriceCoordinator(DataUpdateCoordinator[ElectricityPriceData]):
    """Coordinator to fetch electricity prices from hvakosterstrommen.no."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.area: str = entry.data[CONF_AREA]
        self.entry = entry
        self._tomorrow_notified: str | None = None  # date string of last notification

    @property
    def use_vat(self) -> bool:
        """Whether to include VAT in prices."""
        return self.entry.options.get(CONF_VAT, DEFAULT_VAT)

    async def _async_update_data(self) -> ElectricityPriceData:
        """Fetch today's and (optionally) tomorrow's prices."""
        now = dt_util.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)

        today_prices = await self._fetch_prices(today)
        if not today_prices:
            raise UpdateFailed(f"Failed to fetch electricity prices for {today} area {self.area}")

        tomorrow_prices = await self._fetch_prices(tomorrow)

        # Fire event when tomorrow's prices become available for the first time
        if tomorrow_prices and self._tomorrow_notified != str(tomorrow):
            self._tomorrow_notified = str(tomorrow)
            self.hass.bus.async_fire(
                EVENT_TOMORROW_AVAILABLE,
                {"area": self.area, "date": str(tomorrow)},
            )

        return ElectricityPriceData(today=today_prices, tomorrow=tomorrow_prices)

    async def _fetch_prices(self, date: dt.date) -> list[PriceEntry] | None:
        """Fetch hourly prices for a given date and area."""
        url = API_URL_TEMPLATE.format(
            year=f"{date.year:04d}",
            month=f"{date.month:02d}",
            day=f"{date.day:02d}",
            area=self.area,
        )

        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url, timeout=_REQUEST_TIMEOUT) as response:
                if response.status == 404:
                    _LOGGER.debug("No data available for %s (404)", url)
                    return None
                if response.status != 200:
                    _LOGGER.warning("Unexpected status %s fetching %s", response.status, url)
                    return None
                raw = await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("Error fetching %s: %s", url, err)
            return None

        return self._parse_prices(raw)

    def _parse_prices(self, raw: list[dict[str, Any]]) -> list[PriceEntry]:
        """Parse API response into internal format."""
        vat = VAT_MULTIPLIER if self.use_vat else 1.0
        entries: list[PriceEntry] = []
        for item in raw:
            start = dt_util.parse_datetime(item["time_start"])
            end = dt_util.parse_datetime(item["time_end"])
            nok = item["NOK_per_kWh"] * vat
            eur = item["EUR_per_kWh"] * vat

            if start is None or end is None:
                _LOGGER.warning(
                    "Skipping malformed price entry (unparseable timestamps): %s",
                    item,
                )
                continue

            entries.append(
                PriceEntry(
                    start=start,
                    end=end,
                    price=round(nok, 4),
                    price_eur=round(eur, 4),
                    hour=start.hour,
                )
            )

        return sorted(entries, key=lambda e: e["start"])


_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)
