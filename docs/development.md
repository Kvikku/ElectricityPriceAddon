# Development Guide

Guide for contributing to the **Norway Electricity Prices** Home Assistant
integration.

## Prerequisites

- Python 3.12 or later
- Git
- A text editor or IDE with Python support

## Getting Started

```bash
# Clone the repository
git clone https://github.com/Kvikku/ElectricityPriceAddon.git
cd ElectricityPriceAddon

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
# .venv\Scripts\activate   # Windows

# Install development dependencies
pip install pytest aiohttp ruff
```

## Project Structure

```
ElectricityPriceAddon/
├── custom_components/
│   └── norway_electricity/     # The HA integration
│       ├── __init__.py          # Setup & teardown
│       ├── const.py             # Constants & defaults
│       ├── coordinator.py       # API fetching & data model
│       ├── config_flow.py       # UI configuration
│       ├── sensor.py            # Sensor entities
│       ├── binary_sensor.py     # Binary sensor entities
│       ├── manifest.json        # HA integration manifest
│       ├── strings.json         # English UI strings
│       └── translations/        # Localised strings
│           ├── en.json
│           └── nb.json
├── tests/
│   ├── conftest.py              # HA mocks for standalone testing
│   └── test_coordinator.py      # Unit tests
├── .github/
│   └── workflows/
│       ├── hacs-validate.yaml   # HACS validation on PR/push
│       └── release.yaml         # Release on version tag
├── hacs.json                    # HACS metadata
├── pytest.ini                   # Pytest configuration
└── README.md
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run a specific test class
pytest tests/test_coordinator.py::TestCurrentPrice -v

# Run a single test
pytest tests/test_coordinator.py::TestCurrentPrice::test_returns_correct_hour -v
```

Tests mock the entire `homeassistant` package (see `tests/conftest.py`), so
you do **not** need Home Assistant installed to run them.

## Linting & Formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and
formatting.

```bash
# Check for lint issues
ruff check .

# Auto-fix lint issues
ruff check --fix .

# Check formatting
ruff format --check .

# Auto-format
ruff format .
```

## Making Changes

### Adding a New Sensor

1. Add a new class in `sensor.py` or `binary_sensor.py`, extending the
   appropriate base class.
2. Register it in the `async_setup_entry` function of the same file.
3. If the sensor needs new data, add a method to `ElectricityPriceData` in
   `coordinator.py`.
4. Add tests for any new data methods in `tests/test_coordinator.py`.
5. Update `docs/sensors.md` and `README.md`.

### Adding a Configuration Option

1. Add the config key and default value to `const.py`.
2. Add the option to the options flow schema in `config_flow.py`.
3. Add UI strings to `strings.json` and all files in `translations/`.
4. Use the option in the relevant sensor/coordinator code.
5. Update the README options table.

### Adding a New Translation

1. Copy `translations/en.json` to `translations/{lang_code}.json`.
2. Translate all string values.
3. The file name must be a valid
   [BCP 47 language tag](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry)
   (e.g., `nb.json`, `sv.json`, `da.json`).

### Modifying the API Client

The coordinator (`coordinator.py`) handles all API communication:

- `_fetch_prices(date)` — HTTP GET to the hvakosterstrommen.no API.
- `_parse_prices(raw)` — converts JSON into internal dicts with VAT
  applied.

When changing these methods, always add or update tests in
`test_coordinator.py`.

## Testing Locally with Home Assistant

For end-to-end testing with a real HA instance:

1. Copy (or symlink) `custom_components/norway_electricity/` into your HA
   `config/custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration via **Settings → Devices & Services → Add
   Integration**.
4. Check the HA logs for any errors:
   ```
   Settings → System → Logs
   ```

Alternatively, use a
[HA development container](https://developers.home-assistant.io/docs/development_environment):

```bash
# Using the HA devcontainer
# Mount your integration folder and start HA
```

## Continuous Integration

### HACS Validation (on every PR / push to main)

The `.github/workflows/hacs-validate.yaml` workflow runs the official
[HACS action](https://github.com/hacs/action) to ensure the integration
meets HACS requirements.

### Release (on version tags)

The `.github/workflows/release.yaml` workflow:

1. Validates with HACS and hassfest.
2. Runs tests with pytest.
3. Creates a GitHub Release with auto-generated release notes.

To create a release:

```bash
git tag v1.1.0
git push origin v1.1.0
```

## Code Style Guidelines

- Use `from __future__ import annotations` at the top of every module.
- Type-hint all function parameters and return values.
- Use `async`/`await` for I/O operations.
- Keep constants in `const.py` — avoid magic strings/numbers.
- Follow the
  [Home Assistant integration development guidelines](https://developers.home-assistant.io/docs/creating_integration_manifest).
- Use `_LOGGER` (module-level `logging.getLogger(__name__)`) for all log
  output.
- Docstrings on all public classes and methods.

## Troubleshooting Development Issues

### Tests fail with `ModuleNotFoundError: homeassistant`

This is expected if you don't have HA installed. The `conftest.py` mocks
should handle this — make sure you're running tests from the repository root
and that `pytest.ini` is present.

### `ruff` not found

Install it: `pip install ruff`

### HACS validation fails

Common causes:

- Missing or malformed `manifest.json` fields.
- `hacs.json` missing or incorrect `name` / `homeassistant` version.
- Missing `README.md` (required when `render_readme: true`).
