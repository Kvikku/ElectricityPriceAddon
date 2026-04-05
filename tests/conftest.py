"""Conftest: mock homeassistant modules so tests run without HA installed."""

import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock


# Provide a real parse_datetime so the coordinator can parse ISO timestamps
def _parse_datetime(dt_string: str) -> datetime | None:
    try:
        return datetime.fromisoformat(dt_string)
    except (ValueError, TypeError):
        return None


def _now() -> datetime:
    return datetime.now(tz=timezone(timedelta(hours=1)))


# Provide a real DataUpdateCoordinator stub that can be subclassed
class _FakeDataUpdateCoordinator:
    """Stub so ElectricityPriceCoordinator can inherit properly."""

    def __init__(self, *args, **kwargs):
        pass

    def __init_subclass__(cls, **kwargs):
        pass

    def __class_getitem__(cls, item):
        return cls


# Build the mock module tree with proper parent→child wiring.
# When Python does `from homeassistant.util import dt`, it accesses
# sys.modules["homeassistant.util"].dt — so parent.child must point
# to the same object as sys.modules["parent.child"].

dt_mock = MagicMock()
dt_mock.parse_datetime = _parse_datetime
dt_mock.now = _now

update_coordinator_mock = MagicMock()
update_coordinator_mock.DataUpdateCoordinator = _FakeDataUpdateCoordinator
update_coordinator_mock.UpdateFailed = Exception


class _FakeCoordinatorEntity:
    """Stub so sensor/binary_sensor bases can inherit CoordinatorEntity[T]."""

    def __init__(self, coordinator=None, *args, **kwargs):
        self.coordinator = coordinator

    def __init_subclass__(cls, **kwargs):
        pass

    def __class_getitem__(cls, item):
        return cls


update_coordinator_mock.CoordinatorEntity = _FakeCoordinatorEntity

aiohttp_client_mock = MagicMock()
device_registry_mock = MagicMock()
device_registry_mock.DeviceEntryType = MagicMock()
device_registry_mock.DeviceInfo = dict  # DeviceInfo is a TypedDict, dict works

helpers_mock = MagicMock()
helpers_mock.update_coordinator = update_coordinator_mock
helpers_mock.entity_platform = MagicMock()
helpers_mock.aiohttp_client = aiohttp_client_mock
helpers_mock.device_registry = device_registry_mock

util_mock = MagicMock()
util_mock.dt = dt_mock

ha_mock = MagicMock()
ha_mock.core = MagicMock()
ha_mock.core.callback = lambda f: f  # @callback is a no-op decorator
ha_mock.config_entries = MagicMock()
ha_mock.helpers = helpers_mock
ha_mock.util = util_mock
ha_mock.components = MagicMock()


# Sensor / BinarySensor stubs — must be real classes so multi-inheritance works
class _FakeSensorEntity:
    """Stub for SensorEntity."""

    pass


class _FakeSensorDeviceClass:
    MONETARY = "monetary"


class _FakeSensorStateClass:
    MEASUREMENT = "measurement"


class _FakeBinarySensorEntity:
    """Stub for BinarySensorEntity."""

    pass


sensor_mock = MagicMock()
sensor_mock.SensorEntity = _FakeSensorEntity
sensor_mock.SensorDeviceClass = _FakeSensorDeviceClass
sensor_mock.SensorStateClass = _FakeSensorStateClass

binary_sensor_mock = MagicMock()
binary_sensor_mock.BinarySensorEntity = _FakeBinarySensorEntity

_modules = {
    "homeassistant": ha_mock,
    "homeassistant.core": ha_mock.core,
    "homeassistant.config_entries": ha_mock.config_entries,
    "homeassistant.helpers": helpers_mock,
    "homeassistant.helpers.update_coordinator": update_coordinator_mock,
    "homeassistant.helpers.entity_platform": helpers_mock.entity_platform,
    "homeassistant.helpers.aiohttp_client": aiohttp_client_mock,
    "homeassistant.helpers.device_registry": device_registry_mock,
    "homeassistant.util": util_mock,
    "homeassistant.util.dt": dt_mock,
    "homeassistant.components": ha_mock.components,
    "homeassistant.components.sensor": sensor_mock,
    "homeassistant.components.binary_sensor": binary_sensor_mock,
    "voluptuous": MagicMock(),
}

for mod_name, mod in _modules.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mod
