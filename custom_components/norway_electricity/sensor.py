"""Sensor platform for Norway Electricity Prices."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_AREA, CURRENCY_NOK, DOMAIN, PRICE_AREAS, serialize_entry
from .coordinator import ElectricityPriceCoordinator, ElectricityPriceData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator: ElectricityPriceCoordinator = hass.data[DOMAIN][entry.entry_id]
    area = entry.data[CONF_AREA]

    sensors = [
        CurrentPriceSensor(coordinator, area),
        NextHourPriceSensor(coordinator, area),
        AveragePriceSensor(coordinator, area),
        MinPriceSensor(coordinator, area),
        MaxPriceSensor(coordinator, area),
        PriceLevelSensor(coordinator, area),
        TomorrowAveragePriceSensor(coordinator, area),
        TomorrowMinPriceSensor(coordinator, area),
        TomorrowMaxPriceSensor(coordinator, area),
    ]

    async_add_entities(sensors, update_before_add=True)


class ElectricityPriceSensorBase(CoordinatorEntity[ElectricityPriceCoordinator], SensorEntity):
    """Base class for electricity price sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ElectricityPriceCoordinator,
        area: str,
        key: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._area = area
        self._attr_unique_id = f"{DOMAIN}_{area}_{key}"
        self._attr_translation_key = key
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

    def _raw_today_attr(self) -> list[dict]:
        """Serializable list of today's prices for graph cards."""
        if not self.data:
            return []
        return [serialize_entry(e) for e in self.data.today]

    def _raw_tomorrow_attr(self) -> list[dict] | None:
        """Serializable list of tomorrow's prices."""
        if not self.data or not self.data.tomorrow:
            return None
        return [serialize_entry(e) for e in self.data.tomorrow]


class CurrentPriceSensor(ElectricityPriceSensorBase):
    """Sensor showing the current hour electricity price."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CURRENCY_NOK
    _attr_icon = "mdi:flash"

    def __init__(self, coordinator: ElectricityPriceCoordinator, area: str) -> None:
        super().__init__(coordinator, area, "current_price", "Electricity Price")

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        if not self.data:
            return None
        entry = self.data.current_price()
        return entry["price"] if entry else None

    @property
    def extra_state_attributes(self) -> dict:
        attrs: dict = {}
        if self.data:
            entry = self.data.current_price()
            if entry:
                attrs["price_eur"] = entry["price_eur"]
                attrs["hour"] = entry["hour"]
                attrs["start"] = entry["start"].isoformat()
                attrs["end"] = entry["end"].isoformat()
            attrs["raw_today"] = self._raw_today_attr()
            attrs["raw_tomorrow"] = self._raw_tomorrow_attr()
        return attrs


class NextHourPriceSensor(ElectricityPriceSensorBase):
    """Sensor showing the next hour electricity price."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CURRENCY_NOK
    _attr_icon = "mdi:flash-outline"

    def __init__(self, coordinator: ElectricityPriceCoordinator, area: str) -> None:
        super().__init__(coordinator, area, "next_hour_price", "Next Hour Price")

    @property
    def native_value(self) -> float | None:
        if not self.data:
            return None
        entry = self.data.next_hour_price()
        return entry["price"] if entry else None

    @property
    def extra_state_attributes(self) -> dict:
        if not self.data:
            return {}
        entry = self.data.next_hour_price()
        if not entry:
            return {}
        return {
            "price_eur": entry["price_eur"],
            "hour": entry["hour"],
            "start": entry["start"].isoformat(),
        }


class AveragePriceSensor(ElectricityPriceSensorBase):
    """Sensor showing today's average electricity price."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CURRENCY_NOK
    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator: ElectricityPriceCoordinator, area: str) -> None:
        super().__init__(coordinator, area, "average_price", "Average Price")

    @property
    def native_value(self) -> float | None:
        if not self.data:
            return None
        return round(self.data.average_price(), 4)


class MinPriceSensor(ElectricityPriceSensorBase):
    """Sensor showing today's lowest electricity price."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CURRENCY_NOK
    _attr_icon = "mdi:arrow-down-bold"

    def __init__(self, coordinator: ElectricityPriceCoordinator, area: str) -> None:
        super().__init__(coordinator, area, "min_price", "Min Price")

    @property
    def native_value(self) -> float | None:
        if not self.data:
            return None
        entry = self.data.min_entry()
        return entry["price"] if entry else None

    @property
    def extra_state_attributes(self) -> dict:
        if not self.data:
            return {}
        entry = self.data.min_entry()
        if not entry:
            return {}
        return {
            "hour": entry["hour"],
            "start": entry["start"].isoformat(),
        }


