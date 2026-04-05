# Architecture

This document describes the internal architecture and data flow of the
**Norway Electricity Prices** Home Assistant integration.

## High-Level Overview

```
hvakosterstrommen.no API
        │
        ▼
┌──────────────────────────┐
│  ElectricityPriceCoord-  │  Fetches & parses JSON every 30 min
│  inator (coordinator.py) │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  ElectricityPriceData    │  Structured model with helper methods
│  (coordinator.py)        │
└────┬───────────────┬─────┘
     │               │
     ▼               ▼
┌──────────┐  ┌──────────────┐
│ Sensors  │  │ Binary       │
│ (sensor  │  │ Sensors      │
│  .py)    │  │ (binary_     │
│          │  │  sensor.py)  │
└──────────┘  └──────────────┘
     │               │
     ▼               ▼
  Home Assistant Entity Registry
```

## Components

### Coordinator (`coordinator.py`)

The `ElectricityPriceCoordinator` extends Home Assistant's
`DataUpdateCoordinator` and is responsible for:

- **Fetching** hourly electricity prices from the
  [hvakosterstrommen.no](https://www.hvakosterstrommen.no/) REST API.
- **Polling** every **30 minutes** (`UPDATE_INTERVAL`).
- **Fetching tomorrow's prices** when they become available (typically after
  13:00 CET) and firing a `norway_electricity_tomorrow_available` event the
  first time they appear each day.
- **Parsing** raw API JSON into `ElectricityPriceData`, applying VAT if
  configured.

#### API Endpoint

```
https://www.hvakosterstrommen.no/api/v1/prices/{YYYY}/{MM}-{DD}_{AREA}.json
```

- No API key required.
- Returns 24 hourly entries per day with `NOK_per_kWh`, `EUR_per_kWh`,
  `time_start`, and `time_end`.

### Data Model (`ElectricityPriceData`)

A plain Python class that stores today's and (optionally) tomorrow's parsed
price entries. Each entry is a dict:

```python
{
    "start": datetime,   # Hour start (timezone-aware)
    "end": datetime,     # Hour end
    "price": float,      # NOK/kWh (with or without VAT)
    "price_eur": float,  # EUR/kWh
    "hour": int,         # 0–23
}
```

Key methods:

| Method | Description |
|--------|-------------|
| `current_price(now)` | Entry for the current hour |
| `next_hour_price(now)` | Entry for the next hour |
| `average_price()` | Mean price for today |
| `min_entry()` / `max_entry()` | Cheapest / most expensive entry |
| `price_level(now)` | Categorical level based on percentile ranking |
| `cheapest_hours(n)` | N cheapest hours today |
| `most_expensive_hours(n)` | N most expensive hours today |
| `best_consecutive_window(n)` | Cheapest consecutive block of N hours |

### Sensor Platform (`sensor.py`)

Six sensor entities per configured price area:

| Class | Key | Description |
|-------|-----|-------------|
| `CurrentPriceSensor` | `current_price` | Current hour NOK/kWh |
| `NextHourPriceSensor` | `next_hour_price` | Next hour NOK/kWh |
| `AveragePriceSensor` | `average_price` | Today's average |
| `MinPriceSensor` | `min_price` | Today's lowest price |
| `MaxPriceSensor` | `max_price` | Today's highest price |
| `PriceLevelSensor` | `price_level` | Categorical level string |

All monetary sensors use `SensorDeviceClass.MONETARY` and report in
`NOK/kWh`.

### Binary Sensor Platform (`binary_sensor.py`)

Two binary sensors per configured price area:

| Class | Key | Description |
|-------|-----|-------------|
| `CheapestHoursBinarySensor` | `cheapest_hours` | ON during the N cheapest hours |
| `ExpensiveHoursBinarySensor` | `expensive_hours` | ON during the N most expensive hours |

The cheapest-hours sensor also exposes a `best_consecutive_window` attribute
showing the optimal charging window.

### Config Flow (`config_flow.py`)

- **Setup step**: User selects a price area (NO1–NO5). Duplicate areas are
  rejected via `async_set_unique_id`.
- **Options flow**: Users can adjust VAT toggle, number of cheap hours, and
  number of expensive hours (1–12). Changes trigger a full integration
  reload.

## Price Level Algorithm

The price level is determined by percentile ranking of the current price
against all of today's prices:

| Percentile | Level |
|-----------|-------|
| < 10% | `very_cheap` |
| 10–35% | `cheap` |
| 35–65% | `normal` |
| 65–90% | `expensive` |
| ≥ 90% | `very_expensive` |

## Event System

| Event | Payload | When |
|-------|---------|------|
| `norway_electricity_tomorrow_available` | `{"area": "NO5", "date": "2026-03-21"}` | First time tomorrow's prices are fetched each day |

## Update Lifecycle

1. HA calls `async_config_entry_first_refresh()` on integration setup.
2. Every 30 minutes, `_async_update_data()` fires:
   - Fetches today's prices (required — raises `UpdateFailed` on failure).
   - Attempts to fetch tomorrow's prices (optional — returns `None` if
     unavailable).
   - Fires the "tomorrow available" event if new.
3. All sensor entities inherit from `CoordinatorEntity` and automatically
   update when the coordinator receives new data.
4. If a user changes options, `_async_update_listener` triggers a full
   reload of the integration.
