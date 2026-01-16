from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL_LOCAL, MODEL_CLOUD


class WiNetEntity(CoordinatorEntity):
    """Base entity that provides device_info for WiNet."""

    def __init__(self, coordinator, entry_id: str, mode: str, name: str = "WiNet Stove"):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._mode = mode
        self._device_name = name

    @property
    def device_info(self) -> DeviceInfo:
        model = MODEL_LOCAL if self._mode == "local" else MODEL_CLOUD
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            manufacturer=MANUFACTURER,
            model=model,
            name=self._device_name,
        )
