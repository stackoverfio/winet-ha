from __future__ import annotations

import asyncio

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HAS_WATER
from .entity import WiNetEntity

DEBOUNCE_SECONDS = 2.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    has_water = entry.data.get(CONF_HAS_WATER, False)

    entities: list[NumberEntity] = [
        WiNetSetPowerNumber(coordinator, entry.entry_id, api.mode, api),
        WiNetSetAirTempNumber(coordinator, entry.entry_id, api.mode, api),
    ]

    if has_water:
        entities.append(WiNetSetWaterTempNumber(coordinator, entry.entry_id, api.mode, api))

    async_add_entities(entities)


class _DebouncedNumberBase(WiNetEntity, NumberEntity):
    """Base per Number con invio debounced per ridurre scritture su memoria limitata."""

    def __init__(self, coordinator, entry_id: str, mode: str, api):
        super().__init__(coordinator, entry_id, mode)
        self._api = api
        self._pending_task: asyncio.Task | None = None
        self._pending_value: float | None = None

    async def async_will_remove_from_hass(self) -> None:
        if self._pending_task and not self._pending_task.done():
            self._pending_task.cancel()

    def _cancel_pending(self) -> None:
        if self._pending_task and not self._pending_task.done():
            self._pending_task.cancel()

    async def _debounced_send(self) -> None:
        try:
            await asyncio.sleep(DEBOUNCE_SECONDS)
            final_val = self._pending_value
            if final_val is None:
                return

            await self._send_value(final_val)
            await self.coordinator.async_request_refresh()

        except asyncio.CancelledError:
            return

    async def _send_value(self, value: float) -> None:
        raise NotImplementedError

    async def async_set_native_value(self, value: float) -> None:
        new_val = float(value)

        current = self.native_value
        if current is not None:
            try:
                if abs(float(current) - new_val) < 1e-6:
                    return
            except (TypeError, ValueError):
                pass

        self._pending_value = new_val
        self._cancel_pending()
        self._pending_task = asyncio.create_task(self._debounced_send())


class WiNetSetPowerNumber(_DebouncedNumberBase):
    _attr_name = "WiNet Set Power"
    _attr_min_value = 1
    _attr_max_value = 5
    _attr_step = 1
    _attr_mode = "slider"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry_id: str, mode: str, api):
        super().__init__(coordinator, entry_id, mode, api)
        self._attr_unique_id = f"{entry_id}_set_power"

    @property
    def native_value(self):
        val = self.coordinator.data.get("power")
        if val is None:
            return None
        try:
            return int(float(val))
        except (TypeError, ValueError):
            return None

    async def _send_value(self, value: float) -> None:
        if value < 1:
            value = 1
        if value > 5:
            value = 5
        await self._api.set_power(int(value))


class WiNetSetAirTempNumber(_DebouncedNumberBase):
    _attr_name = "WiNet Set Air Temperature"
    _attr_native_unit_of_measurement = "°C"
    _attr_min_value = 5
    _attr_max_value = 40
    _attr_step = 0.5
    _attr_mode = "slider"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry_id: str, mode: str, api):
        super().__init__(coordinator, entry_id, mode, api)
        self._attr_unique_id = f"{entry_id}_set_air_temp"

    @property
    def native_value(self):
        val = self.coordinator.data.get("setAir")
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    async def _send_value(self, value: float) -> None:
        if value < 5:
            value = 5
        if value > 40:
            value = 40
        await self._api.set_air_temperature(value)


class WiNetSetWaterTempNumber(_DebouncedNumberBase):
    _attr_name = "WiNet Set Water Temperature"
    _attr_native_unit_of_measurement = "°C"
    _attr_min_value = 40
    _attr_max_value = 80
    _attr_step = 0.5
    _attr_mode = "slider"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry_id: str, mode: str, api):
        super().__init__(coordinator, entry_id, mode, api)
        self._attr_unique_id = f"{entry_id}_set_water_temp"

    @property
    def native_value(self):
        val = self.coordinator.data.get("setWater")
        if val is None:
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    async def _send_value(self, value: float) -> None:
        if value < 40:
            value = 40
        if value > 80:
            value = 80
        await self._api.set_water_temperature(value)
