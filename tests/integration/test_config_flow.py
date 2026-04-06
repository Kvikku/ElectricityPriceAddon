"""Integration tests for the config flow and options flow."""

from __future__ import annotations

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.norway_electricity.const import (
    CONF_AREA,
    CONF_CHEAP_HOURS,
    CONF_EXPENSIVE_HOURS,
    CONF_VAT,
    DEFAULT_CHEAP_HOURS,
    DEFAULT_EXPENSIVE_HOURS,
    DEFAULT_VAT,
    DOMAIN,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_config_flow_creates_entry(hass):
    """Submitting a valid area through the config flow creates a config entry."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_AREA: "NO1"})
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_AREA] == "NO1"
    # Options should be initialised with defaults
    assert result["options"][CONF_VAT] == DEFAULT_VAT
    assert result["options"][CONF_CHEAP_HOURS] == DEFAULT_CHEAP_HOURS
    assert result["options"][CONF_EXPENSIVE_HOURS] == DEFAULT_EXPENSIVE_HOURS


@pytest.mark.asyncio
async def test_config_flow_rejects_duplicate_area(hass):
    """Adding the same area twice aborts with already_configured."""
    # First entry
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_AREA: "NO3"})

    # Second entry for the same area
    result2 = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result2 = await hass.config_entries.flow.async_configure(result2["flow_id"], {CONF_AREA: "NO3"})
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_options_flow_saves_options(hass):
    """Submitting the options flow stores updated values on the config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_AREA: "NO2"},
        options={
            CONF_VAT: True,
            CONF_CHEAP_HOURS: 6,
            CONF_EXPENSIVE_HOURS: 6,
        },
        unique_id="NO2",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_VAT: False,
            CONF_CHEAP_HOURS: 4,
            CONF_EXPENSIVE_HOURS: 3,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_VAT] is False
    assert entry.options[CONF_CHEAP_HOURS] == 4
    assert entry.options[CONF_EXPENSIVE_HOURS] == 3


@pytest.mark.asyncio
async def test_config_flow_supports_nordic_areas(hass):
    """Each supported Nordic area code can be used to create a config entry."""
    nordic_areas = ["SE1", "SE2", "SE3", "SE4", "DK1", "DK2", "FI"]
    for area in nordic_areas:
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_AREA: area})
        assert result["type"] == FlowResultType.CREATE_ENTRY, f"Expected CREATE_ENTRY for area {area}"
        assert result["data"][CONF_AREA] == area
