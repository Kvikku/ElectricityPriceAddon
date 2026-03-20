"""Binary sensor platform for Norway Electricity Prices."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_AREA,
    CONF_CHEAP_HOURS,
    CONF_EXPENSIVE_HOURS,
    DEFAULT_CHEAP_HOURS,
    DEFAULT_EXPENSIVE_HOURS,
    DOMAIN,
)
from .coordinator import ElectricityPriceCoordinator, ElectricityPriceData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from a config entry."""
    coordinator: ElectricityPriceCoordinator = hass.data[DOMAIN][entry.entry_id]
    area = entry.data[CONF_AREA]

    async_add_entities(
        [
            CheapestHoursBinarySensor(coordinator, entry, area),
            ExpensiveHoursBinarySensor(coordinator, entry, area),
        ],
        update_before_add=True,
    )


class CheapestHoursBinarySensor(
    CoordinatorEntity[ElectricityPriceCoordinator], BinarySensorEntity
):
    """Binary sensor that is ON during the cheapest hours of the day."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:cash-minus"

    def __init__(self, coordinator, entry, area) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._area = area
        self._attr_unique_id = f"{DOMAIN}_{area}_cheapest_hours"
        self._attr_name = f"Cheapest Hours ({area})"

    @property
    def _num_hours(self) -> int:
        return self._entry.options.get(CONF_CHEAP_HOURS, DEFAULT_CHEAP_HOURS)

    @property
    def data(self) -> ElectricityPriceData | None:
        return self.coordinator.data

    @property
    def is_on(self) -> bool | None:
        if not self.data:
            return None
        current = self.data.current_price()
        if not current:
            return None
        cheapest = self.data.cheapest_hours(self._num_hours)
        return any(e["start"] == current["start"] for e in cheapest)

    @property
    def extra_state_attributes(self) -> dict:
        if not self.data:
            return {}

        cheapest = self.data.cheapest_hours(self._num_hours)
        sorted_by_time = sorted(cheapest, key=lambda e: e["start"])

        attrs = {
            "num_hours": self._num_hours,
            "cheapest_hours": [
                {
                    "hour": e["hour"],
                    "price": e["price"],
                    "start": e["start"].isoformat(),
                }
                for e in sorted_by_time
            ],
        }

        # Best consecutive charging window
        window = self.data.best_consecutive_window(self._num_hours)
        if window:
            attrs["best_consecutive_window"] = {
                "start": window[0]["start"].isoformat(),
                "end": window[-1]["end"].isoformat(),
                "hours": [
                    {"hour": e["hour"], "price": e["price"]} for e in window
                ],
                "average_price": round(
                    sum(e["price"] for e in window) / len(window), 4
                ),
            }

        return attrs


class ExpensiveHoursBinarySensor(
    CoordinatorEntity[ElectricityPriceCoordinator], BinarySensorEntity
):
    """Binary sensor that is ON during the most expensive hours of the day."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:cash-plus"

    def __init__(self, coordinator, entry, area) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._area = area
        self._attr_unique_id = f"{DOMAIN}_{area}_expensive_hours"
        self._attr_name = f"Expensive Hours ({area})"

    @property
    def _num_hours(self) -> int:
        return self._entry.options.get(CONF_EXPENSIVE_HOURS, DEFAULT_EXPENSIVE_HOURS)

    @property
    def data(self) -> ElectricityPriceData | None:
        return self.coordinator.data

    @property
    def is_on(self) -> bool | None:
        if not self.data:
            return None
        current = self.data.current_price()
        if not current:
            return None
        expensive = self.data.most_expensive_hours(self._num_hours)
        return any(e["start"] == current["start"] for e in expensive)

    @property
    def extra_state_attributes(self) -> dict:
        if not self.data:
            return {}

        expensive = self.data.most_expensive_hours(self._num_hours)
        sorted_by_time = sorted(expensive, key=lambda e: e["start"])

        return {
            "num_hours": self._num_hours,
            "expensive_hours": [
                {
                    "hour": e["hour"],
                    "price": e["price"],
                    "start": e["start"].isoformat(),
                }
                for e in sorted_by_time
            ],
        }
