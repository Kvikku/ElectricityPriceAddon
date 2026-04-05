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
update_coordinator_mock.CoordinatorEntity = MagicMock

aiohttp_client_mock = MagicMock()
device_registry_mock = MagicMock()

helpers_mock = MagicMock()
helpers_mock.update_coordinator = update_coordinator_mock
helpers_mock.entity_platform = MagicMock()
helpers_mock.aiohttp_client = aiohttp_client_mock
helpers_mock.device_registry = device_registry_mock

util_mock = MagicMock()
util_mock.dt = dt_mock

ha_mock = MagicMock()
ha_mock.core = MagicMock()
ha_mock.config_entries = MagicMock()
ha_mock.helpers = helpers_mock
ha_mock.util = util_mock
ha_mock.components = MagicMock()

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
    "homeassistant.components.sensor": MagicMock(),
    "homeassistant.components.binary_sensor": MagicMock(),
    "voluptuous": MagicMock(),
}

for mod_name, mod in _modules.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mod
