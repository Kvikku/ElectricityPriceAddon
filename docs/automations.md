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

---

## Advanced Notifications

Six ready-to-use notification automations that go beyond the basics above.
Each uses `notify.mobile_app_your_phone` as a placeholder — replace it with
your actual [mobile app notify service](https://companion.home-assistant.io/docs/notifications/notifications-basic).

> **Customisation checklist:**
>
> 1. Replace `no1` with your price area (`no1`–`no5`).
> 2. Replace `notify.mobile_app_your_phone` with your notify service
>    (e.g., `notify.mobile_app_pixel_8`). Find yours under
>    **Developer Tools → Services**.
> 3. To send to **multiple people**, duplicate the `service` block or
>    use a [notify group](https://www.home-assistant.io/integrations/group/#notify-groups).
> 4. For **per-user opt-in/out**, see
>    [Per-User Notification Preferences](#per-user-notification-preferences)
>    below.

---

### 1. Price Drop Alert — Advance Warning Before Cheap Hours

Fires ~15 minutes before the cheapest consecutive window starts, giving you
lead time to prepare (load the dishwasher, plug in the car, etc.).

```yaml
automation:
  - alias: "Price drop alert — advance warning"
    trigger:
      - platform: template
        value_template: >
          {% set window = state_attr('binary_sensor.cheapest_hours_no1', 'best_consecutive_window') %}
          {% if window and window.start %}
            {% set start = as_datetime(window.start) %}
            {{ now() >= start - timedelta(minutes=15) and now() < start }}
          {% else %}
            false
          {% endif %}
    action:
      - variables:
          window: "{{ state_attr('binary_sensor.cheapest_hours_no1', 'best_consecutive_window') }}"
          price: "{{ window.average_price | round(2) }}"
          start_time: "{{ as_datetime(window.start).strftime('%H:%M') }}"
          end_time: "{{ as_datetime(window.end).strftime('%H:%M') }}"
      - service: notify.mobile_app_your_phone
        data:
          title: "🔔 Cheap electricity at {{ start_time }}"
          message: >
            Price drops to avg {{ price }} NOK/kWh ({{ start_time }}–{{ end_time }}).
            Good time to start the washing machine, charge the car, or run the dryer.
```

### 2. Price Spike Warning — Expensive Hours Approaching

Fires ~30 minutes before the first expensive hour begins.

```yaml
automation:
  - alias: "Price spike warning"
    trigger:
      - platform: template
        value_template: >
          {% set hours = state_attr('binary_sensor.expensive_hours_no1', 'expensive_hours') %}
          {% if hours and hours | length > 0 %}
            {% set first_start = as_datetime(hours[0].start) %}
            {{ now() >= first_start - timedelta(minutes=30) and now() < first_start }}
          {% else %}
            false
          {% endif %}
    action:
      - variables:
          hours: "{{ state_attr('binary_sensor.expensive_hours_no1', 'expensive_hours') }}"
          first_price: "{{ hours[0].price | round(2) }}"
          first_time: "{{ as_datetime(hours[0].start).strftime('%H:%M') }}"
      - service: notify.mobile_app_your_phone
        data:
          title: "⚠️ Expensive electricity at {{ first_time }}"
          message: >
            Price rises to {{ first_price }} NOK/kWh at {{ first_time }}.
            Consider finishing high-consumption tasks now.
```

### 3. Tomorrow Planning — Actionable Daily Plan

Fires when tomorrow's prices become available (~13:00 CET). Includes
tomorrow's cheapest window and a comparison to today.

```yaml
automation:
  - alias: "Tomorrow price planning"
    trigger:
      - platform: event
        event_type: norway_electricity_tomorrow_available
    action:
      - variables:
          window: "{{ state_attr('binary_sensor.cheapest_hours_no1', 'best_consecutive_window_tomorrow') }}"
          tomorrow_avg: >
            {% set prices = state_attr('sensor.electricity_price_no1', 'raw_tomorrow') %}
            {% if prices %}
              {{ (prices | map(attribute='price') | list | sum / prices | length) | round(2) }}
            {% else %}N/A{% endif %}
          today_avg: "{{ states('sensor.average_price_no1') }}"
          comparison: >
            {% set prices = state_attr('sensor.electricity_price_no1', 'raw_tomorrow') %}
            {% if prices %}
              {% set tmr = (prices | map(attribute='price') | list | sum / prices | length) %}
              {% set tod = states('sensor.average_price_no1') | float(0) %}
              {% if tmr < tod %}cheaper{% elif tmr > tod %}more expensive{% else %}about the same{% endif %}
            {% else %}unknown{% endif %}
          cheap_start: >
            {% if window %}{{ as_datetime(window.start).strftime('%H:%M') }}{% else %}N/A{% endif %}
          cheap_end: >
            {% if window %}{{ as_datetime(window.end).strftime('%H:%M') }}{% else %}N/A{% endif %}
          cheap_avg: >
            {% if window %}{{ window.average_price | round(2) }}{% else %}N/A{% endif %}
      - service: notify.mobile_app_your_phone
        data:
          title: "📊 Plan your day tomorrow"
          message: >
            Tomorrow is {{ comparison }} than today
            (avg {{ tomorrow_avg }} vs {{ today_avg }} NOK/kWh).
            Best time for heavy usage: {{ cheap_start }}–{{ cheap_end }}
            (avg {{ cheap_avg }} NOK/kWh).
```

### 4. Price Level Change

Fires when the price level category changes (e.g., normal → very_cheap).

```yaml
automation:
  - alias: "Price level change notification"
    trigger:
      - platform: state
        entity_id: sensor.price_level_no1
    condition:
      - condition: template
        value_template: "{{ trigger.from_state.state != trigger.to_state.state }}"
    action:
      - variables:
          level: "{{ states('sensor.price_level_no1') | replace('_', ' ') | title }}"
          price: "{{ states('sensor.electricity_price_no1') }}"
          tip: >
            {% set l = states('sensor.price_level_no1') %}
            {% if l in ['very_cheap', 'cheap'] %}Great time to use electricity!
            {% elif l in ['expensive', 'very_expensive'] %}Try to reduce usage.
            {% else %}Normal pricing.{% endif %}
      - service: notify.mobile_app_your_phone
        data:
          title: "💡 Price now: {{ level }}"
          message: "{{ price }} NOK/kWh — {{ tip }}"
```

### 5. Morning Briefing — Your Electricity Day at a Glance

Fires at 07:00 every morning with a compact daily summary.

```yaml
automation:
  - alias: "Morning electricity briefing"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - variables:
          avg: "{{ states('sensor.average_price_no1') }}"
          min_price: "{{ states('sensor.min_price_no1') }}"
          min_hour: "{{ '%02d' | format(state_attr('sensor.min_price_no1', 'hour') | int) }}"
          max_price: "{{ states('sensor.max_price_no1') }}"
          max_hour: "{{ '%02d' | format(state_attr('sensor.max_price_no1', 'hour') | int) }}"
          window: "{{ state_attr('binary_sensor.cheapest_hours_no1', 'best_consecutive_window') }}"
          cheap_start: >
            {% if window %}{{ as_datetime(window.start).strftime('%H:%M') }}{% else %}N/A{% endif %}
          cheap_end: >
            {% if window %}{{ as_datetime(window.end).strftime('%H:%M') }}{% else %}N/A{% endif %}
      - service: notify.mobile_app_your_phone
        data:
          title: "🏠 Electricity today"
          message: >
            Range: {{ min_price }}–{{ max_price }} NOK/kWh (avg {{ avg }})
            Cheapest: {{ min_hour }}:00 | Most expensive: {{ max_hour }}:00
            Best window: {{ cheap_start }}–{{ cheap_end }}
            💡 Run heavy appliances during the cheap window!
```

### 6. Threshold Alerts — Price Crossed Your Limit

Fires when the price crosses your configured threshold (set in the
integration options under **Price threshold (NOK/kWh)**).

```yaml
automation:
  - alias: "Price dropped below threshold"
    trigger:
      - platform: state
        entity_id: binary_sensor.price_below_threshold_no1
        to: "on"
    action:
      - variables:
          threshold: "{{ state_attr('binary_sensor.price_below_threshold_no1', 'threshold') }}"
          price: "{{ state_attr('binary_sensor.price_below_threshold_no1', 'current_price') }}"
      - service: notify.mobile_app_your_phone
        data:
          title: "📉 Price below {{ threshold }} NOK/kWh"
          message: >
            Current price: {{ price }} NOK/kWh — below your target!
            Use electricity now.

  - alias: "Price exceeded threshold"
    trigger:
      - platform: state
        entity_id: binary_sensor.price_above_threshold_no1
        to: "on"
    action:
      - variables:
          threshold: "{{ state_attr('binary_sensor.price_above_threshold_no1', 'threshold') }}"
          price: "{{ state_attr('binary_sensor.price_above_threshold_no1', 'current_price') }}"
      - service: notify.mobile_app_your_phone
        data:
          title: "📈 Price above {{ threshold }} NOK/kWh"
          message: >
            Current price: {{ price }} NOK/kWh — over your limit!
            Reduce usage if possible.
```

---

## Per-User Notification Preferences

If multiple people share your Home Assistant, you can let each person choose
which notifications they receive using **input_boolean helpers**.

### Step 1 — Create Helpers

Add to `configuration.yaml`, or create them in the UI via
**Settings → Devices → Helpers → Toggle**.

Create one set per person, using a consistent naming convention:

```yaml
input_boolean:
  # Replace "alice" with the person's name (lowercase, no spaces).
  # Repeat the entire block for each household member.
  alice_notify_price_drop:
    name: "Alice: Price drop alert"
    icon: mdi:arrow-down-bold
  alice_notify_price_spike:
    name: "Alice: Price spike warning"
    icon: mdi:arrow-up-bold
  alice_notify_tomorrow_plan:
    name: "Alice: Tomorrow planning"
    icon: mdi:calendar-clock
  alice_notify_level_change:
    name: "Alice: Price level change"
    icon: mdi:speedometer
  alice_notify_morning_briefing:
    name: "Alice: Morning briefing"
    icon: mdi:weather-sunny
  alice_notify_threshold:
    name: "Alice: Threshold alerts"
    icon: mdi:target
```

### Step 2 — Dashboard Card

Give each user a toggle card on their personal dashboard so they can enable
or disable each notification type:

```yaml
type: entities
title: 🔔 My Electricity Notifications
entities:
  - entity: input_boolean.alice_notify_price_drop
    name: Price drop alert
  - entity: input_boolean.alice_notify_price_spike
    name: Price spike warning
  - entity: input_boolean.alice_notify_tomorrow_plan
    name: Tomorrow planning
  - entity: input_boolean.alice_notify_level_change
    name: Price level change
  - entity: input_boolean.alice_notify_morning_briefing
    name: Morning briefing
  - entity: input_boolean.alice_notify_threshold
    name: Threshold alerts
```

### Step 3 — Add Conditions to Any Automation

Wrap the `service` call in any automation above with a condition. For
example, to gate the morning briefing for two people:

```yaml
# Replace the single "service:" block in any automation above with this:
action:
  - variables:
      # ... (keep the existing variables from the automation)
  # --- Alice ---
  - if:
      - condition: state
        entity_id: input_boolean.alice_notify_morning_briefing
        state: "on"
    then:
      - service: notify.mobile_app_alice_phone
        data:
          title: "🏠 Electricity today"
          message: >
            Range: {{ min_price }}–{{ max_price }} NOK/kWh (avg {{ avg }})
            Best window: {{ cheap_start }}–{{ cheap_end }}
  # --- Bob (copy the block above, change the entity IDs) ---
  - if:
      - condition: state
        entity_id: input_boolean.bob_notify_morning_briefing
        state: "on"
    then:
      - service: notify.mobile_app_bob_phone
        data:
          title: "🏠 Electricity today"
          message: >
            Range: {{ min_price }}–{{ max_price }} NOK/kWh (avg {{ avg }})
            Best window: {{ cheap_start }}–{{ cheap_end }}
```

> **Tip:** To avoid duplicating messages, create a
> [notify group](https://www.home-assistant.io/integrations/group/#notify-groups)
> that includes only the opted-in members, or use a
> [script](https://www.home-assistant.io/integrations/script/) with a
> `target` variable.

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