class MaxPriceSensor(ElectricityPriceSensorBase):
    """Sensor showing today's highest electricity price."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CURRENCY_NOK
    _attr_icon = "mdi:arrow-up-bold"

    def __init__(self, coordinator: ElectricityPriceCoordinator, area: str) -> None:
        super().__init__(coordinator, area, "max_price", "Max Price")

    @property
    def native_value(self) -> float | None:
        if not self.data:
            return None
        entry = self.data.max_entry()
        return entry["price"] if entry else None

    @property
    def extra_state_attributes(self) -> dict:
        if not self.data:
            return {}
        entry = self.data.max_entry()
        if not entry:
            return {}
        return {
            "hour": entry["hour"],
            "start": entry["start"].isoformat(),
        }


class PriceLevelSensor(ElectricityPriceSensorBase):
    """Sensor showing the current hour's price level category."""

    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: ElectricityPriceCoordinator, area: str) -> None:
        super().__init__(coordinator, area, "price_level", "Price Level")

    @property
    def native_value(self) -> str | None:
        if not self.data:
            return None
        return self.data.price_level()

    @property
    def extra_state_attributes(self) -> dict:
        if not self.data:
            return {}
        return {
            "levels": "very_cheap, cheap, normal, expensive, very_expensive",
        }


class TomorrowAveragePriceSensor(ElectricityPriceSensorBase):
    """Sensor showing tomorrow's average electricity price."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CURRENCY_NOK
    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator: ElectricityPriceCoordinator, area: str) -> None:
        super().__init__(coordinator, area, "tomorrow_average_price", "Tomorrow Average Price")

    @property
    def native_value(self) -> float | None:
        if not self.data or not self.data.tomorrow:
            return None
        return round(self.data.average_price(self.data.tomorrow), 4)

    @property
    def extra_state_attributes(self) -> dict:
        raw = self._raw_tomorrow_attr()
        if raw is None:
            return {}
        return {"raw_tomorrow": raw}


class TomorrowMinPriceSensor(ElectricityPriceSensorBase):
    """Sensor showing tomorrow's lowest electricity price."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CURRENCY_NOK
    _attr_icon = "mdi:arrow-down-bold"

    def __init__(self, coordinator: ElectricityPriceCoordinator, area: str) -> None:
        super().__init__(coordinator, area, "tomorrow_min_price", "Tomorrow Min Price")

    @property
    def native_value(self) -> float | None:
        if not self.data or not self.data.tomorrow:
            return None
        entry = self.data.min_entry(self.data.tomorrow)
        return entry["price"] if entry else None

    @property
    def extra_state_attributes(self) -> dict:
        if not self.data or not self.data.tomorrow:
            return {}
        entry = self.data.min_entry(self.data.tomorrow)
        if not entry:
            return {}
        return {
            "hour": entry["hour"],
            "start": entry["start"].isoformat(),
        }


class TomorrowMaxPriceSensor(ElectricityPriceSensorBase):
    """Sensor showing tomorrow's highest electricity price."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CURRENCY_NOK
    _attr_icon = "mdi:arrow-up-bold"

    def __init__(self, coordinator: ElectricityPriceCoordinator, area: str) -> None:
        super().__init__(coordinator, area, "tomorrow_max_price", "Tomorrow Max Price")

    @property
    def native_value(self) -> float | None:
        if not self.data or not self.data.tomorrow:
            return None
        entry = self.data.max_entry(self.data.tomorrow)
        return entry["price"] if entry else None

    @property
    def extra_state_attributes(self) -> dict:
        if not self.data or not self.data.tomorrow:
            return {}
        entry = self.data.max_entry(self.data.tomorrow)
        if not entry:
            return {}
        return {
            "hour": entry["hour"],
            "start": entry["start"].isoformat(),
        }
