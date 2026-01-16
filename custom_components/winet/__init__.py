from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WiNetApi, WiNetApiError
from .const import (
    DOMAIN,
    CONF_MODE,
    CONF_HOST,
    CONF_STOVE_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)

LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "switch", "number"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    mode = entry.data[CONF_MODE]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    api = WiNetApi(
        hass=hass,
        mode=mode,
        host=entry.data.get(CONF_HOST),
        stove_id=entry.data.get(CONF_STOVE_ID),
    )

    async def _async_update_data():
        try:
            return await api.get_all()
        except WiNetApiError as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name="winet",
        update_method=_async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
