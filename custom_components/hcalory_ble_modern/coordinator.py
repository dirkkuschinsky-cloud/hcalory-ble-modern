"""Poll the heater through Home Assistant's Bluetooth manager."""
from datetime import timedelta
import logging

from bleak import BleakError
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import HeaterClient
from .const import DOMAIN
from .protocol import HeaterStatus


class HeaterCoordinator(DataUpdateCoordinator[HeaterStatus]):
    def __init__(self, hass: HomeAssistant, entry) -> None:
        super().__init__(
            hass, logging.getLogger(__name__), name=DOMAIN,
            config_entry=entry, update_interval=timedelta(seconds=5),
        )
        self.address = entry.data["address"]
        self.heater = HeaterClient(
            lambda: bluetooth.async_ble_device_from_address(
                hass, self.address, connectable=True,
            ), entry.title,
        )

    async def _async_update_data(self) -> HeaterStatus:
        try:
            return await self.heater.poll()
        except (BleakError, TimeoutError) as err:
            raise UpdateFailed("No valid heater status received") from err
