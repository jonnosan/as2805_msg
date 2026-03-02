"""Tests for as2805_msg.message — AS2805Message pack/unpack."""

import pytest

from as2805_msg import AS2805Message
from as2805_msg.errors import AS2805BuildError, AS2805ParseError


class TestAS2805MessageBasic:
    def test_getitem_setitem(self):
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        assert msg[3] == "000000"

    def test_contains(self):
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        assert 3 in msg
        assert 4 not in msg

    def test_repr(self):
        msg = AS2805Message(mti="0200", fields={3: "000000", 4: "000000001000"})
        r = repr(msg)
        assert "0200" in r
        assert "3" in r

    def test_missing_field_raises(self):
        msg = AS2805Message()
        with pytest.raises(KeyError):
            _ = msg[99]


class TestAS2805MessagePackUnpack:
    def test_simple_roundtrip(self):
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        msg[4] = "000000001000"
        msg[11] = "000001"
        msg[41] = "TERM0001"

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)

        assert msg2.mti == "0200"
        assert msg2[3] == "000000"
        assert msg2[4] == "000000001000"
        assert msg2[11] == "000001"
        assert msg2[41] == "TERM0001"

    def test_network_management_roundtrip(self):
        msg = AS2805Message(mti="0800")
        msg[7] = "0302120000"
        msg[11] = "000001"
        msg[33] = "123456"
        msg[70] = "001"
        msg[100] = "999999"

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)

        assert msg2.mti == "0800"
        assert msg2[7] == "0302120000"
        assert msg2[11] == "000001"
        assert msg2[33] == "123456"
        assert msg2[70] == "001"
        assert msg2[100] == "999999"

    def test_with_track2(self):
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        msg[4] = "000000001000"
        msg[35] = "4987654321098769D2512"

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)
        assert msg2[35] == "4987654321098769D2512"

    def test_with_mac_field_64(self):
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        msg[4] = "000000001000"
        msg[64] = b"\xaa\xbb\xcc\xdd\x11\x22\x33\x44"

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)
        assert msg2[64] == b"\xaa\xbb\xcc\xdd\x11\x22\x33\x44"

    def test_with_mac_field_128(self):
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        msg[4] = "000000001000"
        msg[128] = b"\x00" * 8

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)
        assert msg2[128] == b"\x00" * 8
        # Secondary bitmap should have been set
        assert len(raw) > 10 + 8  # MTI + primary + secondary + fields

    def test_with_binary_variable(self):
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        msg[55] = b"\x9f\x26\x08" + b"\xAA" * 8
        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)
        assert msg2[55] == b"\x9f\x26\x08" + b"\xAA" * 8

    def test_invalid_mti_raises(self):
        msg = AS2805Message(mti="ABCD")
        msg[3] = "000000"
        with pytest.raises(AS2805BuildError):
            msg.pack()

    def test_too_short_raises(self):
        with pytest.raises(AS2805ParseError):
            AS2805Message.unpack(b"\x00\x00")

    def test_many_fields_roundtrip(self):
        """Test with many fields to exercise primary + secondary bitmap."""
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        msg[4] = "000000001000"
        msg[7] = "0302120000"
        msg[11] = "000001"
        msg[12] = "120000"
        msg[13] = "0302"
        msg[15] = "0302"
        msg[22] = "051"
        msg[25] = "00"
        msg[32] = "123456"
        msg[37] = "000000000001"
        msg[41] = "TERM0001"
        msg[42] = "MERCHANT0000001"
        msg[53] = "0000000000000001"
        msg[57] = "000000000000"
        msg[128] = b"\x00" * 8

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)

        assert msg2.mti == "0200"
        assert msg2[3] == "000000"
        assert msg2[4] == "000000001000"
        assert msg2[7] == "0302120000"
        assert msg2[11] == "000001"
        assert msg2[12] == "120000"
        assert msg2[13] == "0302"
        assert msg2[15] == "0302"
        assert msg2[22] == "051"
        assert msg2[25] == "00"
        assert msg2[32] == "123456"
        assert msg2[37] == "000000000001"
        assert msg2[41] == "TERM0001"
        assert msg2[42] == "MERCHANT0000001"
        assert msg2[53] == "0000000000000001"
        assert msg2[57] == "000000000000"
        assert msg2[128] == b"\x00" * 8


class TestMACInput:
    def test_mac_input_clears_repeat_bit(self):
        msg = AS2805Message(mti="0221")
        msg[3] = "000000"
        msg[4] = "000000001000"
        msg[64] = b"\xAA" * 8

        mac_bytes = msg.mac_input()
        # MTI should be 0220 (repeat bit cleared)
        from as2805_msg.codec import bcd_decode
        mti_in_mac = bcd_decode(mac_bytes[0:2], 4)
        assert mti_in_mac == "0220"

    def test_mac_input_excludes_mac_bytes(self):
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        msg[64] = b"\xFF" * 8

        mac_bytes = msg.mac_input()
        # Should NOT end with the MAC value
        assert not mac_bytes.endswith(b"\xFF" * 8)
        # Should NOT end with zero MAC either (it's stripped)
        assert not mac_bytes.endswith(b"\x00" * 8)

    def test_mac_input_for_0220_and_0221_same(self):
        fields = {3: "000000", 4: "000000001000", 64: b"\x00" * 8}
        msg_220 = AS2805Message(mti="0220", fields=dict(fields))
        msg_221 = AS2805Message(mti="0221", fields=dict(fields))

        assert msg_220.mac_input() == msg_221.mac_input()
