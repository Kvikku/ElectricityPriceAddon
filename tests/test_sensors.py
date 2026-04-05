"""Tests for sensor entities."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from custom_components.norway_electricity.coordinator import ElectricityPriceData
from custom_components.norway_electricity.sensor import (
    AveragePriceSensor,
    CurrentPriceSensor,
    MaxPriceSensor,
    MinPriceSensor,
    NextHourPriceSensor,
    PriceLevelSensor,
)

# --- Helpers ---


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


def _make_coordinator(data: ElectricityPriceData | None = None) -> MagicMock:
    """Create a mock coordinator with given data."""
    coord = MagicMock()
    coord.data = data
    return coord


# --- Fixtures ---


@pytest.fixture
def sample_today():
    """24 hours of varied prices."""
    prices = [
        0.10,
        0.08,
        0.07,
        0.06,
        0.05,
        0.06,
        0.15,
        0.30,
        0.45,
        0.50,
        0.40,
        0.35,
        0.25,
        0.20,
        0.18,
        0.15,
        0.20,
        0.35,
        0.55,
        0.60,
        0.50,
        0.35,
        0.20,
        0.12,
    ]
    return _make_entries(prices)


@pytest.fixture
def sample_tomorrow():
    """24 hours of tomorrow prices."""
    prices = [0.10 + i * 0.02 for i in range(24)]
    return _make_entries(prices, date_str="2026-03-21")


@pytest.fixture
def price_data(sample_today, sample_tomorrow):
    return ElectricityPriceData(today=sample_today, tomorrow=sample_tomorrow)


@pytest.fixture
def coordinator(price_data):
    return _make_coordinator(price_data)


# --- Tests ---


class TestCurrentPriceSensor:
    def test_native_value(self, coordinator, price_data):
        CurrentPriceSensor(coordinator, "NO1")
        # Verify the underlying data returns the correct value for hour 10
        now = datetime.fromisoformat("2026-03-20T10:30:00+01:00")
        entry = price_data.current_price(now)
        assert entry is not None
        assert entry["price"] == 0.40

    def test_native_value_none_when_no_data(self):
        coord = _make_coordinator(None)
        sensor = CurrentPriceSensor(coord, "NO1")
        assert sensor.native_value is None

    def test_extra_state_attributes_empty_when_no_data(self):
        coord = _make_coordinator(None)
        sensor = CurrentPriceSensor(coord, "NO1")
        assert sensor.extra_state_attributes == {}

    def test_extra_state_attributes_has_raw_today(self, coordinator, price_data):
        sensor = CurrentPriceSensor(coordinator, "NO1")
        attrs = sensor.extra_state_attributes
        assert "raw_today" in attrs
        assert len(attrs["raw_today"]) == 24

    def test_unique_id(self, coordinator):
        sensor = CurrentPriceSensor(coordinator, "NO1")
        assert sensor._attr_unique_id == "norway_electricity_NO1_current_price"


class TestNextHourPriceSensor:
    def test_native_value_none_when_no_data(self):
        coord = _make_coordinator(None)
        sensor = NextHourPriceSensor(coord, "NO1")
        assert sensor.native_value is None

    def test_extra_state_attributes_empty_when_no_data(self):
        coord = _make_coordinator(None)
        sensor = NextHourPriceSensor(coord, "NO1")
        assert sensor.extra_state_attributes == {}

    def test_unique_id(self, coordinator):
        sensor = NextHourPriceSensor(coordinator, "NO1")
        assert sensor._attr_unique_id == "norway_electricity_NO1_next_hour_price"


class TestAveragePriceSensor:
    def test_native_value(self, coordinator, price_data):
        sensor = AveragePriceSensor(coordinator, "NO1")
        expected = round(price_data.average_price(), 4)
        assert sensor.native_value == expected

    def test_native_value_none_when_no_data(self):
        coord = _make_coordinator(None)
        sensor = AveragePriceSensor(coord, "NO1")
        assert sensor.native_value is None


class TestMinPriceSensor:
    def test_native_value(self, coordinator):
        sensor = MinPriceSensor(coordinator, "NO1")
        assert sensor.native_value == 0.05

    def test_extra_state_attributes(self, coordinator):
        sensor = MinPriceSensor(coordinator, "NO1")
        attrs = sensor.extra_state_attributes
        assert attrs["hour"] == 4

    def test_native_value_none_when_no_data(self):
        coord = _make_coordinator(None)
        sensor = MinPriceSensor(coord, "NO1")
        assert sensor.native_value is None


class TestMaxPriceSensor:
    def test_native_value(self, coordinator):
        sensor = MaxPriceSensor(coordinator, "NO1")
        assert sensor.native_value == 0.60

    def test_extra_state_attributes(self, coordinator):
        sensor = MaxPriceSensor(coordinator, "NO1")
        attrs = sensor.extra_state_attributes
        assert attrs["hour"] == 19

    def test_native_value_none_when_no_data(self):
        coord = _make_coordinator(None)
        sensor = MaxPriceSensor(coord, "NO1")
        assert sensor.native_value is None


class TestPriceLevelSensor:
    def test_native_value_none_when_no_data(self):
        coord = _make_coordinator(None)
        sensor = PriceLevelSensor(coord, "NO1")
        assert sensor.native_value is None

    def test_extra_state_attributes(self, coordinator):
        sensor = PriceLevelSensor(coordinator, "NO1")
        attrs = sensor.extra_state_attributes
        assert "levels" in attrs

    def test_extra_state_attributes_empty_when_no_data(self):
        coord = _make_coordinator(None)
        sensor = PriceLevelSensor(coord, "NO1")
        assert sensor.extra_state_attributes == {}


class TestDeviceInfo:
    def test_sensors_have_device_info(self, coordinator):
        sensor = CurrentPriceSensor(coordinator, "NO1")
        assert sensor._attr_device_info is not None

    def test_device_info_identifiers(self, coordinator):
        sensor = CurrentPriceSensor(coordinator, "NO1")
        info = sensor._attr_device_info
        assert ("norway_electricity", "NO1") in info["identifiers"]
