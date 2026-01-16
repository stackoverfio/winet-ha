from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_HAS_WATER
from .entity import WiNetEntity


STATUS_MAP_LOCAL = {
    0: "SPENTO",
    1: "ACCESO",
    2: "PULIZIA FINALE",
    3: "ALARM",
    4: "UNMANAGED",
}

STATUS_MAP_CLOUD = {
    0: "SPENTO",
    1: "ATTESA FIAMMA",
    2: "ATTESA FIAMMA",
    3: "ACCESO",
    4: "ACCESO",
    5: "STAND-BY",
    6: "PULIZIA FINALE",
    7: "PULIZIA BRACIERE",
    8: "ALARM",
    9: "ALARM",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    mode = api.mode
    entry_id = entry.entry_id
    has_water = entry.data.get(CONF_HAS_WATER, False)

    entities: list[SensorEntity] = [
        WiNetStatusSensor(coordinator, entry_id, mode),
        WiNetAirTempSensor(coordinator, entry_id, mode),
        WiNetSetAirTempSensor(coordinator, entry_id, mode),
        WiNetPowerSensor(coordinator, entry_id, mode),
    ]

    if has_water:
        entities += [
            WiNetWaterTempSensor(coordinator, entry_id, mode),
            WiNetSetWaterTempSensor(coordinator, entry_id, mode),
        ]

    entities += [
        WiNetFlueTempSensor(coordinator, entry_id, mode),
        WiNetExtractorRpmSensor(coordinator, entry_id, mode),
    ]

    async_add_entities(entities)


class WiNetStatusSensor(WiNetEntity, SensorEntity):
    _attr_name = "WiNet Status"

    def __init__(self, coordinator, entry_id: str, mode: str):
        super().__init__(coordinator, entry_id, mode)
        self._attr_unique_id = f"{entry_id}_status"

    @property
    def native_value(self):
        st = self.coordinator.data.get("status")
        if st is None:
            return None
        mapping = STATUS_MAP_LOCAL if self._mode == "local" else STATUS_MAP_CLOUD
        return mapping.get(st, f"UNKNOWN ({st})")


class WiNetAirTempSensor(WiNetEntity, SensorEntity):
    _attr_name = "WiNet Air Temperature"
    _attr_native_unit_of_measurement = "°C"
    _attr_device_class = "temperature"

    def __init__(self, coordinator, entry_id: str, mode: str):
        super().__init__(coordinator, entry_id, mode)
        self._attr_unique_id = f"{entry_id}_air_temperature"

    @property
    def native_value(self):
        return self.coordinator.data.get("air")


class WiNetSetAirTempSensor(WiNetEntity, SensorEntity):
    _attr_name = "WiNet Target Air Temperature"
    _attr_native_unit_of_measurement = "°C"
    _attr_device_class = "temperature"

    def __init__(self, coordinator, entry_id: str, mode: str):
        super().__init__(coordinator, entry_id, mode)
        self._attr_unique_id = f"{entry_id}_target_air_temperature"

    @property
    def native_value(self):
        return self.coordinator.data.get("setAir")


class WiNetPowerSensor(WiNetEntity, SensorEntity):
    _attr_name = "WiNet Power (reported)"

    def __init__(self, coordinator, entry_id: str, mode: str):
        super().__init__(coordinator, entry_id, mode)
        self._attr_unique_id = f"{entry_id}_power_reported"

    @property
    def native_value(self):
        return self.coordinator.data.get("power")


# ===== SENSORI OPZIONALI (ACQUA) =====

class WiNetWaterTempSensor(WiNetEntity, SensorEntity):
    _attr_name = "WiNet Water Temperature"
    _attr_native_unit_of_measurement = "°C"
    _attr_device_class = "temperature"

    def __init__(self, coordinator, entry_id: str, mode: str):
        super().__init__(coordinator, entry_id, mode)
        self._attr_unique_id = f"{entry_id}_water_temperature"

    @property
    def native_value(self):
        val = self.coordinator.data.get("water")
        return None if val in (None, "---") else val


class WiNetSetWaterTempSensor(WiNetEntity, SensorEntity):
    _attr_name = "WiNet Target Water Temperature"
    _attr_native_unit_of_measurement = "°C"
    _attr_device_class = "temperature"

    def __init__(self, coordinator, entry_id: str, mode: str):
        super().__init__(coordinator, entry_id, mode)
        self._attr_unique_id = f"{entry_id}_target_water_temperature"

    @property
    def native_value(self):
        val = self.coordinator.data.get("setWater")
        return None if val in (None, "---") else val


# ===== SENSORI DIAGNOSTICA (FUMI / RPM) =====

class WiNetFlueTempSensor(WiNetEntity, SensorEntity):
    _attr_name = "WiNet Flue Temperature"
    _attr_native_unit_of_measurement = "°C"
    _attr_device_class = "temperature"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator, entry_id: str, mode: str):
        super().__init__(coordinator, entry_id, mode)
        self._attr_unique_id = f"{entry_id}_flue_temperature"

    @property
    def native_value(self):
        val = self.coordinator.data.get("gasflue")
        if val is None:
            return None
        try:
            v = float(val)
        except (TypeError, ValueError):
            return None
        return None if v <= 30 else v


class WiNetExtractorRpmSensor(WiNetEntity, SensorEntity):
    _attr_name = "WiNet Extractor RPM"
    _attr_native_unit_of_measurement = "rpm"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator, entry_id: str, mode: str):
        super().__init__(coordinator, entry_id, mode)
        self._attr_unique_id = f"{entry_id}_extractor_rpm"

    @property
    def native_value(self):
        val = self.coordinator.data.get("rpmExtractor")
        if val is None:
            return 0
        try:
            return int(float(val))
        except (TypeError, ValueError):
            return 0
