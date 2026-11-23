"""Experimental level control, restricted to captured commands 3 and 4."""
from bleak import BleakError
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([HeaterTestLevel(entry.runtime_data, entry)])


class HeaterTestLevel(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "test_level"
    _attr_icon = "mdi:fire"
    _attr_native_min_value = 3
    _attr_native_max_value = 4
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_test_level"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.address)})

    @property
    def available(self):
        data = self.coordinator.data
        return bool(super().available and data and data.mode_raw == 2 and data.state_raw == 133)

    @property
    def native_value(self):
        data = self.coordinator.data
        # The separate sensor continues to display all ten actual levels.
        return data.level if data and data.level in (3, 4) else None

    async def async_set_native_value(self, value: float) -> None:
        if value not in (3, 4):
            raise HomeAssistantError("Für diesen Test sind nur Stufe 3 und 4 freigegeben.")
        try:
            await self.coordinator.heater.set_level(int(value))
        except (BleakError, TimeoutError, ValueError) as err:
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError(f"Stufenänderung nicht bestätigt: {err}") from err
        # Refresh after the serialized write to avoid an older in-flight poll
        # overwriting the confirmed command result in the coordinator.
        await self.coordinator.async_request_refresh()
