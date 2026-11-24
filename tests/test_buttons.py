"""Entity-boundary regression tests, including HA's read-only enabled property."""
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

from support import load, protocol
from test_client import BleakError


class FakeButtonEntity:
    @property
    def enabled(self):
        return True


class FakeCoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    @property
    def available(self):
        return self.coordinator.last_update_success


class HomeAssistantError(Exception):
    pass


modules = {name: types.ModuleType(name) for name in (
    'homeassistant', 'homeassistant.components', 'homeassistant.components.button',
    'homeassistant.exceptions', 'homeassistant.helpers', 'homeassistant.helpers.entity',
    'homeassistant.helpers.update_coordinator', 'bleak',
)}
modules['homeassistant.components.button'].ButtonEntity = FakeButtonEntity
modules['homeassistant.exceptions'].HomeAssistantError = HomeAssistantError
modules['homeassistant.helpers.entity'].DeviceInfo = dict
modules['homeassistant.helpers.update_coordinator'].CoordinatorEntity = FakeCoordinatorEntity
modules['bleak'].BleakError = BleakError
with patch.dict(sys.modules, modules):
    buttons = load('button')


def coordinator(raw=0, success=True):
    return types.SimpleNamespace(
        address='AA:BB:CC:DD:EE:FF', data=protocol.HeaterStatus(raw, 2, 1),
        last_update_success=success,
        heater=types.SimpleNamespace(set_power=AsyncMock()),
        async_request_refresh=AsyncMock(),
    )


class ButtonTests(unittest.IsolatedAsyncioTestCase):
    async def test_construct_both_without_overwriting_enabled(self):
        c = coordinator()
        start, stop = buttons.HeaterPowerButton(c, True), buttons.HeaterPowerButton(c, False)
        self.assertTrue(start.enabled)
        self.assertTrue(stop.enabled)
        self.assertNotEqual(start._attr_unique_id, stop._attr_unique_id)
        self.assertEqual(start._attr_translation_key, 'start')
        self.assertEqual(stop._attr_translation_key, 'stop')

    async def test_availability_follows_state_and_connection(self):
        c = coordinator()
        start, stop = buttons.HeaterPowerButton(c, True), buttons.HeaterPowerButton(c, False)
        for raw in (0, 128, 129, 131, 135, 133, 68, 69, 67, 65, 255):
            c.data = protocol.HeaterStatus(raw, 2, 1)
            self.assertEqual(start.available, raw == 0)
            self.assertEqual(stop.available, raw == 133)
        c.data = protocol.HeaterStatus(0, 0, 0)
        c.last_update_success = False
        self.assertFalse(start.available)
        self.assertFalse(stop.available)
        c.data = None
        c.last_update_success = True
        self.assertFalse(start.available)
        self.assertFalse(stop.available)

    async def test_press_uses_correct_target_then_refreshes(self):
        for target in (True, False):
            c = coordinator()
            button = buttons.HeaterPowerButton(c, target)
            await button.async_press()
            c.heater.set_power.assert_awaited_once_with(target)
            c.async_request_refresh.assert_awaited_once()

    async def test_failed_command_refreshes_and_reports_error(self):
        c = coordinator()
        c.heater.set_power.side_effect = TimeoutError('No confirmation')
        with self.assertRaises(HomeAssistantError):
            await buttons.HeaterPowerButton(c, True).async_press()
        c.heater.set_power.assert_awaited_once()
        c.async_request_refresh.assert_awaited_once()

    async def test_platform_creates_two_buttons(self):
        result = []
        await buttons.async_setup_entry(None, types.SimpleNamespace(runtime_data=coordinator()), result.extend)
        self.assertEqual(len(result), 2)
