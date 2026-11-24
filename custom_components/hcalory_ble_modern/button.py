"""Start and stop are separate actions, with state-dependent availability."""
from bleak import BleakError
from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        HeaterPowerButton(entry.runtime_data, True),
        HeaterPowerButton(entry.runtime_data, False),
    ])


class HeaterPowerButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, enabled: bool):
        super().__init__(coordinator)
        self.enabled = enabled
        action = "start" if enabled else "stop"
        self._attr_translation_key = action
        self._attr_icon = "mdi:play" if enabled else "mdi:stop"
        self._attr_unique_id = f"{coordinator.address}_{action}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.address)})

    @property
    def available(self):
        data = self.coordinator.data
        return bool(
            super().available and data
            and (data.can_start if self.enabled else data.can_stop)
        )

    async def async_press(self) -> None:
        try:
            await self.coordinator.heater.set_power(self.enabled)
        except (BleakError, TimeoutError, ValueError) as err:
            await self.coordinator.async_request_refresh()
            raise HomeAssistantError(f"Heizbefehl nicht bestätigt: {err}") from err
        await self.coordinator.async_request_refresh()
