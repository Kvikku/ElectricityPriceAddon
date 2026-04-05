# Copilot Instructions — Norway Electricity Prices

## Project Overview

This is a **Home Assistant custom integration** (not an add-on) that fetches
real-time Norwegian electricity spot prices from
[hvakosterstrommen.no](https://www.hvakosterstrommen.no/) and exposes them as
HA sensors and binary sensors.

- **Domain**: `norway_electricity`
- **Integration type**: Hub (`cloud_polling`)
- **Language**: Python 3.12+
- **HA minimum version**: 2024.1.0

## Repository Layout

```
custom_components/norway_electricity/
├── __init__.py          # Integration setup / unload
├── const.py             # Constants (domain, API URL, config keys, defaults)
├── coordinator.py       # DataUpdateCoordinator + ElectricityPriceData model
├── config_flow.py       # Config flow + options flow (UI setup)
├── sensor.py            # Sensor entities (current, next hour, avg, min, max, level)
├── binary_sensor.py     # Binary sensors (cheapest hours, expensive hours)
├── manifest.json        # HA integration manifest
├── strings.json         # English UI strings
└── translations/        # Localisations (en.json, nb.json)

tests/
├── conftest.py          # HA mock setup (so tests run without full HA)
└── test_coordinator.py  # Unit tests for ElectricityPriceData and parsing
```

## Coding Conventions

- Follow **Home Assistant integration development** guidelines.
- Use `from __future__ import annotations` in every Python module.
- Type-hint all function signatures.
- Use `async`/`await` for all I/O-bound operations.
- Prefer `homeassistant.util.dt` for datetime handling.
- Keep `aiohttp` sessions short-lived (create + close per request in the
  coordinator).
- Constants live in `const.py` — never hard-code domain names, config keys,
  or default values elsewhere.
- Use `_LOGGER = logging.getLogger(__name__)` for logging.

## Linting & Formatting

- **Linter/formatter**: [Ruff](https://docs.astral.sh/ruff/)
- Lint: `ruff check .`
- Format check: `ruff format --check .`
- Auto-fix: `ruff check --fix .` / `ruff format .`

## Testing

- **Framework**: pytest
- Run: `pytest tests/ -v`
- Config: `pytest.ini` (test paths = `tests/`, python path = `.`)
- Tests mock the entire `homeassistant` package via `conftest.py` so they
  run without Home Assistant installed.
- When adding new logic to `coordinator.py`, add corresponding tests in
  `tests/test_coordinator.py`.

## Key Patterns

### Data Flow

1. `ElectricityPriceCoordinator` fetches JSON from the hvakosterstrommen.no
   API every 30 minutes.
2. Raw JSON is parsed into `ElectricityPriceData` (a structured container
   with helper methods like `current_price()`, `price_level()`,
   `cheapest_hours()`, etc.).
3. Sensor and binary-sensor entities read from the coordinator's `data`
   property and expose values + attributes to HA.

### Config & Options

- **Config flow** (`config_flow.py`): user selects a price area (NO1–NO5).
  Each area creates a unique config entry (duplicate areas are rejected).
- **Options flow**: users can toggle VAT, and set the number of cheap /
  expensive hours (1–12).
- Changing options triggers `async_reload` of the integration.

### Events

- `norway_electricity_tomorrow_available` is fired once per day when
  tomorrow's prices become available (typically around 13:00 CET).

## Adding New Features

1. If adding a new sensor, create a class in `sensor.py` or
   `binary_sensor.py` inheriting from the appropriate base.
2. If adding new configuration options, update `config_flow.py`,
   `const.py`, `strings.json`, and the translation files.
3. If modifying data fetching or parsing, update `coordinator.py` and add
   tests.
4. Always update `README.md` and relevant docs when adding user-facing
   features.

## CI / CD

- **HACS validation** runs on push to `main` and on pull requests
  (`.github/workflows/hacs-validate.yaml`).
- **Release workflow** runs on version tags (`v*`) — validates, tests, and
  creates a GitHub release (`.github/workflows/release.yaml`).
