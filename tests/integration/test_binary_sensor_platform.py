"""Integration tests for the binary sensor platform."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.norway_electricity.const import (
    CONF_AREA,
    CONF_CHEAP_HOURS,
    CONF_EXPENSIVE_HOURS,
    CONF_HIGH_THRESHOLD,
    CONF_LOW_THRESHOLD,
    CONF_VAT,
    DOMAIN,
)

from .conftest import TODAY_RAW, patch_fetch_prices

pytestmark = pytest.mark.integration

# Expected unique IDs for all four binary sensors created per area
BINARY_SENSOR_UNIQUE_IDS = [
    "norway_electricity_NO1_cheapest_hours",
    "norway_electricity_NO1_expensive_hours",
    "norway_electricity_NO1_price_below_threshold",
    "norway_electricity_NO1_price_above_threshold",
]


@pytest.fixture
async def loaded_entry(hass):
    """Create and load a config entry for NO1 with mocked price data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_AREA: "NO1"},
        options={
            CONF_VAT: True,
            CONF_CHEAP_HOURS: 6,
            CONF_EXPENSIVE_HOURS: 6,
            CONF_LOW_THRESHOLD: None,
            CONF_HIGH_THRESHOLD: None,
        },
        unique_id="NO1",
    )
    entry.add_to_hass(hass)

    with patch_fetch_prices(today=TODAY_RAW):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


@pytest.mark.asyncio
async def test_all_binary_sensor_entities_registered(hass, loaded_entry):
    """After setup, all four binary sensor entities should exist in the entity registry."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for uid in BINARY_SENSOR_UNIQUE_IDS:
        entity_id = registry.async_get_entity_id("binary_sensor", DOMAIN, uid)
        assert entity_id is not None, f"Binary sensor with unique_id '{uid}' not found in registry"


@pytest.mark.asyncio
async def test_cheapest_hours_sensor_has_state(hass, loaded_entry):
    """The cheapest hours binary sensor should have a boolean state."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("binary_sensor", DOMAIN, "norway_electricity_NO1_cheapest_hours")
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state in ("on", "off")


@pytest.mark.asyncio
async def test_threshold_sensors_unavailable_when_not_configured(hass, loaded_entry):
    """Price threshold sensors should be unavailable when thresholds are None."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for uid in ("norway_electricity_NO1_price_below_threshold", "norway_electricity_NO1_price_above_threshold"):
        entity_id = registry.async_get_entity_id("binary_sensor", DOMAIN, uid)
        assert entity_id is not None
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state in ("unavailable",), f"{uid} should be unavailable without threshold set"


@pytest.mark.asyncio
async def test_threshold_sensors_active_when_configured(hass):
    """Price threshold sensors should have a boolean state when thresholds are set."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_AREA: "NO1"},
        options={
            CONF_VAT: True,
            CONF_CHEAP_HOURS: 6,
            CONF_EXPENSIVE_HOURS: 6,
            CONF_LOW_THRESHOLD: 5.00,  # very high — current will always be below
            CONF_HIGH_THRESHOLD: 0.001,  # very low — current will always be above
        },
        unique_id="NO1",
    )
    entry.add_to_hass(hass)

    with patch_fetch_prices(today=TODAY_RAW):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    below_id = registry.async_get_entity_id("binary_sensor", DOMAIN, "norway_electricity_NO1_price_below_threshold")
    above_id = registry.async_get_entity_id("binary_sensor", DOMAIN, "norway_electricity_NO1_price_above_threshold")
    assert below_id is not None
    assert above_id is not None

    below_state = hass.states.get(below_id)
    above_state = hass.states.get(above_id)
    assert below_state.state == "on", "Price should be below the very high threshold (5.00 NOK/kWh)"
    assert above_state.state == "on", "Price should be above the very low threshold (0.001 NOK/kWh)"
