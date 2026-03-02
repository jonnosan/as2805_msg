"""Tests for as2805_msg.stream — 2-byte length-header framing."""

import pytest

from as2805_msg import AS2805Message, AS2805Stream
from as2805_msg.errors import AS2805ParseError


class TestAS2805Stream:
    def _make_simple_msg(self, mti="0200"):
        msg = AS2805Message(mti=mti)
        msg[3] = "000000"
        msg[4] = "000000001000"
        msg[11] = "000001"
        return msg

    def test_write_read_roundtrip(self):
        msg = self._make_simple_msg()
        frame = AS2805Stream.write_message(msg)

        # First 2 bytes are length
        body_len = int.from_bytes(frame[:2], "big")
        assert body_len == len(frame) - 2

        msg2, consumed = AS2805Stream.read_message(frame)
        assert consumed == len(frame)
        assert msg2.mti == "0200"
        assert msg2[3] == "000000"

    def test_read_with_offset(self):
        msg = self._make_simple_msg()
        frame = AS2805Stream.write_message(msg)
        prefix = b"\xff\xff\xff"
        data = prefix + frame

        msg2, consumed = AS2805Stream.read_message(data, offset=3)
        assert consumed == len(frame)
        assert msg2.mti == "0200"

    def test_read_all(self):
        msg1 = self._make_simple_msg("0200")
        msg2 = self._make_simple_msg("0800")
        buffer = AS2805Stream.write_message(msg1) + AS2805Stream.write_message(msg2)

        messages = AS2805Stream.read_all(buffer)
        assert len(messages) == 2
        assert messages[0].mti == "0200"
        assert messages[1].mti == "0800"

    def test_not_enough_data_for_header(self):
        with pytest.raises(AS2805ParseError):
            AS2805Stream.read_message(b"\x00")

    def test_not_enough_data_for_body(self):
        # Header says 100 bytes but only 5 available
        data = b"\x00\x64" + b"\x00" * 5
        with pytest.raises(AS2805ParseError, match="exceeds"):
            AS2805Stream.read_message(data)

    def test_length_header_value(self):
        msg = self._make_simple_msg()
        body = msg.pack()
        frame = AS2805Stream.write_message(msg)
        assert frame[:2] == len(body).to_bytes(2, "big")
