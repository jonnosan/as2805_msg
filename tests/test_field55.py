"""Tests for as2805_msg.fields.field55 — Field 55 BER-TLV parser."""

import pytest

from as2805_msg.fields import Field55
from as2805_msg.errors import AS2805ParseError


class TestField55:
    def test_single_byte_tag_short_length(self):
        # Tag 0x82 (AIP), length 2, value 0x1980
        data = b"\x82\x02\x19\x80"
        result = Field55.unpack(data)
        assert result[b"\x82"] == b"\x19\x80"

    def test_two_byte_tag(self):
        # Tag 9F26 (Application Cryptogram), length 8
        cryptogram = b"\x11\x22\x33\x44\x55\x66\x77\x88"
        data = b"\x9f\x26\x08" + cryptogram
        result = Field55.unpack(data)
        assert result[b"\x9f\x26"] == cryptogram

    def test_multiple_tags(self):
        tag1 = b"\x9f\x26\x08" + b"\xAA" * 8   # 9F26, len 8
        tag2 = b"\x9f\x27\x01\x80"              # 9F27, len 1, val 0x80
        tag3 = b"\x82\x02\x19\x80"              # 82, len 2
        data = tag1 + tag2 + tag3
        result = Field55.unpack(data)
        assert len(result) == 3
        assert result[b"\x9f\x26"] == b"\xAA" * 8
        assert result[b"\x9f\x27"] == b"\x80"
        assert result[b"\x82"] == b"\x19\x80"

    def test_long_form_length(self):
        # Tag with length > 127 (uses long form)
        value = b"\x00" * 200
        data = b"\x9f\x10" + b"\x81\xc8" + value  # 0x81 = long form, 1 byte follows, 0xC8 = 200
        result = Field55.unpack(data)
        assert len(result[b"\x9f\x10"]) == 200

    def test_pack_single(self):
        packed = Field55.pack({b"\x82": b"\x19\x80"})
        assert packed == b"\x82\x02\x19\x80"

    def test_pack_two_byte_tag(self):
        packed = Field55.pack({b"\x9f\x26": b"\x11\x22\x33\x44"})
        assert packed == b"\x9f\x26\x04\x11\x22\x33\x44"

    def test_roundtrip(self):
        elements = {
            b"\x9f\x26": b"\xAA" * 8,
            b"\x9f\x27": b"\x80",
            b"\x82": b"\x19\x80",
            b"\x9f\x10": b"\xBB" * 32,
        }
        packed = Field55.pack(elements)
        unpacked = Field55.unpack(packed)
        assert unpacked == elements

    def test_empty_data(self):
        result = Field55.unpack(b"")
        assert result == {}

    def test_truncated_tag_raises(self):
        with pytest.raises(AS2805ParseError):
            Field55.unpack(b"\x9f")  # Multi-byte tag, but no second byte

    def test_length_exceeds_data_raises(self):
        with pytest.raises(AS2805ParseError, match="exceeds"):
            Field55.unpack(b"\x82\x10\x00\x00")  # Says length 16, only 2 bytes

    def test_pack_long_form_length(self):
        value = b"\x00" * 200
        packed = Field55.pack({b"\x9f\x10": value})
        unpacked = Field55.unpack(packed)
        assert unpacked[b"\x9f\x10"] == value

    def test_zero_length_value(self):
        packed = Field55.pack({b"\x82": b""})
        assert packed == b"\x82\x00"
        result = Field55.unpack(packed)
        assert result[b"\x82"] == b""
