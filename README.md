# Norway Electricity Prices — Home Assistant Integration

[![HACS Validation](https://github.com/Kvikku/ElectricityPriceAddon/actions/workflows/hacs-validate.yaml/badge.svg)](https://github.com/Kvikku/ElectricityPriceAddon/actions/workflows/hacs-validate.yaml)
[![GitHub Release](https://img.shields.io/github/v/release/Kvikku/ElectricityPriceAddon?sort=semver)](https://github.com/Kvikku/ElectricityPriceAddon/releases)
[![License: MIT](https://img.shields.io/github/license/Kvikku/ElectricityPriceAddon)](LICENSE)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange)](https://hacs.xyz/)

A custom Home Assistant integration that fetches real-time Norwegian
electricity spot prices from
[hvakosterstrommen.no](https://www.hvakosterstrommen.no/) and provides
sensors, price level indicators, and smart automation helpers for each of the
five Norwegian price areas (NO1–NO5).

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Sensors & Entities](#sensors--entities)
- [Lovelace Examples](#lovelace-examples)
- [Automation Examples](#automation-examples)
- [Data Source](#data-source)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Feature | Description |
|---------|-------------|
| ⚡ **Current hour price** | Real-time NOK/kWh with EUR price as attribute |
| ⏭️ **Next hour price** | Plan ahead with upcoming hour's price |
| 📊 **Daily statistics** | Average, min, and max prices with timestamps |
| 🏷️ **Price level** | Categorical indicator: `very_cheap` → `very_expensive` |
| 💚 **Cheapest hours** | Binary sensor ON during the N cheapest hours today |
| 🔴 **Expensive hours** | Binary sensor ON during the N most expensive hours |
| 🔋 **Best charging window** | Finds the cheapest consecutive block of N hours (ideal for EV charging) |
| 📅 **Tomorrow's prices** | Fetched automatically once available (~13:00 CET), with HA event fired |
| 🧾 **VAT toggle** | Include or exclude 25% MVA in integration options |
| 🗺️ **Multi-area** | Add the integration multiple times for different price areas |
| ✅ **HACS compatible** | Easy install and updates through HACS |

---

## Installation

### HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Go to **Integrations** → **⋮ menu** → **Custom repositories**.
3. Add this repository URL:
   ```
   https://github.com/Kvikku/ElectricityPriceAddon
   ```
4. Select category **Integration** and click **Add**.
5. Find **Norway Electricity Prices** in the integration list and click
   **Install**.
6. **Restart** Home Assistant.

### Manual Installation

1. Download or clone this repository.
2. Copy the `custom_components/norway_electricity/` folder into your Home
   Assistant `config/custom_components/` directory.
3. **Restart** Home Assistant.

---

## Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Norway Electricity Prices**.
3. Select your price area:

   | Code | Region |
   |------|--------|
   | **NO1** | Oslo / Øst-Norge |
   | **NO2** | Kristiansand / Sør-Norge |
   | **NO3** | Trondheim / Midt-Norge |
   | **NO4** | Tromsø / Nord-Norge |
   | **NO5** | Bergen / Vest-Norge |

4. Done! Sensors will appear automatically.

> 💡 **Tip:** Add the integration multiple times to monitor different price
> areas simultaneously.

### Options

After adding the integration, click **Configure** to adjust:

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| Include VAT (25%) | ✅ On | — | Add 25% MVA to spot prices |
| Cheapest hours | 6 | 1–12 | Number of hours considered "cheap" |
| Most expensive hours | 6 | 1–12 | Number of hours considered "expensive" |

---

## Sensors & Entities

Each price area creates **8 entities**:

| Entity | Type | State | Key Attributes |
|--------|------|-------|----------------|
| `sensor.electricity_price_{area}` | Sensor | Current NOK/kWh | `price_eur`, `hour`, `raw_today`, `raw_tomorrow` |
| `sensor.next_hour_price_{area}` | Sensor | Next hour NOK/kWh | `price_eur`, `hour` |
| `sensor.average_price_{area}` | Sensor | Today's average | — |
| `sensor.min_price_{area}` | Sensor | Today's lowest | `hour` of cheapest |
| `sensor.max_price_{area}` | Sensor | Today's highest | `hour` of most expensive |
| `sensor.price_level_{area}` | Sensor | Category string | — |
| `binary_sensor.cheapest_hours_{area}` | Binary | ON if cheap now | `cheapest_hours`, `best_consecutive_window` |
| `binary_sensor.expensive_hours_{area}` | Binary | ON if expensive now | `expensive_hours` |

📖 **Full details:** [Sensor Reference](docs/sensors.md)

---

## Lovelace Examples

### Hourly Price Bar Chart

Requires [apexcharts-card](https://github.com/RomRider/apexcharts-card)
(install via HACS):

```yaml
type: custom:apexcharts-card
header:
  title: Electricity Prices Today
  show: true
graph_span: 24h
span:
  start: day
series:
  - entity: sensor.electricity_price_no5
    data_generator: |
      const data = entity.attributes.raw_today || [];
      return data.map(e => [new Date(e.start).getTime(), e.price]);
    type: column
    name: NOK/kWh
    color: "#4CAF50"
```

### Today + Tomorrow (48h View)

```yaml
type: custom:apexcharts-card
header:
  title: Electricity Prices (48h)
  show: true
graph_span: 48h
span:
  start: day
series:
  - entity: sensor.electricity_price_no5
    data_generator: |
      const today = entity.attributes.raw_today || [];
      const tomorrow = entity.attributes.raw_tomorrow || [];
      const all = [...today, ...tomorrow];
      return all.map(e => [new Date(e.start).getTime(), e.price]);
    type: column
    name: NOK/kWh
    color: "#2196F3"
```

📖 **More examples:** [Automation & Lovelace Examples](docs/automations.md)

---

## Automation Examples

### Notify When Cheap Electricity Starts

```yaml
automation:
  - alias: "Notify cheap electricity"
    trigger:
      - platform: state
        entity_id: binary_sensor.cheapest_hours_no5
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "⚡ Cheap electricity now!"
          message: >
            Current price: {{ states('sensor.electricity_price_no5') }} NOK/kWh.
            Good time to charge the car or run the dishwasher!
```

### Pause EV Charging During Expensive Hours

```yaml
automation:
  - alias: "Pause EV charging — expensive hours"
    trigger:
      - platform: state
        entity_id: binary_sensor.expensive_hours_no5
        to: "on"
    action:
      - service: switch.turn_off
        entity_id: switch.ev_charger
  - alias: "Resume EV charging — cheap hours"
    trigger:
      - platform: state
        entity_id: binary_sensor.expensive_hours_no5
        to: "off"
    action:
      - service: switch.turn_on
        entity_id: switch.ev_charger
```

📖 **More automations:** [Automation Examples](docs/automations.md) — includes
dishwasher scheduling, water heater control, daily summaries, template
sensors, and more.

---

## Data Source

All data comes from
[hvakosterstrommen.no](https://www.hvakosterstrommen.no/) — a free, open API
provided by [Hva koster strømmen](https://www.hvakosterstrommen.no/).

- **No API key required**
- **Update interval:** every 30 minutes
- **Tomorrow's prices:** typically available after 13:00 CET

---

## Documentation

| Document | Description |
|----------|-------------|
| [Sensor Reference](docs/sensors.md) | Detailed info on every entity, attribute, and event |
| [Automation Examples](docs/automations.md) | Ready-to-use automations, Lovelace cards, and template sensors |
| [Architecture](docs/architecture.md) | Internal data flow, components, and design decisions |
| [Development Guide](docs/development.md) | Setup, testing, and code style for contributors |
| [Contributing](CONTRIBUTING.md) | How to report bugs, suggest features, and submit PRs |

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for
guidelines.

```bash
# Quick start for developers
git clone https://github.com/Kvikku/ElectricityPriceAddon.git
cd ElectricityPriceAddon
python -m venv .venv && source .venv/bin/activate
pip install pytest aiohttp ruff
pytest tests/ -v
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No data after setup | Check HA logs (Settings → System → Logs). The API may be temporarily unavailable. |
| Prices show 0.0 | Verify your price area is correct. Check if the API has data for today. |
| Tomorrow's prices missing | Normal before ~13:00 CET. They appear automatically when the API publishes them. |
| Sensors show "unavailable" | Restart HA. If persistent, remove and re-add the integration. |
| HACS can't find the integration | Ensure you added the repository URL as a custom repository with category "Integration". |

---

## License

[MIT](LICENSE)
