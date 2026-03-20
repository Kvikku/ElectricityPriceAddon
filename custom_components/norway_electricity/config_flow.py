"""Config flow for Norway Electricity Prices."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback

from .const import (
    CONF_AREA,
    CONF_CHEAP_HOURS,
    CONF_EXPENSIVE_HOURS,
    CONF_VAT,
    DEFAULT_CHEAP_HOURS,
    DEFAULT_EXPENSIVE_HOURS,
    DEFAULT_VAT,
    DOMAIN,
    PRICE_AREAS,
)


class NorwayElectricityConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Norway Electricity Prices."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step — select price area."""
        if user_input is not None:
            area = user_input[CONF_AREA]
            # Prevent duplicate entries for the same area
            await self.async_set_unique_id(area)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Electricity {area} ({PRICE_AREAS[area]})",
                data={CONF_AREA: area},
                options={
                    CONF_VAT: DEFAULT_VAT,
                    CONF_CHEAP_HOURS: DEFAULT_CHEAP_HOURS,
                    CONF_EXPENSIVE_HOURS: DEFAULT_EXPENSIVE_HOURS,
                },
            )

        area_options = {code: f"{code} — {name}" for code, name in PRICE_AREAS.items()}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AREA): vol.In(area_options),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return NorwayElectricityOptionsFlow(config_entry)


class NorwayElectricityOptionsFlow(OptionsFlow):
    """Handle options for Norway Electricity Prices."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_VAT,
                        default=current.get(CONF_VAT, DEFAULT_VAT),
                    ): bool,
                    vol.Required(
                        CONF_CHEAP_HOURS,
                        default=current.get(CONF_CHEAP_HOURS, DEFAULT_CHEAP_HOURS),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
                    vol.Required(
                        CONF_EXPENSIVE_HOURS,
                        default=current.get(
                            CONF_EXPENSIVE_HOURS, DEFAULT_EXPENSIVE_HOURS
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
                }
            ),
        )
