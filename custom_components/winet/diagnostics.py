from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> dict:
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    return {
        "mode": api.mode,
        "host": getattr(api, "host", None),
        "has_water": config_entry.data.get("has_water", False),
        "last_data": coordinator.data,
    }
