# Automation Examples

Ready-to-use automation blueprints for the **Nordic Electricity Prices**
integration. Replace `no5` with your price area code (e.g., `no1`, `se3`, `fi`).

---

## Notifications

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

### Notify When Tomorrow's Prices Are Available

```yaml
automation:
  - alias: "Tomorrow prices available"
    trigger:
      - platform: event
        event_type: norway_electricity_tomorrow_available
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "📊 Tomorrow's electricity prices"
          message: >
            Prices for tomorrow are now available.
            Cheapest window:
            {{ state_attr('binary_sensor.cheapest_hours_no5', 'best_consecutive_window') }}
```

### Notify When Price Drops Below Threshold

```yaml
automation:
  - alias: "Price below threshold alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.price_below_threshold_no5
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "💚 Price below threshold!"
          message: >
            Current price: {{ state_attr('binary_sensor.price_below_threshold_no5', 'current_price') }} NOK/kWh
            (threshold: {{ state_attr('binary_sensor.price_below_threshold_no5', 'threshold') }} NOK/kWh)
```

### Notify When Price Rises Above Threshold

```yaml
automation:
  - alias: "Price above threshold alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.price_above_threshold_no5
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🔴 Price above threshold!"
          message: >
            Current price: {{ state_attr('binary_sensor.price_above_threshold_no5', 'current_price') }} NOK/kWh
            (threshold: {{ state_attr('binary_sensor.price_above_threshold_no5', 'threshold') }} NOK/kWh)
```

### Daily Price Summary

```yaml
automation:
  - alias: "Daily electricity summary"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "📈 Today's electricity prices"
          message: >
            Average: {{ states('sensor.average_price_no5') }} NOK/kWh
            Cheapest: {{ states('sensor.min_price_no5') }} NOK/kWh (hour {{ state_attr('sensor.min_price_no5', 'hour') }})
            Most expensive: {{ states('sensor.max_price_no5') }} NOK/kWh (hour {{ state_attr('sensor.max_price_no5', 'hour') }})
            Current level: {{ states('sensor.price_level_no5') }}
```

---

## Smart Appliance Control

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

### Run Dishwasher During Cheap Hours

```yaml
automation:
  - alias: "Start dishwasher when cheap"
    trigger:
      - platform: state
        entity_id: binary_sensor.cheapest_hours_no5
        to: "on"
    condition:
      - condition: state
        entity_id: input_boolean.dishwasher_ready
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.dishwasher
      - service: input_boolean.turn_off
        entity_id: input_boolean.dishwasher_ready
```

### Water Heater — Boost During Cheap, Reduce During Expensive

```yaml
automation:
  - alias: "Water heater boost — cheap electricity"
    trigger:
      - platform: state
        entity_id: binary_sensor.cheapest_hours_no5
        to: "on"
    action:
      - service: climate.set_temperature
        entity_id: climate.water_heater
        data:
          temperature: 70

  - alias: "Water heater eco — expensive electricity"
    trigger:
      - platform: state
        entity_id: binary_sensor.expensive_hours_no5
        to: "on"
    action:
      - service: climate.set_temperature
        entity_id: climate.water_heater
        data:
          temperature: 50
```

---

## Lovelace Cards

### Hourly Price Bar Chart (Today)

Requires [apexcharts-card](https://github.com/RomRider/apexcharts-card)
(install via HACS).

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

### Price Chart — Today + Tomorrow

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

### Color-Coded Price Chart (Cheap = Green, Expensive = Red)

```yaml
type: custom:apexcharts-card
header:
  title: Price by Level
  show: true
graph_span: 24h
span:
  start: day
series:
  - entity: sensor.electricity_price_no5
    data_generator: |
      const data = entity.attributes.raw_today || [];
      const prices = data.map(e => e.price);
      const avg = prices.reduce((a, b) => a + b, 0) / prices.length;
      return data.map(e => {
        return [new Date(e.start).getTime(), e.price];
      });
    type: column
    name: NOK/kWh
    color_threshold:
      - value: 0
        color: "#4CAF50"
      - value: 0.5
        color: "#FFC107"
      - value: 1.0
        color: "#F44336"
```

### Simple Entity Cards

```yaml
type: entities
title: Electricity Prices (NO5)
entities:
  - entity: sensor.electricity_price_no5
    name: Current Price
  - entity: sensor.next_hour_price_no5
    name: Next Hour
  - entity: sensor.average_price_no5
    name: Today's Average
  - entity: sensor.min_price_no5
    name: Today's Cheapest
  - entity: sensor.max_price_no5
    name: Today's Most Expensive
  - entity: sensor.price_level_no5
    name: Price Level
  - entity: binary_sensor.cheapest_hours_no5
    name: Cheap Now?
  - entity: binary_sensor.expensive_hours_no5
    name: Expensive Now?
```

---

## Template Sensors

### Custom Savings Estimate

Create a template sensor showing how much you save (or overpay) relative to
the daily average:

```yaml
template:
  - sensor:
      - name: "Electricity savings indicator"
        unit_of_measurement: "NOK/kWh"
        state: >
          {% set current = states('sensor.electricity_price_no5') | float(0) %}
          {% set avg = states('sensor.average_price_no5') | float(0) %}
          {{ (avg - current) | round(4) }}
        icon: >
          {% if this.state | float(0) > 0 %}
            mdi:piggy-bank
          {% else %}
            mdi:cash-remove
          {% endif %}
```

### Price Category with Emoji

```yaml
template:
  - sensor:
      - name: "Electricity level emoji"
        state: >
          {% set level = states('sensor.price_level_no5') %}
          {% set icons = {
            'very_cheap': '🟢 Very Cheap',
            'cheap': '🟡 Cheap',
            'normal': '🔵 Normal',
            'expensive': '🟠 Expensive',
            'very_expensive': '🔴 Very Expensive'
          } %}
          {{ icons.get(level, '⚪ Unknown') }}
```
