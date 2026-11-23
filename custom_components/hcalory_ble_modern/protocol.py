"""BD39 protocol decoded from owner-provided Heater5069 captures.

This module has no Home Assistant or Bluetooth dependencies.
"""
from dataclasses import dataclass

SERVICE_UUID = "0000bd39-0000-1000-8000-00805f9b34fb"
CHANNEL_UUID = "0000bdf8-0000-1000-8000-00805f9b34fb"
HELLO = bytes.fromhex("000200010001000a0c000005010000000012")
POLL = bytes.fromhex("000200010001000e040000090000000000000000000d")
PREFIXES = (bytes.fromhex("000100010001"), bytes.fromhex("000300010001"))


@dataclass(frozen=True)
class HeaterStatus:
    """Only fields whose location is established; state/mode remain raw."""

    state_raw: int
    mode_raw: int
    setting_raw: int

    @property
    def level(self) -> int | None:
        """Do not label thermostat settings as power levels."""
        if self.mode_raw == 2 and 1 <= self.setting_raw <= 10:
            return self.setting_raw
        return None


def parse_status(frame: bytes) -> HeaterStatus | None:
    """Accept the captured 43-byte status frame and verify its checksum."""
    if (
        len(frame) != 43
        or frame[:6] not in PREFIXES
        or frame[6:9] != bytes.fromhex("002303")
        or sum(frame[8:-1]) % 256 != frame[-1]
    ):
        return None
    return HeaterStatus(frame[20], frame[21], frame[22])


class FrameDecoder:
    """Handle split and combined protocol frames, with bounded buffering."""

    def __init__(self) -> None:
        self.buffer = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        self.buffer.extend(data)
        frames = []
        while len(self.buffer) >= 8:
            if self.buffer[:6] not in PREFIXES:
                del self.buffer[0]
                continue
            size = int.from_bytes(self.buffer[6:8], "big") + 8
            if not 9 <= size <= 512:
                del self.buffer[0]
                continue
            if len(self.buffer) < size:
                break
            frame = bytes(self.buffer[:size])
            if sum(frame[8:-1]) % 256 != frame[-1]:
                del self.buffer[0]
                continue
            frames.append(frame)
            del self.buffer[:size]
        return frames


def level_command(level: int) -> bytes:
    """Build an absolute level command; 3/4 match captured reference packets."""
    if isinstance(level, bool) or not isinstance(level, int) or not 1 <= level <= 10:
        raise ValueError("Power level must be an integer from 1 to 10")
    payload = bytes.fromhex("000200010001000607000001") + bytes([level])
    return payload + bytes([sum(payload[8:]) % 256])
