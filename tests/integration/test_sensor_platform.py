"""Integration tests for the sensor platform."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.norway_electricity.const import (
    CONF_AREA,
    CONF_CHEAP_HOURS,
    CONF_EXPENSIVE_HOURS,
    CONF_VAT,
    DOMAIN,
)

from .conftest import TODAY_RAW, TOMORROW_RAW, patch_fetch_prices

pytestmark = pytest.mark.integration

# Expected unique IDs for all nine sensors created per area
SENSOR_UNIQUE_IDS = [
    "norway_electricity_NO1_current_price",
    "norway_electricity_NO1_next_hour_price",
    "norway_electricity_NO1_average_price",
    "norway_electricity_NO1_min_price",
    "norway_electricity_NO1_max_price",
    "norway_electricity_NO1_price_level",
    "norway_electricity_NO1_tomorrow_average_price",
    "norway_electricity_NO1_tomorrow_min_price",
    "norway_electricity_NO1_tomorrow_max_price",
]


@pytest.fixture
async def loaded_entry(hass):
    """Create and load a config entry for NO1 with mocked price data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_AREA: "NO1"},
        options={CONF_VAT: True, CONF_CHEAP_HOURS: 6, CONF_EXPENSIVE_HOURS: 6},
        unique_id="NO1",
    )
    entry.add_to_hass(hass)

    with patch_fetch_prices(today=TODAY_RAW, tomorrow=TOMORROW_RAW):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


@pytest.mark.asyncio
async def test_all_sensor_entities_registered(hass, loaded_entry):
    """After setup, all nine sensor entities should exist in the entity registry."""
    for uid in SENSOR_UNIQUE_IDS:
        # Entity IDs are not directly predictable, but every sensor state must be loaded
        # We check via the entity registry unique_id lookup
        from homeassistant.helpers import entity_registry as er

        registry = er.async_get(hass)
        entry = registry.async_get_entity_id("sensor", DOMAIN, uid)
        assert entry is not None, f"Sensor with unique_id '{uid}' not found in registry"


@pytest.mark.asyncio
async def test_current_price_sensor_has_state(hass, loaded_entry):
    """The current price sensor should have a numeric state."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, "norway_electricity_NO1_current_price")
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state not in ("unavailable", "unknown")
    assert float(state.state) >= 0


@pytest.mark.asyncio
async def test_tomorrow_sensors_available_when_tomorrow_data_present(hass, loaded_entry):
    """Tomorrow Average/Min/Max sensors should be available when tomorrow data is fetched."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for key in ("tomorrow_average_price", "tomorrow_min_price", "tomorrow_max_price"):
        uid = f"norway_electricity_NO1_{key}"
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, uid)
        assert entity_id is not None, f"Sensor {uid} not found"
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state not in ("unavailable", "unknown"), f"Sensor {uid} should have a value"


@pytest.mark.asyncio
async def test_tomorrow_sensors_unavailable_when_no_tomorrow_data(hass):
    """Tomorrow sensors should be unavailable when tomorrow data is not yet published."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_AREA: "NO1"},
        options={CONF_VAT: True, CONF_CHEAP_HOURS: 6, CONF_EXPENSIVE_HOURS: 6},
        unique_id="NO1",
    )
    entry.add_to_hass(hass)

    with patch_fetch_prices(today=TODAY_RAW, tomorrow=None):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for key in ("tomorrow_average_price", "tomorrow_min_price", "tomorrow_max_price"):
        uid = f"norway_electricity_NO1_{key}"
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, uid)
        assert entity_id is not None
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state in ("unavailable", "unknown"), f"Sensor {uid} should be unavailable without tomorrow data"
