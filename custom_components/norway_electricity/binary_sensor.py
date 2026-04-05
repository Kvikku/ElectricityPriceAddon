"""Binary sensor platform for Norway Electricity Prices."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_AREA,
    CONF_CHEAP_HOURS,
    CONF_EXPENSIVE_HOURS,
    DEFAULT_CHEAP_HOURS,
    DEFAULT_EXPENSIVE_HOURS,
    DOMAIN,
    PRICE_AREAS,
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


class ElectricityBinarySensorBase(CoordinatorEntity[ElectricityPriceCoordinator], BinarySensorEntity):
    """Base class for electricity binary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ElectricityPriceCoordinator,
        entry: ConfigEntry,
        area: str,
        key: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._area = area
        self._attr_unique_id = f"{DOMAIN}_{area}_{key}"
        self._attr_name = f"{name} ({area})"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, area)},
            name=f"Electricity Prices {area}",
            manufacturer="hvakosterstrommen.no",
            model=PRICE_AREAS.get(area, area),
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def data(self) -> ElectricityPriceData | None:
        """Return coordinator data."""
        return self.coordinator.data


class CheapestHoursBinarySensor(ElectricityBinarySensorBase):
    """Binary sensor that is ON during the cheapest hours of the day."""

    _attr_icon = "mdi:cash-minus"

    def __init__(self, coordinator: ElectricityPriceCoordinator, entry: ConfigEntry, area: str) -> None:
        super().__init__(coordinator, entry, area, "cheapest_hours", "Cheapest Hours")

    @property
    def _num_hours(self) -> int:
        return self._entry.options.get(CONF_CHEAP_HOURS, DEFAULT_CHEAP_HOURS)

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

        attrs: dict = {
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
                "hours": [{"hour": e["hour"], "price": e["price"]} for e in window],
                "average_price": round(sum(e["price"] for e in window) / len(window), 4),
            }

        return attrs


class ExpensiveHoursBinarySensor(ElectricityBinarySensorBase):
    """Binary sensor that is ON during the most expensive hours of the day."""

    _attr_icon = "mdi:cash-plus"

    def __init__(self, coordinator: ElectricityPriceCoordinator, entry: ConfigEntry, area: str) -> None:
        super().__init__(coordinator, entry, area, "expensive_hours", "Expensive Hours")

    @property
    def _num_hours(self) -> int:
        return self._entry.options.get(CONF_EXPENSIVE_HOURS, DEFAULT_EXPENSIVE_HOURS)

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
