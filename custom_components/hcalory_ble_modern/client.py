"""Status-only transport using Home Assistant's local or remote BLE device."""
import asyncio
from collections.abc import Callable

from bleak import BleakClient, BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .protocol import CHANNEL_UUID, HELLO, POLL, FrameDecoder, HeaterStatus, parse_status


class HeaterClient:
    """Serialize polls and discard status from an earlier request/session."""

    def __init__(self, get_device: Callable, name: str) -> None:
        self.get_device = get_device
        self.name = name
        self.client: BleakClient | None = None
        self.decoder = FrameDecoder()
        self.lock = asyncio.Lock()
        self.waiter: asyncio.Future[HeaterStatus] | None = None

    def _disconnected(self, client: BleakClient) -> None:
        if client is self.client:
            self.client = None
            self.decoder = FrameDecoder()
            if self.waiter and not self.waiter.done():
                self.waiter.set_exception(BleakError("Heater disconnected"))

    def _notify(self, sender, data: bytearray) -> None:
        for frame in self.decoder.feed(data):
            status = parse_status(frame)
            if status and self.waiter and not self.waiter.done():
                self.waiter.set_result(status)

    async def _connect(self) -> None:
        if self.client and self.client.is_connected:
            return
        device = self.get_device()
        if device is None:
            raise BleakError("Heater not visible to a connectable Bluetooth adapter")
        self.decoder = FrameDecoder()
        client = await establish_connection(
            BleakClientWithServiceCache, device, self.name,
            disconnected_callback=self._disconnected,
            ble_device_callback=self.get_device,
        )
        self.client = client
        try:
            await client.start_notify(CHANNEL_UUID, self._notify)
            await client.write_gatt_char(CHANNEL_UUID, HELLO, response=False)
            await asyncio.sleep(0.3)
        except BaseException:
            await self._disconnect()
            raise

    async def poll(self) -> HeaterStatus:
        """Request a complete new status, or fail within a bounded timeout."""
        async with self.lock:
            try:
                async with asyncio.timeout(45):
                    await self._connect()
                    self.waiter = asyncio.get_running_loop().create_future()
                    await self.client.write_gatt_char(CHANNEL_UUID, POLL, response=False)
                    return await asyncio.wait_for(self.waiter, timeout=10)
            except BaseException:
                await self._disconnect()
                raise
            finally:
                if self.waiter:
                    if not self.waiter.done():
                        self.waiter.cancel()
                    elif not self.waiter.cancelled():
                        self.waiter.exception()
                self.waiter = None

    async def _disconnect(self) -> None:
        client, self.client = self.client, None
        self.decoder = FrameDecoder()
        if client:
            try:
                async with asyncio.timeout(10):
                    await client.disconnect()
            except (BleakError, TimeoutError):
                pass

    async def disconnect(self) -> None:
        async with self.lock:
            await self._disconnect()
