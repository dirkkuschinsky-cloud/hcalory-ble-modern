"""Discover BD39 heaters or configure their Bluetooth address manually."""
import re

import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow

from .const import DOMAIN
from .protocol import SERVICE_UUID


class HcaloryConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_bluetooth(self, discovery_info):
        if SERVICE_UUID not in [uuid.lower() for uuid in discovery_info.service_uuids]:
            return self.async_abort(reason="not_supported")
        self.address = discovery_info.address.upper()
        self.device_name = discovery_info.name or "Hcalory BD39"
        await self.async_set_unique_id(self.address)
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {"name": self.device_name}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=self.device_name, data={"address": self.address},
            )
        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            address = user_input["address"].strip().upper()
            if not re.fullmatch(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", address):
                errors["address"] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                info = bluetooth.async_last_service_info(self.hass, address, connectable=True)
                if info is None:
                    errors["base"] = "cannot_connect"
                elif SERVICE_UUID not in [uuid.lower() for uuid in info.service_uuids]:
                    errors["base"] = "not_supported"
                else:
                    return self.async_create_entry(
                        title=info.name or "Hcalory BD39", data={"address": address},
                    )
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required("address"): str}),
            errors=errors,
        )
