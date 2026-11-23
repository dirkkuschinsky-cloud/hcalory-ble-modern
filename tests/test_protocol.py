"""Regression tests against application frames from the real heater."""
import json
from pathlib import Path
import unittest

from support import protocol as p

FRAMES = [bytes.fromhex(h) for h in json.loads(
    (Path(__file__).parent / "fixtures/status_frames.json").read_text()
)]


class ProtocolTests(unittest.TestCase):
    def test_captured_levels(self):
        self.assertEqual([p.parse_status(f).level for f in FRAMES], [3, 3, 4])

    def test_every_split_boundary(self):
        for frame in FRAMES:
            for split in range(1, len(frame)):
                decoder = p.FrameDecoder()
                self.assertEqual(decoder.feed(frame[:split]), [])
                self.assertEqual(decoder.feed(frame[split:]), [frame])

    def test_combined_frames_and_noise(self):
        self.assertEqual(p.FrameDecoder().feed(b"noise" + b"".join(FRAMES)), FRAMES)

    def test_checksum_failure_and_resynchronization(self):
        broken = bytearray(FRAMES[0])
        broken[22] = 10
        self.assertIsNone(p.parse_status(bytes(broken)))
        self.assertEqual(p.FrameDecoder().feed(bytes(broken) + FRAMES[1]), [FRAMES[1]])

    def test_oversized_frame_and_bounded_noise(self):
        decoder = p.FrameDecoder()
        self.assertEqual(decoder.feed(p.PREFIXES[0] + b"\xff\xff" + FRAMES[0]), [FRAMES[0]])
        decoder.feed(b"x" * 10000)
        self.assertLess(len(decoder.buffer), 8)

    def test_partial_frame_is_not_status(self):
        for size in range(43):
            self.assertIsNone(p.parse_status(FRAMES[0][:size]))

    def test_thermostat_is_not_power_level(self):
        self.assertIsNone(p.HeaterStatus(133, 1, 25).level)
        self.assertIsNone(p.HeaterStatus(133, 2, 0).level)
        self.assertIsNone(p.HeaterStatus(133, 2, 255).level)

    def test_only_initialization_and_poll_commands_exposed(self):
        self.assertEqual(p.HELLO.hex(), "000200010001000a0c000005010000000012")
        self.assertEqual(p.POLL.hex(), "000200010001000e040000090000000000000000000d")

class LevelCommandTests(unittest.TestCase):
    def test_captured_commands(self):
        self.assertEqual(p.level_command(3).hex(), '000200010001000607000001030b')
        self.assertEqual(p.level_command(4).hex(), '000200010001000607000001040c')

    def test_reject_invalid_levels_and_types(self):
        for value in (-1, 0, 11, 255, True, 3.0, '3', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                p.level_command(value)

    def test_all_levels_have_expected_payload_and_checksum(self):
        for level in range(1, 11):
            with self.subTest(level=level):
                command = p.level_command(level)
                self.assertEqual(len(command), 14)
                self.assertEqual(command[:12].hex(), '000200010001000607000001')
                self.assertEqual(command[12], level)
                self.assertEqual(command[13], 8 + level)
                self.assertEqual(sum(command[8:-1]) % 256, command[-1])
