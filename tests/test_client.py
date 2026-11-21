"""Transport behavior with a simulated BLE peer; no physical hardware."""
import asyncio
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch

from support import load, protocol
from test_protocol import FRAMES


class BleakError(Exception):
    pass


# Transport tests run offline and isolate the external BLE boundary.
with patch.dict(sys.modules, {
    "bleak": types.SimpleNamespace(BleakClient=object, BleakError=BleakError),
    "bleak_retry_connector": types.SimpleNamespace(
        BleakClientWithServiceCache=object, establish_connection=AsyncMock(),
    ),
}):
    transport = load("client")


class FakePeer:
    def __init__(self):
        self.is_connected = True
        self.callback = None
        self.writes = []
        self.disconnect = AsyncMock()
        self.answer = True

    async def start_notify(self, uuid, callback):
        self.callback = callback

    async def write_gatt_char(self, uuid, data, response):
        self.writes.append((uuid, data, response))
        if data == protocol.POLL and self.answer:
            self.callback(None, bytearray(FRAMES[0]))


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.peer = FakePeer()
        self.connection = patch.object(transport, "establish_connection", AsyncMock(return_value=self.peer))
        self.establish = self.connection.start()
        self.addCleanup(self.connection.stop)
        self.client = transport.HeaterClient(lambda: object(), "Test heater")

    async def test_poll_and_connection_reuse(self):
        self.assertEqual((await self.client.poll()).level, 3)
        self.assertEqual((await self.client.poll()).level, 3)
        self.establish.assert_awaited_once()
        self.assertEqual([x[1] for x in self.peer.writes], [protocol.HELLO, protocol.POLL, protocol.POLL])
        self.assertTrue(all(x[0] == protocol.CHANNEL_UUID and x[2] is False for x in self.peer.writes))
        await self.client.disconnect()
        self.peer.disconnect.assert_awaited_once()

    async def test_no_visible_adapter(self):
        client = transport.HeaterClient(lambda: None, "Missing heater")
        with self.assertRaises(BleakError):
            await client.poll()
        self.establish.assert_not_awaited()

    async def test_notification_timeout_closes_connection(self):
        self.peer.answer = False
        with patch.object(transport.asyncio, "wait_for", AsyncMock(side_effect=TimeoutError)):
            with self.assertRaises(TimeoutError):
                await self.client.poll()
        self.peer.disconnect.assert_awaited_once()
        self.assertIsNone(self.client.client)
        self.assertIsNone(self.client.waiter)

    async def test_disconnect_invalidates_pending_request(self):
        self.client.client = self.peer
        self.client.waiter = asyncio.get_running_loop().create_future()
        self.client._disconnected(self.peer)
        with self.assertRaises(BleakError):
            await self.client.waiter
        self.assertIsNone(self.client.client)

    async def test_old_session_disconnect_does_not_break_new_session(self):
        self.client.client = self.peer
        self.client._disconnected(FakePeer())
        self.assertIs(self.client.client, self.peer)

    async def test_failed_initialization_closes_connection(self):
        self.peer.start_notify = AsyncMock(side_effect=BleakError("notify failed"))
        with self.assertRaises(BleakError):
            await self.client.poll()
        self.peer.disconnect.assert_awaited_once()
