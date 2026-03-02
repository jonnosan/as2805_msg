"""Tests for as2805_msg.fields.field90 — Field 90 composite sub-fields."""

import pytest

from as2805_msg.fields import Field90


class TestField90:
    def test_unpack(self):
        value = "0200" + "000001" + "0302120000" + "00000123456" + "00000000000"
        result = Field90.unpack(value)
        assert result["mti"] == "0200"
        assert result["stan"] == "000001"
        assert result["transmission_dt"] == "0302120000"
        assert result["acq_inst"] == "00000123456"
        assert result["fwd_inst"] == "00000000000"

    def test_pack(self):
        elements = {
            "mti": "0200",
            "stan": "000001",
            "transmission_dt": "0302120000",
            "acq_inst": "123456",
            "fwd_inst": "0",
        }
        result = Field90.pack(elements)
        assert len(result) == 42
        assert result[:4] == "0200"
        assert result[4:10] == "000001"
        assert result[10:20] == "0302120000"
        # acq_inst zero-padded to 11 digits
        assert result[20:31] == "00000123456"
        # fwd_inst zero-padded to 11 digits
        assert result[31:42] == "00000000000"

    def test_roundtrip(self):
        original = {
            "mti": "0200",
            "stan": "000001",
            "transmission_dt": "0302120000",
            "acq_inst": "12345678901",
            "fwd_inst": "98765432109",
        }
        packed = Field90.pack(original)
        unpacked = Field90.unpack(packed)
        assert unpacked["mti"] == "0200"
        assert unpacked["stan"] == "000001"
        assert unpacked["transmission_dt"] == "0302120000"
        assert unpacked["acq_inst"] == "12345678901"
        assert unpacked["fwd_inst"] == "98765432109"

    def test_wrong_length_raises(self):
        with pytest.raises(ValueError, match="42 digits"):
            Field90.unpack("0200000001")

    def test_all_zeros(self):
        value = "0" * 42
        result = Field90.unpack(value)
        assert result["mti"] == "0000"
        assert result["stan"] == "000000"
