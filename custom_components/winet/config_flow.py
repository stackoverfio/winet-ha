from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_MODE, MODE_LOCAL, MODE_CLOUD,
    CONF_HOST, CONF_STOVE_ID,
    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL,
    CONF_HAS_WATER, DEFAULT_HAS_WATER,
)
from .api import WiNetApi, WiNetApiError


class WiNetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._mode: str | None = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Step 1: scegli Locale o Cloud."""
        errors = {}

        if user_input is not None:
            self._mode = user_input[CONF_MODE]
            if self._mode == MODE_LOCAL:
                return await self.async_step_local()
            return await self.async_step_cloud()

        schema = vol.Schema({
            vol.Required(CONF_MODE, default=MODE_LOCAL): vol.In([MODE_LOCAL, MODE_CLOUD]),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_local(self, user_input=None) -> FlowResult:
        """Step 2 (Locale): chiede solo IP/Host + flag acqua + scan interval."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            has_water = user_input.get(CONF_HAS_WATER, DEFAULT_HAS_WATER)
            scan = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            api = WiNetApi(hass=self.hass, mode=MODE_LOCAL, host=host)
            try:
                await api.get_all()
            except WiNetApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="WiNet Stove (Local)",
                    data={
                        CONF_MODE: MODE_LOCAL,
                        CONF_HOST: host,
                        CONF_HAS_WATER: has_water,
                        CONF_SCAN_INTERVAL: scan,
                    },
                )

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_HAS_WATER, default=DEFAULT_HAS_WATER): bool,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
        })
        return self.async_show_form(step_id="local", data_schema=schema, errors=errors)

    async def async_step_cloud(self, user_input=None) -> FlowResult:
        """Step 2 (Cloud): chiede solo stove_id + flag acqua + scan interval."""
        errors = {}

        if user_input is not None:
            stove_id = user_input[CONF_STOVE_ID].strip()
            has_water = user_input.get(CONF_HAS_WATER, DEFAULT_HAS_WATER)
            scan = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            api = WiNetApi(hass=self.hass, mode=MODE_CLOUD, stove_id=stove_id)
            try:
                await api.get_all()
            except WiNetApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="WiNet Stove (Cloud)",
                    data={
                        CONF_MODE: MODE_CLOUD,
                        CONF_STOVE_ID: stove_id,
                        CONF_HAS_WATER: has_water,
                        CONF_SCAN_INTERVAL: scan,
                    },
                )

        schema = vol.Schema({
            vol.Required(CONF_STOVE_ID): str,
            vol.Optional(CONF_HAS_WATER, default=DEFAULT_HAS_WATER): bool,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
        })
        return self.async_show_form(step_id="cloud", data_schema=schema, errors=errors)
