# Automation Examples

Ready-to-use automation blueprints for the **Norway Electricity Prices**
integration. Replace `no5` with your price area code (e.g., `no1`, `no2`).

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

### Morning Briefing with Actionable Insight

Fires at 07:00 with a richer summary — not just averages, but *when* to use electricity.

```yaml
automation:
  - alias: "Morning electricity briefing"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "☀️ Today's electricity at a glance"
          message: >
            Avg {{ states('sensor.average_price_no5') }} NOK/kWh
            ({{ states('sensor.min_price_no5') }}–{{ states('sensor.max_price_no5') }}).
            Cheapest at {{ state_attr('sensor.min_price_no5', 'hour') }}:00,
            priciest at {{ state_attr('sensor.max_price_no5', 'hour') }}:00.
            Level now: {{ states('sensor.price_level_no5') | replace('_', ' ') }}.
            {% set window = state_attr('binary_sensor.cheapest_hours_no5', 'best_consecutive_window') %}
            {% if window %}
            Best window: {{ as_datetime(window['start']) | as_local | strftime('%H:%M') }}–{{ as_datetime(window['end']) | as_local | strftime('%H:%M') }}
            (avg {{ window['average_price'] }} NOK/kWh).
            {% endif %}
```

### Advance Warning: Cheap Electricity Approaching

Fires ~30 minutes before cheap hours begin, giving you time to load appliances before prices drop.

```yaml
automation:
  - alias: "Notify — cheap electricity in 30 minutes"
    trigger:
      - platform: time_pattern
        minutes: "/5"
    condition:
      - condition: state
        entity_id: binary_sensor.cheapest_hours_no5
        state: "off"
      - condition: template
        value_template: >
          {% set cheapest = state_attr('binary_sensor.cheapest_hours_no5', 'cheapest_hours') %}
          {% if cheapest %}
            {% set first_start = as_datetime(cheapest | first | attr('start')) %}
            {% set mins = ((first_start - now()).total_seconds() / 60) | int %}
            {{ mins in range(28, 33) }}
          {% else %}
            false
          {% endif %}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "⚡ Cheap electricity in ~30 minutes!"
          message: >
            {% set first = state_attr('binary_sensor.cheapest_hours_no5', 'cheapest_hours') | first %}
            Starts at {{ first['hour'] }}:00 ({{ first['price'] }} NOK/kWh).
            Load the dishwasher, plug in the car, or start the washing machine now!
```

### Advance Warning: Expensive Electricity Approaching

Fires ~30 minutes before expensive hours begin, prompting you to finish high-consumption tasks.

```yaml
automation:
  - alias: "Notify — expensive electricity in 30 minutes"
    trigger:
      - platform: time_pattern
        minutes: "/5"
    condition:
      - condition: state
        entity_id: binary_sensor.expensive_hours_no5
        state: "off"
      - condition: template
        value_template: >
          {% set expensive = state_attr('binary_sensor.expensive_hours_no5', 'expensive_hours') %}
          {% if expensive %}
            {% set first_start = as_datetime(expensive | first | attr('start')) %}
            {% set mins = ((first_start - now()).total_seconds() / 60) | int %}
            {{ mins in range(28, 33) }}
          {% else %}
            false
          {% endif %}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "⚠️ Expensive electricity in ~30 minutes!"
          message: >
            {% set first = state_attr('binary_sensor.expensive_hours_no5', 'expensive_hours') | first %}
            Expensive period starts at {{ first['hour'] }}:00 ({{ first['price'] }} NOK/kWh).
            Finish high-consumption tasks before then!
```

### Last-Chance Alert: Cheap Period Ending Soon

Fires ~15 minutes before cheap hours end so you can squeeze in any remaining tasks.

```yaml
automation:
  - alias: "Notify — cheap electricity ending soon"
    trigger:
      - platform: time_pattern
        minutes: "/5"
    condition:
      - condition: state
        entity_id: binary_sensor.cheapest_hours_no5
        state: "on"
      - condition: template
        value_template: >
          {% set cheapest = state_attr('binary_sensor.cheapest_hours_no5', 'cheapest_hours') %}
          {% if cheapest %}
            {% set last_hour = cheapest | last | attr('hour') %}
            {{ now().hour == last_hour and now().minute in range(44, 50) }}
          {% else %}
            false
          {% endif %}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "⏰ Cheap electricity ending soon!"
          message: >
            {% set cheapest = state_attr('binary_sensor.cheapest_hours_no5', 'cheapest_hours') %}
            {% set last_hour = cheapest | last | attr('hour') %}
            Cheap hours end at {{ last_hour + 1 }}:00.
            Current price: {{ states('sensor.electricity_price_no5') }} NOK/kWh.
            Start any remaining tasks now!
```

### Price Level Change Alert

Sends a push when the price category changes — no manual dashboard checks needed.

```yaml
automation:
  - alias: "Notify — price dropped to cheap"
    trigger:
      - platform: state
        entity_id: sensor.price_level_no5
        to:
          - "very_cheap"
          - "cheap"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🟢 Electricity is cheap now!"
          message: >
            Price: {{ states('sensor.electricity_price_no5') }} NOK/kWh
            (level: {{ states('sensor.price_level_no5') | replace('_', ' ') }}).
            Good time to run appliances!

  - alias: "Notify — price jumped to expensive"
    trigger:
      - platform: state
        entity_id: sensor.price_level_no5
        to:
          - "expensive"
          - "very_expensive"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "🔴 Electricity is expensive now!"
          message: >
            Price: {{ states('sensor.electricity_price_no5') }} NOK/kWh
            (level: {{ states('sensor.price_level_no5') | replace('_', ' ') }}).
            Try to reduce electricity usage.
```

### Tomorrow Prices — Detailed Planning

A richer version of the "tomorrow available" notification that includes a concrete action: the
best charging window, tomorrow's price range, and a comparison against today.

```yaml
automation:
  - alias: "Tomorrow prices — detailed planning"
    trigger:
      - platform: event
        event_type: norway_electricity_tomorrow_available
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "📅 Plan tomorrow's electricity usage"
          message: >
            {% set raw = state_attr('sensor.electricity_price_no5', 'raw_tomorrow') %}
            {% set today_avg = states('sensor.average_price_no5') | float(0) %}
            {% if raw %}
            {% set prices = raw | map(attribute='price') | list %}
            {% set tmrw_avg = (prices | sum / prices | length) | round(2) %}
            Tomorrow: avg {{ tmrw_avg }} NOK/kWh
            ({{ prices | min | round(2) }}–{{ prices | max | round(2) }}).
            {% if tmrw_avg < today_avg %}💚 Cheaper than today!{% else %}🔴 Pricier than today.{% endif %}
            {% endif %}
            {% set window = state_attr('binary_sensor.cheapest_hours_no5', 'best_consecutive_window') %}
            {% if window %}
            Best window: {{ as_datetime(window['start']) | as_local | strftime('%H:%M') }}–{{ as_datetime(window['end']) | as_local | strftime('%H:%M') }}
            (avg {{ window['average_price'] }} NOK/kWh).
            {% endif %}
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
