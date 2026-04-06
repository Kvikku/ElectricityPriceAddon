# Sensor Reference

Complete reference for all entities created by the **Nordic Electricity
Prices** integration.

Each configured price area creates its own set of entities. Entity
IDs use the **lowercase** area code as a suffix (e.g., `no1`, `se3`, `fi`).
Examples below use `no5` — replace with your area.

---

## Sensors

### Current Price

| | |
|---|---|
| **Entity** | `sensor.electricity_price_no5` |
| **Type** | Sensor |
| **Device class** | `monetary` |
| **Unit** | NOK/kWh |
| **Icon** | `mdi:flash` |
| **State** | Current hour's spot price (incl. or excl. VAT) |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `price_eur` | float | Current price in EUR/kWh |
| `hour` | int | Current hour (0–23) |
| `start` | ISO 8601 | Start time of current hour |
| `end` | ISO 8601 | End time of current hour |
| `raw_today` | list | All 24 hourly entries for today (for chart cards) |
| `raw_tomorrow` | list or null | All 24 hourly entries for tomorrow (if available) |

Each entry in `raw_today` / `raw_tomorrow`:

```json
{
  "start": "2026-03-20T00:00:00+01:00",
  "end": "2026-03-20T01:00:00+01:00",
  "price": 0.625,
  "hour": 0
}
```

---

### Next Hour Price

| | |
|---|---|
| **Entity** | `sensor.next_hour_price_no5` |
| **Type** | Sensor |
| **Device class** | `monetary` |
| **Unit** | NOK/kWh |
| **Icon** | `mdi:flash-outline` |
| **State** | Next hour's spot price |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `price_eur` | float | Next hour price in EUR/kWh |
| `hour` | int | Next hour (0–23) |
| `start` | ISO 8601 | Start time of next hour |

---

### Average Price

| | |
|---|---|
| **Entity** | `sensor.average_price_no5` |
| **Type** | Sensor |
| **Device class** | `monetary` |
| **Unit** | NOK/kWh |
| **Icon** | `mdi:chart-line` |
| **State** | Today's average spot price |

No additional attributes.

---

### Min Price

| | |
|---|---|
| **Entity** | `sensor.min_price_no5` |
| **Type** | Sensor |
| **Device class** | `monetary` |
| **Unit** | NOK/kWh |
| **Icon** | `mdi:arrow-down-bold` |
| **State** | Today's lowest hourly price |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `hour` | int | Hour with lowest price |
| `start` | ISO 8601 | Start time of cheapest hour |

---

### Max Price

| | |
|---|---|
| **Entity** | `sensor.max_price_no5` |
| **Type** | Sensor |
| **Device class** | `monetary` |
| **Unit** | NOK/kWh |
| **Icon** | `mdi:arrow-up-bold` |
| **State** | Today's highest hourly price |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `hour` | int | Hour with highest price |
| `start` | ISO 8601 | Start time of most expensive hour |

---

### Price Level

| | |
|---|---|
| **Entity** | `sensor.price_level_no5` |
| **Type** | Sensor |
| **Icon** | `mdi:speedometer` |
| **State** | Categorical price level |

Possible values: `very_cheap`, `cheap`, `normal`, `expensive`,
`very_expensive`, `unknown`.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `levels` | string | Comma-separated list of possible levels |

The level is calculated by ranking the current price against all of today's
prices by percentile:

| Percentile | Level |
|-----------|-------|
| < 10% | `very_cheap` |
| 10–35% | `cheap` |
| 35–65% | `normal` |
| 65–90% | `expensive` |
| ≥ 90% | `very_expensive` |

---

### Tomorrow Average Price

| | |
|---|---|
| **Entity** | `sensor.tomorrow_average_price_no5` |
| **Type** | Sensor |
| **Device class** | `monetary` |
| **Unit** | NOK/kWh |
| **Icon** | `mdi:chart-line` |
| **State** | Tomorrow's average spot price, or `unavailable` until prices are published |

> ℹ️ Tomorrow's prices are typically published at ~13:00 CET. The sensor
> returns `unavailable` before they are available.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `raw_tomorrow` | list | All 24 hourly entries for tomorrow (for chart cards) |

---

### Tomorrow Min Price

| | |
|---|---|
| **Entity** | `sensor.tomorrow_min_price_no5` |
| **Type** | Sensor |
| **Device class** | `monetary` |
| **Unit** | NOK/kWh |
| **Icon** | `mdi:arrow-down-bold` |
| **State** | Tomorrow's lowest hourly price, or `unavailable` until prices are published |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `hour` | int | Hour with tomorrow's lowest price |
| `start` | ISO 8601 | Start time of that hour |

