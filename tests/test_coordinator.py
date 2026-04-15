"""Tests for the ElectricityPriceData helper class and coordinator parsing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from custom_components.norway_electricity.coordinator import ElectricityPriceData

# --- Helpers ---

TZ = timezone(timedelta(hours=1))  # CET


def _make_entries(prices: list[float], base_hour: int = 0, date_str: str = "2026-03-20") -> list[dict]:
    """Create a list of hourly price entries for testing."""
    entries = []
    for i, price in enumerate(prices):
        hour = base_hour + i
        start = datetime.fromisoformat(f"{date_str}T{hour:02d}:00:00+01:00")
        end = start + timedelta(hours=1)
        entries.append(
            {
                "start": start,
                "end": end,
                "price": price,
                "price_eur": round(price * 0.09, 4),
                "hour": start.hour,
            }
        )
    return entries


# --- Fixtures ---


@pytest.fixture
def sample_today():
    """24 hours of varied prices."""
    # Prices roughly mimicking a real day: cheap at night, expensive in morning/evening
    prices = [
        0.10,
        0.08,
        0.07,
        0.06,
        0.05,
        0.06,  # 00-05 (night, cheap)
        0.15,
        0.30,
        0.45,
        0.50,
        0.40,
        0.35,  # 06-11 (morning peak)
        0.25,
        0.20,
        0.18,
        0.15,
        0.20,
        0.35,  # 12-17 (afternoon)
        0.55,
        0.60,
        0.50,
        0.35,
        0.20,
        0.12,  # 18-23 (evening peak)
    ]
    return _make_entries(prices)


@pytest.fixture
def sample_tomorrow():
    """24 hours of tomorrow prices."""
    prices = [0.10 + i * 0.02 for i in range(24)]
    return _make_entries(prices, date_str="2026-03-21")


@pytest.fixture
def data(sample_today, sample_tomorrow):
    return ElectricityPriceData(today=sample_today, tomorrow=sample_tomorrow)


@pytest.fixture
def data_today_only(sample_today):
    return ElectricityPriceData(today=sample_today, tomorrow=None)


# --- Tests ---


class TestCurrentPrice:
    def test_returns_correct_hour(self, data):
        now = datetime.fromisoformat("2026-03-20T10:30:00+01:00")
        entry = data.current_price(now)
        assert entry is not None
        assert entry["hour"] == 10
        assert entry["price"] == 0.40

    def test_returns_none_outside_range(self, data_today_only):
        # Way in the future (no data)
        now = datetime.fromisoformat("2026-03-22T10:00:00+01:00")
        assert data_today_only.current_price(now) is None


class TestNextHourPrice:
    def test_returns_next_hour(self, data):
        now = datetime.fromisoformat("2026-03-20T14:15:00+01:00")
        entry = data.next_hour_price(now)
        assert entry is not None
        assert entry["hour"] == 15
        assert entry["price"] == 0.15

    def test_wraps_to_tomorrow(self, data):
        now = datetime.fromisoformat("2026-03-20T23:30:00+01:00")
        entry = data.next_hour_price(now)
        assert entry is not None
        # Should return first hour of tomorrow
        assert entry["start"].day == 21


class TestFutureHourPrice:
    def test_2_hours_ahead(self, data):
        now = datetime.fromisoformat("2026-03-20T10:30:00+01:00")
        entry = data.future_hour_price(2, now)
        assert entry is not None
        assert entry["hour"] == 12
        assert entry["price"] == 0.25

    def test_3_hours_ahead(self, data):
        now = datetime.fromisoformat("2026-03-20T10:30:00+01:00")
        entry = data.future_hour_price(3, now)
        assert entry is not None
        assert entry["hour"] == 13
        assert entry["price"] == 0.20

    def test_wraps_to_tomorrow(self, data):
        now = datetime.fromisoformat("2026-03-20T22:30:00+01:00")
        entry = data.future_hour_price(3, now)
        assert entry is not None
        assert entry["start"].day == 21
        assert entry["hour"] == 1

    def test_returns_none_outside_range(self, data_today_only):
        now = datetime.fromisoformat("2026-03-20T23:00:00+01:00")
        assert data_today_only.future_hour_price(3, now) is None


class TestAveragePrice:
    def test_average_today(self, data):
        avg = data.average_price()
        assert avg == pytest.approx(sum(e["price"] for e in data.today) / 24, rel=1e-3)

    def test_average_empty(self):
        empty = ElectricityPriceData(today=[], tomorrow=None)
        assert empty.average_price() == 0.0


class TestMinMax:
    def test_min_entry(self, data):
        entry = data.min_entry()
        assert entry is not None
        assert entry["price"] == 0.05
        assert entry["hour"] == 4

    def test_max_entry(self, data):
        entry = data.max_entry()
        assert entry is not None
        assert entry["price"] == 0.60
        assert entry["hour"] == 19


class TestPriceLevel:
    def test_very_cheap(self, data):
        # Hour 4 has the cheapest price (0.05)
        now = datetime.fromisoformat("2026-03-20T04:30:00+01:00")
        assert data.price_level(now) == "very_cheap"

    def test_very_expensive(self, data):
        # Hour 19 has the most expensive price (0.60)
        now = datetime.fromisoformat("2026-03-20T19:30:00+01:00")
        assert data.price_level(now) == "very_expensive"

    def test_unknown_when_no_data(self):
        empty = ElectricityPriceData(today=[], tomorrow=None)
        assert empty.price_level() == "unknown"


class TestCheapestHours:
    def test_returns_n_cheapest(self, data):
        cheapest = data.cheapest_hours(3)
        assert len(cheapest) == 3
        prices = [e["price"] for e in cheapest]
        # Should be the 3 lowest
        assert sorted(prices) == prices  # already sorted ascending
        assert prices[-1] <= 0.07  # 3rd cheapest is 0.07


class TestMostExpensiveHours:
    def test_returns_n_most_expensive(self, data):
        expensive = data.most_expensive_hours(3)
        assert len(expensive) == 3
        prices = [e["price"] for e in expensive]
        assert min(prices) >= 0.50


class TestBestConsecutiveWindow:
    def test_finds_cheapest_block(self, data_today_only):
        window = data_today_only.best_consecutive_window(4)
        assert window is not None
        assert len(window) == 4
        # The cheapest 4 consecutive hours should be around 02:00-05:00
        hours = [e["hour"] for e in window]
        assert hours == [2, 3, 4, 5]

    def test_returns_none_when_insufficient_hours(self):
        short = ElectricityPriceData(today=_make_entries([0.1, 0.2]), tomorrow=None)
        assert short.best_consecutive_window(5) is None

    def test_spans_today_and_tomorrow(self, data):
        # With both today and tomorrow available, should find window across boundary
        window = data.best_consecutive_window(6)
        assert window is not None
        assert len(window) == 6


class TestBestConsecutiveWindowTomorrow:
    def test_finds_cheapest_block_tomorrow(self, data):
        window = data.best_consecutive_window_tomorrow(4)
        assert window is not None
        assert len(window) == 4
        # All hours should be from tomorrow (2026-03-21)
        for entry in window:
            assert entry["start"].day == 21

    def test_returns_none_when_no_tomorrow(self, data_today_only):
        assert data_today_only.best_consecutive_window_tomorrow(4) is None

    def test_returns_none_when_insufficient_hours(self, data):
        assert data.best_consecutive_window_tomorrow(25) is None


class TestParsePrices:
    def test_parse_roundtrip(self):
        """Test that the coordinator parses API format correctly."""
        from custom_components.norway_electricity.coordinator import (
            ElectricityPriceCoordinator,
        )

        raw = [
            {
                "NOK_per_kWh": 0.5,
                "EUR_per_kWh": 0.045,
                "EXR": 11.11,
                "time_start": "2026-03-20T00:00:00+01:00",
                "time_end": "2026-03-20T01:00:00+01:00",
            },
            {
                "NOK_per_kWh": 0.6,
                "EUR_per_kWh": 0.054,
                "EXR": 11.11,
                "time_start": "2026-03-20T01:00:00+01:00",
                "time_end": "2026-03-20T02:00:00+01:00",
            },
        ]

        # Create a lightweight object with just the attributes _parse_prices needs
        class MockCoord:
            use_vat = True

        coord = MockCoord()
        # Bind the unbound method to our mock
        entries = ElectricityPriceCoordinator._parse_prices(coord, raw)

        assert len(entries) == 2
        # With VAT (1.25): 0.5 * 1.25 = 0.625
        assert entries[0]["price"] == pytest.approx(0.625, rel=1e-3)
        assert entries[0]["hour"] == 0
        assert entries[1]["hour"] == 1

    @pytest.mark.parametrize(
        "area",
        [
            # Norway
            "NO1",
            "NO2",
            "NO3",
            "NO4",
            "NO5",
            # Sweden
            "SE1",
            "SE2",
            "SE3",
            "SE4",
            # Denmark
            "DK1",
            "DK2",
            # Finland
            "FI",
        ],
    )
    def test_all_nordic_areas_in_price_areas(self, area):
        """Verify every supported Nordic area code is listed in PRICE_AREAS."""
        from custom_components.norway_electricity.const import PRICE_AREAS

        assert area in PRICE_AREAS, f"{area} is missing from PRICE_AREAS"

    def test_no_extra_unknown_areas(self):
        """Verify PRICE_AREAS contains exactly the expected set of area codes."""
        from custom_components.norway_electricity.const import PRICE_AREAS

        expected = {"NO1", "NO2", "NO3", "NO4", "NO5", "SE1", "SE2", "SE3", "SE4", "DK1", "DK2", "FI"}
        assert set(PRICE_AREAS.keys()) == expected
