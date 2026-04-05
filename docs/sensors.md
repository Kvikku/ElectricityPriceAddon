# Sensor Reference

Complete reference for all entities created by the **Norway Electricity
Prices** integration.

Each configured price area (NO1–NO5) creates its own set of entities. Entity
IDs include the area code as a suffix (e.g., `sensor.electricity_price_no5`).

---

## Sensors

### Current Price

| | |
|---|---|
| **Entity** | `sensor.electricity_price_{area}` |
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
| **Entity** | `sensor.next_hour_price_{area}` |
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
| **Entity** | `sensor.average_price_{area}` |
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
| **Entity** | `sensor.min_price_{area}` |
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
| **Entity** | `sensor.max_price_{area}` |
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
| **Entity** | `sensor.price_level_{area}` |
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

## Binary Sensors

### Cheapest Hours

| | |
|---|---|
| **Entity** | `binary_sensor.cheapest_hours_{area}` |
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
| **Entity** | `binary_sensor.expensive_hours_{area}` |
| **Type** | Binary sensor |
| **Icon** | `mdi:cash-plus` |
| **State** | ON when the current hour is among the N most expensive today |

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `num_hours` | int | Configured number of expensive hours |
| `expensive_hours` | list | The N most expensive hours with price and time |

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
