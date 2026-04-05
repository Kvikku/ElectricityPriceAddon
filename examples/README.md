# Example Dashboards

This folder contains ready-to-use Home Assistant dashboards for the
**Norway Electricity Prices** integration, ordered from simple to complex.

> **Tip:** Every example uses **NO3 (Trondheim)** as the price area.
> Replace every occurrence of `no3` with your area code (`no1`, `no2`,
> `no4`, or `no5`) to match your region.

## How to install a dashboard

1. In Home Assistant go to **Settings → Dashboards → Add Dashboard**.
2. Open the new dashboard and click **⋮ → Edit Dashboard → Raw
   configuration editor**.
3. Paste the contents of the chosen YAML file and click **Save**.

---

## Dashboards at a glance

| File | Complexity | HACS extras? | Description |
|------|:----------:|:------------:|-------------|
| [`dashboard-minimal.yaml`](dashboard-minimal.yaml) | 🟢 Simple | None | Two glance cards showing current price, next hour, price level, average, and cheap/expensive status. Perfect as a sidebar panel or secondary view. |
| [`dashboard-overview.yaml`](dashboard-overview.yaml) | 🟡 Moderate | None | A full-page daily overview with a colour-coded gauge, current vs next hour, daily min/avg/max statistics, cheap/expensive indicators, and a "current vs average" comparison. Uses only built-in HA cards. |
| [`dashboard.yaml`](dashboard.yaml) | 🟠 Detailed | [apexcharts-card] | The comprehensive reference dashboard: gauge, entity cards, daily stats, colour-coded hourly bar chart, 48-hour forecast, best charging window, cheapest/expensive hour tables, and a full entity list. |
| [`dashboard-ev-charging.yaml`](dashboard-ev-charging.yaml) | 🔴 Advanced | [apexcharts-card] | An energy-optimisation dashboard for EV owners and smart-home users. Highlights the best consecutive charging window, side-by-side cheapest/expensive hour tables, hourly chart with average overlay, and a 48-hour forecast. |

[apexcharts-card]: https://github.com/RomRider/apexcharts-card

---

## What you'll need

| Requirement | Minimal | Overview | Detailed | EV / Smart-Home |
|-------------|:-------:|:--------:|:--------:|:---------------:|
| Norway Electricity Prices integration | ✅ | ✅ | ✅ | ✅ |
| [apexcharts-card][apexcharts-card] (HACS frontend) | — | — | ✅ | ✅ |

---

## Customisation ideas

- **Combine dashboards:** Copy individual cards from different files into
  a single dashboard to create your own mix.
- **Add automations panel:** Pair any dashboard with the automation
  examples in [`docs/automations.md`](../docs/automations.md).
- **Multiple areas:** Duplicate cards for different price areas to compare
  regions on the same dashboard.
- **Theme colours:** Adjust the `color` values in gauge segments and chart
  `color_threshold` entries to match your HA theme.
