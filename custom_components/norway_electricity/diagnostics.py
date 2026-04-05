"""Diagnostics support for Norway Electricity Prices."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, serialize_entry
from .coordinator import ElectricityPriceCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: ElectricityPriceCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data

    diag: dict[str, Any] = {
        "config_entry": {
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "coordinator": {
            "area": coordinator.area,
            "use_vat": coordinator.use_vat,
            "update_interval_seconds": coordinator.update_interval.total_seconds()
            if coordinator.update_interval
            else None,
        },
    }

    if data:
        diag["data"] = {
            "today_count": len(data.today),
            "tomorrow_count": len(data.tomorrow) if data.tomorrow else 0,
            "today": [serialize_entry(e) for e in data.today],
            "tomorrow": [serialize_entry(e) for e in data.tomorrow] if data.tomorrow else None,
        }
    else:
        diag["data"] = None

    return diag
