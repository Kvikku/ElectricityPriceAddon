"""Tests for binary sensor entities."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from custom_components.norway_electricity.binary_sensor import (
    CheapestHoursBinarySensor,
    ExpensiveHoursBinarySensor,
    PriceAboveThresholdBinarySensor,
    PriceBelowThresholdBinarySensor,
)
from custom_components.norway_electricity.coordinator import ElectricityPriceData

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


def _make_entry(cheap_hours: int = 6, expensive_hours: int = 6) -> MagicMock:
    """Create a mock config entry with options."""
    entry = MagicMock()
    entry.options = {"cheap_hours": cheap_hours, "expensive_hours": expensive_hours}
    return entry


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
def price_data(sample_today):
    return ElectricityPriceData(today=sample_today, tomorrow=None)


@pytest.fixture
def coordinator(price_data):
    return _make_coordinator(price_data)


@pytest.fixture
def entry():
    return _make_entry()


# --- Tests ---


class TestCheapestHoursBinarySensor:
    def test_is_on_during_cheap_hour(self, coordinator, entry, price_data):
        sensor = CheapestHoursBinarySensor(coordinator, entry, "NO1")
        # Hour 4 (0.05) is the cheapest — should be in top 6 cheapest
        fixed_now = datetime.fromisoformat("2026-03-20T04:30:00+01:00")
        with patch("custom_components.norway_electricity.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = fixed_now
            assert sensor.is_on is True

    def test_is_off_during_expensive_hour(self, coordinator, entry):
        sensor = CheapestHoursBinarySensor(coordinator, entry, "NO1")
        # Hour 19 (0.60) is the most expensive — should NOT be in top 6 cheapest
        fixed_now = datetime.fromisoformat("2026-03-20T19:30:00+01:00")
        with patch("custom_components.norway_electricity.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = fixed_now
            assert sensor.is_on is False

    def test_is_on_none_when_no_data(self, entry):
        coord = _make_coordinator(None)
        sensor = CheapestHoursBinarySensor(coord, entry, "NO1")
        assert sensor.is_on is None

    def test_extra_state_attributes_empty_when_no_data(self, entry):
        coord = _make_coordinator(None)
        sensor = CheapestHoursBinarySensor(coord, entry, "NO1")
        assert sensor.extra_state_attributes == {}

    def test_extra_state_attributes_has_cheapest_hours(self, coordinator, entry):
        sensor = CheapestHoursBinarySensor(coordinator, entry, "NO1")
        attrs = sensor.extra_state_attributes
        assert "cheapest_hours" in attrs
        assert "num_hours" in attrs
        assert attrs["num_hours"] == 6
        assert len(attrs["cheapest_hours"]) == 6

    def test_extra_state_attributes_has_best_consecutive_window(self, coordinator, entry):
        sensor = CheapestHoursBinarySensor(coordinator, entry, "NO1")
        attrs = sensor.extra_state_attributes
        assert "best_consecutive_window" in attrs
        window = attrs["best_consecutive_window"]
        assert "start" in window
        assert "end" in window
        assert "average_price" in window

    def test_unique_id(self, coordinator, entry):
        sensor = CheapestHoursBinarySensor(coordinator, entry, "NO1")
        assert sensor._attr_unique_id == "norway_electricity_NO1_cheapest_hours"


class TestExpensiveHoursBinarySensor:
    def test_is_on_during_expensive_hour(self, coordinator, entry, price_data):
        sensor = ExpensiveHoursBinarySensor(coordinator, entry, "NO1")
        # Hour 19 (0.60) is the most expensive — should be in top 6 expensive
        fixed_now = datetime.fromisoformat("2026-03-20T19:30:00+01:00")
        with patch("custom_components.norway_electricity.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = fixed_now
            assert sensor.is_on is True

    def test_is_off_during_cheap_hour(self, coordinator, entry):
        sensor = ExpensiveHoursBinarySensor(coordinator, entry, "NO1")
        # Hour 4 (0.05) is the cheapest — should NOT be in top 6 expensive
        fixed_now = datetime.fromisoformat("2026-03-20T04:30:00+01:00")
        with patch("custom_components.norway_electricity.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = fixed_now
            assert sensor.is_on is False

    def test_is_on_none_when_no_data(self, entry):
        coord = _make_coordinator(None)
        sensor = ExpensiveHoursBinarySensor(coord, entry, "NO1")
        assert sensor.is_on is None

    def test_extra_state_attributes_empty_when_no_data(self, entry):
        coord = _make_coordinator(None)
        sensor = ExpensiveHoursBinarySensor(coord, entry, "NO1")
        assert sensor.extra_state_attributes == {}

    def test_extra_state_attributes_has_expensive_hours(self, coordinator, entry):
        sensor = ExpensiveHoursBinarySensor(coordinator, entry, "NO1")
        attrs = sensor.extra_state_attributes
        assert "expensive_hours" in attrs
        assert "num_hours" in attrs
        assert attrs["num_hours"] == 6
        assert len(attrs["expensive_hours"]) == 6

    def test_unique_id(self, coordinator, entry):
        sensor = ExpensiveHoursBinarySensor(coordinator, entry, "NO1")
        assert sensor._attr_unique_id == "norway_electricity_NO1_expensive_hours"


class TestBinarySensorDeviceInfo:
    def test_has_device_info(self, coordinator, entry):
        sensor = CheapestHoursBinarySensor(coordinator, entry, "NO1")
        assert sensor._attr_device_info is not None

    def test_device_info_identifiers(self, coordinator, entry):
        sensor = CheapestHoursBinarySensor(coordinator, entry, "NO1")
        info = sensor._attr_device_info
        assert ("norway_electricity", "NO1") in info["identifiers"]


class TestPriceBelowThresholdBinarySensor:
    def _make_entry_with_threshold(self, low: float | None = None, high: float | None = None) -> MagicMock:
        entry = MagicMock()
        entry.options = {"low_price_threshold": low, "high_price_threshold": high}
        return entry

    def test_is_on_when_price_below_threshold(self, coordinator, price_data):
        # Hour 4 has price 0.05 — set threshold at 0.10 → should be ON
        entry = self._make_entry_with_threshold(low=0.10)
        sensor = PriceBelowThresholdBinarySensor(coordinator, entry, "NO1")
        fixed_now = datetime.fromisoformat("2026-03-20T04:30:00+01:00")
        with patch("custom_components.norway_electricity.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = fixed_now
            assert sensor.is_on is True

    def test_is_off_when_price_above_threshold(self, coordinator):
        # Hour 19 has price 0.60 — set threshold at 0.10 → should be OFF
        entry = self._make_entry_with_threshold(low=0.10)
        sensor = PriceBelowThresholdBinarySensor(coordinator, entry, "NO1")
        fixed_now = datetime.fromisoformat("2026-03-20T19:30:00+01:00")
        with patch("custom_components.norway_electricity.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = fixed_now
            assert sensor.is_on is False

    def test_is_on_none_when_threshold_not_set(self, coordinator):
        entry = self._make_entry_with_threshold(low=None)
        sensor = PriceBelowThresholdBinarySensor(coordinator, entry, "NO1")
        assert sensor.is_on is None

    def test_is_on_none_when_no_data(self):
        coord = _make_coordinator(None)
        entry = self._make_entry_with_threshold(low=0.50)
        sensor = PriceBelowThresholdBinarySensor(coord, entry, "NO1")
        assert sensor.is_on is None

    def test_extra_state_attributes_contains_threshold(self, coordinator):
        entry = self._make_entry_with_threshold(low=0.30)
        sensor = PriceBelowThresholdBinarySensor(coordinator, entry, "NO1")
        attrs = sensor.extra_state_attributes
        assert attrs["threshold"] == 0.30

    def test_extra_state_attributes_contains_current_price(self, coordinator, price_data):
        entry = self._make_entry_with_threshold(low=0.30)
        sensor = PriceBelowThresholdBinarySensor(coordinator, entry, "NO1")
        fixed_now = datetime.fromisoformat("2026-03-20T04:30:00+01:00")
        with patch("custom_components.norway_electricity.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = fixed_now
            attrs = sensor.extra_state_attributes
        assert "current_price" in attrs
        assert attrs["current_price"] == 0.05

    def test_unique_id(self, coordinator, entry):
        sensor = PriceBelowThresholdBinarySensor(coordinator, entry, "NO1")
        assert sensor._attr_unique_id == "norway_electricity_NO1_price_below_threshold"


class TestPriceAboveThresholdBinarySensor:
    def _make_entry_with_threshold(self, high: float | None = None) -> MagicMock:
        entry = MagicMock()
        entry.options = {"low_price_threshold": None, "high_price_threshold": high}
        return entry

    def test_is_on_when_price_above_threshold(self, coordinator, price_data):
        # Hour 19 has price 0.60 — set threshold at 0.50 → should be ON
        entry = self._make_entry_with_threshold(high=0.50)
        sensor = PriceAboveThresholdBinarySensor(coordinator, entry, "NO1")
        fixed_now = datetime.fromisoformat("2026-03-20T19:30:00+01:00")
        with patch("custom_components.norway_electricity.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = fixed_now
            assert sensor.is_on is True

    def test_is_off_when_price_below_threshold(self, coordinator):
        # Hour 4 has price 0.05 — set threshold at 0.50 → should be OFF
        entry = self._make_entry_with_threshold(high=0.50)
        sensor = PriceAboveThresholdBinarySensor(coordinator, entry, "NO1")
        fixed_now = datetime.fromisoformat("2026-03-20T04:30:00+01:00")
        with patch("custom_components.norway_electricity.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = fixed_now
            assert sensor.is_on is False

    def test_is_on_none_when_threshold_not_set(self, coordinator):
        entry = self._make_entry_with_threshold(high=None)
        sensor = PriceAboveThresholdBinarySensor(coordinator, entry, "NO1")
        assert sensor.is_on is None

    def test_is_on_none_when_no_data(self):
        coord = _make_coordinator(None)
        entry = self._make_entry_with_threshold(high=0.50)
        sensor = PriceAboveThresholdBinarySensor(coord, entry, "NO1")
        assert sensor.is_on is None

    def test_extra_state_attributes_contains_threshold(self, coordinator):
        entry = self._make_entry_with_threshold(high=0.80)
        sensor = PriceAboveThresholdBinarySensor(coordinator, entry, "NO1")
        attrs = sensor.extra_state_attributes
        assert attrs["threshold"] == 0.80

    def test_extra_state_attributes_contains_current_price(self, coordinator, price_data):
        entry = self._make_entry_with_threshold(high=0.30)
        sensor = PriceAboveThresholdBinarySensor(coordinator, entry, "NO1")
        fixed_now = datetime.fromisoformat("2026-03-20T19:30:00+01:00")
        with patch("custom_components.norway_electricity.coordinator.dt_util") as mock_dt:
            mock_dt.now.return_value = fixed_now
            attrs = sensor.extra_state_attributes
        assert "current_price" in attrs
        assert attrs["current_price"] == 0.60

    def test_unique_id(self, coordinator, entry):
        sensor = PriceAboveThresholdBinarySensor(coordinator, entry, "NO1")
        assert sensor._attr_unique_id == "norway_electricity_NO1_price_above_threshold"
