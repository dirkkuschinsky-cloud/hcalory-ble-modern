"""Status and confirmed test-level transport using Home Assistant's local or remote BLE device."""
import asyncio
from collections.abc import Callable

from bleak import BleakClient, BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .protocol import CHANNEL_UUID, HELLO, POLL, FrameDecoder, HeaterStatus, parse_status, level_command
from .protocol import START, STOP


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

    async def _request_status(self) -> HeaterStatus:
        self.waiter = asyncio.get_running_loop().create_future()
        try:
            await self.client.write_gatt_char(CHANNEL_UUID, POLL, response=False)
            return await asyncio.wait_for(self.waiter, timeout=10)
        finally:
            if self.waiter:
                if not self.waiter.done():
                    self.waiter.cancel()
                elif not self.waiter.cancelled():
                    self.waiter.exception()
            self.waiter = None

    async def set_level(self, level: int) -> HeaterStatus:
        """Write once, then require a matching device response; no optimistic state."""
        command = level_command(level)
        async with self.lock:
            try:
                async with asyncio.timeout(45):
                    await self._connect()
                    before = await self._request_status()
                    if before.state_raw != 133 or before.mode_raw != 2:
                        raise ValueError("Level changes require a running heater in power-level mode")
                    if before.level == level:
                        return before
                    await self.client.write_gatt_char(CHANNEL_UUID, command, response=False)
                    for _ in range(5):
                        await asyncio.sleep(1)
                        after = await self._request_status()
                        if after.mode_raw != 2 or after.state_raw != 133:
                            raise ValueError("Heater left running power-level mode during confirmation")
                        if after.level == level:
                            return after
                    raise TimeoutError("Requested level was not confirmed by the heater")
            except BaseException:
                await self._disconnect()
                raise

    async def set_power(self, enabled: bool) -> HeaterStatus:
        """Send one captured power command and confirm entry into its sequence.

        Acceptance is not completion of ignition/cooling. Normal polls follow
        the remaining transitions. Never replay a power write after reconnect.
        """
        if not isinstance(enabled, bool):
            raise ValueError("Power target must be a boolean")
        async with self.lock:
            try:
                async with asyncio.timeout(45):
                    await self._connect()
                    before = await self._request_status()
                    if enabled:
                        if before.state in ("starting", "running"):
                            return before
                        if not before.can_start:
                            raise ValueError("Start requires confirmed off state; cooling cannot be interrupted")
                    else:
                        if before.state in ("cooling", "off"):
                            return before
                        if not before.can_stop:
                            raise ValueError("Stop is currently supported only from confirmed running state")
                    await self.client.write_gatt_char(
                        CHANNEL_UUID, START if enabled else STOP, response=False,
                    )
                    accepted = {"starting", "running"} if enabled else {"cooling", "off"}
                    for _ in range(5):
                        await asyncio.sleep(1)
                        after = await self._request_status()
                        if after.state in accepted:
                            return after
                        if after.state == "unknown_state":
                            raise ValueError("Heater reported an unrecognized state after power command")
                    raise TimeoutError("Power command was not confirmed; check the heater before retrying")
            except BaseException:
                await self._disconnect()
                raise

    async def poll(self) -> HeaterStatus:
        """Request a complete new status, or fail within a bounded timeout."""
        async with self.lock:
            try:
                async with asyncio.timeout(45):
                    await self._connect()
                    return await self._request_status()
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
