"""Power commands and transitions based on owner-provided start/stop captures."""
import asyncio
import json
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from support import protocol
from test_client import transport, FakePeer, BleakError

FRAMES = {int(k): bytes.fromhex(v) for k, v in json.loads(
    (Path(__file__).parent / "fixtures/power_states.json").read_text()
).items()}


class PowerProtocolTests(unittest.TestCase):
    def test_exact_captured_commands(self):
        self.assertEqual(protocol.START.hex(), "000200010001000e040000090000000000000000020f")
        self.assertEqual(protocol.STOP.hex(), "000200010001000e040000090000000000000000010e")

    def test_complete_captured_transition_sequences(self):
        raw = [0, 128, 129, 131, 135, 133, 68, 69, 67, 65, 0]
        expected = ["off"] + ["starting"] * 4 + ["running"] + ["cooling"] * 4 + ["off"]
        self.assertEqual([protocol.parse_status(FRAMES[x]).state for x in raw], expected)

    def test_unknown_states_do_not_become_off(self):
        for raw in (1, 64, 66, 132, 255):
            status = protocol.HeaterStatus(raw, 0, 0)
            self.assertEqual(status.state, "unknown_state")
            self.assertFalse(status.can_start)
            self.assertFalse(status.can_stop)

    def test_start_and_stop_permissions(self):
        for raw, frame in FRAMES.items():
            data = protocol.parse_status(frame)
            self.assertEqual(data.can_start, raw == 0)
            self.assertEqual(data.can_stop, raw == 133)


class PowerPeer(FakePeer):
    def __init__(self, state=0):
        super().__init__()
        self.state = state
        self.accept_commands = True
        self.reject_state = None

    async def write_gatt_char(self, uuid, data, response):
        self.writes.append((uuid, data, response))
        if data == protocol.POLL:
            frame = bytearray(FRAMES.get(self.state, FRAMES[0]))
            frame[20] = self.state
            frame[-1] = sum(frame[8:-1]) % 256
            self.callback(None, frame)
        elif data in (protocol.START, protocol.STOP) and self.accept_commands:
            self.state = self.reject_state if self.reject_state is not None else (
                128 if data == protocol.START else 68
            )


class PowerTransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.peer = PowerPeer()
        patcher = patch.object(transport, "establish_connection", AsyncMock(return_value=self.peer))
        self.establish = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(transport.asyncio, "sleep", AsyncMock())
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = transport.HeaterClient(lambda: object(), "Test")

    async def test_start_confirms_starting_not_running(self):
        result = await self.client.set_power(True)
        self.assertEqual(result.state, "starting")
        self.assertEqual(sum(w[1] == protocol.START for w in self.peer.writes), 1)

    async def test_stop_confirms_cooling_not_off(self):
        self.peer.state = 133
        result = await self.client.set_power(False)
        self.assertEqual(result.state, "cooling")
        self.assertEqual(sum(w[1] == protocol.STOP for w in self.peer.writes), 1)

    async def test_start_rejected_for_every_cooling_state(self):
        for state in (68, 69, 67, 65):
            self.peer.state = state
            with self.assertRaises(ValueError):
                await self.client.set_power(True)
        self.assertNotIn(protocol.START, [w[1] for w in self.peer.writes])

    async def test_no_duplicate_start_when_starting_or_running(self):
        for state in (128, 129, 131, 135, 133):
            self.peer.state = state
            await self.client.set_power(True)
        self.assertNotIn(protocol.START, [w[1] for w in self.peer.writes])

    async def test_no_duplicate_stop_when_cooling_or_off(self):
        for state in (68, 69, 67, 65, 0):
            self.peer.state = state
            await self.client.set_power(False)
        self.assertNotIn(protocol.STOP, [w[1] for w in self.peer.writes])

    async def test_stop_during_ignition_not_enabled_without_evidence(self):
        self.peer.state = 131
        with self.assertRaises(ValueError):
            await self.client.set_power(False)
        self.assertNotIn(protocol.STOP, [w[1] for w in self.peer.writes])

    async def test_unknown_state_rejects_both_commands(self):
        self.peer.state = 255
        for enabled in (True, False):
            with self.assertRaises(ValueError):
                await self.client.set_power(enabled)
        self.assertFalse(any(w[1] in (protocol.START, protocol.STOP) for w in self.peer.writes))

    async def test_timeout_does_not_repeat_start(self):
        self.peer.accept_commands = False
        with self.assertRaises(TimeoutError):
            await self.client.set_power(True)
        self.assertEqual(sum(w[1] == protocol.START for w in self.peer.writes), 1)

    async def test_timeout_does_not_repeat_stop(self):
        self.peer.state = 133
        self.peer.accept_commands = False
        with self.assertRaises(TimeoutError):
            await self.client.set_power(False)
        self.assertEqual(sum(w[1] == protocol.STOP for w in self.peer.writes), 1)

    async def test_unknown_confirmation_is_error(self):
        self.peer.reject_state = 255
        with self.assertRaises(ValueError):
            await self.client.set_power(True)

    async def test_concurrent_start_requests_only_write_once(self):
        result = await asyncio.gather(self.client.set_power(True), self.client.set_power(True))
        self.assertTrue(all(status.state == "starting" for status in result))
        self.assertEqual(sum(w[1] == protocol.START for w in self.peer.writes), 1)

    async def test_poll_follows_start_and_cooling_to_completion(self):
        await self.client.set_power(True)
        for raw in (129, 131, 135, 133):
            self.peer.state = raw
            self.assertEqual((await self.client.poll()).state, "running" if raw == 133 else "starting")
        await self.client.set_power(False)
        for raw in (69, 67, 65, 0):
            self.peer.state = raw
            self.assertEqual((await self.client.poll()).state, "off" if raw == 0 else "cooling")

    async def test_level_change_during_cooling_is_rejected(self):
        self.peer.state = 65
        with self.assertRaises(ValueError):
            await self.client.set_level(3)
        self.assertNotIn(protocol.level_command(3), [w[1] for w in self.peer.writes])

    async def test_nonboolean_power_target_rejected_before_connection(self):
        for value in (0, 1, "on", None):
            with self.assertRaises(ValueError):
                await self.client.set_power(value)
        self.establish.assert_not_awaited()