---

### Tomorrow Max Price

| | |
|---|---|
| **Entity** | `sensor.tomorrow_max_price_no5` |
| **Type** | Sensor |
| **Device class** | `monetary` |
| **Unit** | NOK/kWh |
| **Icon** | `mdi:arrow-up-bold` |
| **State** | Tomorrow's highest hourly price, or `unavailable` until prices are published |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `hour` | int | Hour with tomorrow's highest price |
| `start` | ISO 8601 | Start time of that hour |

---

## Binary Sensors

### Cheapest Hours

| | |
|---|---|
| **Entity** | `binary_sensor.cheapest_hours_no5` |
| **Type** | Binary sensor |
| **Icon** | `mdi:cash-minus` |
| **State** | ON when the current hour is among the N cheapest today |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `num_hours` | int | Configured number of cheap hours |
| `cheapest_hours` | list | The N cheapest hours with price and time |
| `best_consecutive_window` | object or absent | Cheapest consecutive block of N hours |

`best_consecutive_window` structure:

```json
{
  "start": "2026-03-20T02:00:00+01:00",
  "end": "2026-03-20T06:00:00+01:00",
  "hours": [
    { "hour": 2, "price": 0.07 },
    { "hour": 3, "price": 0.06 },
    { "hour": 4, "price": 0.05 },
    { "hour": 5, "price": 0.06 }
  ],
  "average_price": 0.06
}
```

---

### Expensive Hours

| | |
|---|---|
| **Entity** | `binary_sensor.expensive_hours_no5` |
| **Type** | Binary sensor |
| **Icon** | `mdi:cash-plus` |
| **State** | ON when the current hour is among the N most expensive today |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `num_hours` | int | Configured number of expensive hours |
| `expensive_hours` | list | The N most expensive hours with price and time |

---

### Price Below Threshold

| | |
|---|---|
| **Entity** | `binary_sensor.price_below_threshold_no5` |
| **Type** | Binary sensor |
| **Icon** | `mdi:trending-down` |
| **State** | ON when the current price is below the configured threshold; `unavailable` when no threshold is set |

Configure the threshold in the integration's options (in NOK/kWh). Leave it
empty (or set to `None`) to disable the sensor.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `threshold` | float or null | The configured low price threshold (NOK/kWh) |
| `current_price` | float | Current hour's price (NOK/kWh) |

**Example automation — notify when price drops below 0.20 NOK/kWh:**

```yaml
automation:
  - alias: "Notify cheap electricity alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.price_below_threshold_no5
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "💚 Price below threshold!"
          message: "Current price: {{ states('sensor.electricity_price_no5') }} NOK/kWh"
```

---

### Price Above Threshold

| | |
|---|---|
| **Entity** | `binary_sensor.price_above_threshold_no5` |
| **Type** | Binary sensor |
| **Icon** | `mdi:trending-up` |
| **State** | ON when the current price is above the configured threshold; `unavailable` when no threshold is set |

Configure the threshold in the integration's options (in NOK/kWh). Leave it
empty (or set to `None`) to disable the sensor.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `threshold` | float or null | The configured high price threshold (NOK/kWh) |
| `current_price` | float | Current hour's price (NOK/kWh) |

---

## Events

### `norway_electricity_tomorrow_available`

Fired once per day when tomorrow's prices become available (typically around
13:00 CET).

**Payload:**

```json
{
  "area": "NO5",
  "date": "2026-03-21"
}
```

Use this event to trigger automations that plan the next day's energy usage.

---

## Supported Price Areas

| Code | Region |
|------|--------|
| **NO1** | Oslo / Øst-Norge |
| **NO2** | Kristiansand / Sør-Norge |
| **NO3** | Trondheim / Midt-Norge |
| **NO4** | Tromsø / Nord-Norge |
| **NO5** | Bergen / Vest-Norge |
| **SE1** | Luleå / Norra Sverige |
| **SE2** | Sundsvall / Mellersta Nord Sverige |
| **SE3** | Stockholm / Mellersta Syd Sverige |
| **SE4** | Malmö / Södra Sverige |
| **DK1** | Jylland / Fyn (Vest-Danmark) |
| **DK2** | Sjælland (Øst-Danmark) |
| **FI** | Finland |

