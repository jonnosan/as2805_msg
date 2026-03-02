"""Tests for as2805_msg.fields.field48 — session key data parser."""

from as2805_msg import Field48


class TestField48Unpack:
    def test_session_keys_32_bytes(self):
        ppk = b"\x01" * 16
        mak = b"\x02" * 16
        result = Field48.unpack(ppk + mak)
        assert result["ppk"] == ppk
        assert result["mak"] == mak

    def test_other_length_raw(self):
        data = b"\xAB\xCD\xEF"
        result = Field48.unpack(data)
        assert result["raw"] == data

    def test_empty_returns_empty_dict(self):
        result = Field48.unpack(b"")
        assert result == {}


class TestField48Pack:
    def test_pack_ppk_mak(self):
        ppk = b"\x01" * 16
        mak = b"\x02" * 16
        result = Field48.pack({"ppk": ppk, "mak": mak})
        assert result == ppk + mak

    def test_pack_raw(self):
        data = b"\xAB\xCD"
        result = Field48.pack({"raw": data})
        assert result == data

    def test_pack_random(self):
        random_data = b"\x99" * 8
        result = Field48.pack({"random": random_data})
        assert result == random_data

    def test_roundtrip(self):
        ppk = bytes(range(16))
        mak = bytes(range(16, 32))
        packed = Field48.pack({"ppk": ppk, "mak": mak})
        unpacked = Field48.unpack(packed)
        assert unpacked["ppk"] == ppk
        assert unpacked["mak"] == mak
