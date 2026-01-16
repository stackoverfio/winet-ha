from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import WiNetEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    async_add_entities([WiNetStoveSwitch(coordinator, entry.entry_id, api.mode, api)])


class WiNetStoveSwitch(WiNetEntity, SwitchEntity):
    _attr_name = "WiNet Stove"

    def __init__(self, coordinator, entry_id: str, mode: str, api):
        super().__init__(coordinator, entry_id, mode)
        self._api = api
        self._attr_unique_id = f"{entry_id}_stove_switch"

    @property
    def is_on(self):
        status = self.coordinator.data.get("status")
        if self._mode == "local":
            return status == 1
        return status in (3, 4)

    async def async_turn_on(self, **kwargs):
        await self._api.ignite()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._api.shutdown()
        await self.coordinator.async_request_refresh()
