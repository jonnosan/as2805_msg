"""Tests for as2805_msg.fields.field113 — Field 113 TLV parser."""

import pytest

from as2805_msg.fields import Field113
from as2805_msg.errors import AS2805ParseError


class TestField113:
    def test_single_tag(self):
        data = b"001012498765432101"
        result = Field113.unpack(data)
        assert result["001"] == b"498765432101"

    def test_multiple_tags(self):
        # Tag 001 (Funding PAN, 16 digits) + Tag 002 (Expiry, 4 digits)
        tag1 = b"0010164987654321098769"
        tag2 = b"0020042512"
        data = tag1 + tag2
        result = Field113.unpack(data)
        assert result["001"] == b"4987654321098769"
        assert result["002"] == b"2512"

    def test_pack_single(self):
        packed = Field113.pack({"001": b"4987654321098769"})
        assert packed == b"0010164987654321098769"

    def test_roundtrip(self):
        elements = {
            "001": b"4987654321098769",
            "002": b"2512",
            "180": b"01",
        }
        packed = Field113.pack(elements)
        unpacked = Field113.unpack(packed)
        assert unpacked == elements

    def test_empty_data(self):
        result = Field113.unpack(b"")
        assert result == {}

    def test_incomplete_header_raises(self):
        with pytest.raises(AS2805ParseError, match="incomplete"):
            Field113.unpack(b"001")

    def test_length_exceeds_data_raises(self):
        with pytest.raises(AS2805ParseError, match="exceeds"):
            Field113.unpack(b"001999XX")

    def test_invalid_tag_length_for_pack(self):
        with pytest.raises(ValueError, match="3 characters"):
            Field113.pack({"01": b"value"})
