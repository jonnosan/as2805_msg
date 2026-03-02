"""Tests for as2805_msg.fields.field47 — Field 47 backslash-delimited parser."""

import pytest

from as2805_msg.fields import Field47
from as2805_msg.errors import AS2805ParseError


class TestField47:
    def test_single_tag(self):
        data = b"TCCR2\\"
        result = Field47.unpack(data)
        assert result == {"TCC": b"R2"}

    def test_multiple_tags(self):
        data = b"TCCR2\\PCA2000\\FCA01\\"
        result = Field47.unpack(data)
        assert result["TCC"] == b"R2"
        assert result["PCA"] == b"2000"
        assert result["FCA"] == b"01"

    def test_pack_single(self):
        packed = Field47.pack({"TCC": b"R2"})
        assert packed == b"TCCR2\\"

    def test_pack_multiple(self):
        elements = {"TCC": b"R2", "PCA": b"2000"}
        packed = Field47.pack(elements)
        # Verify round-trip
        result = Field47.unpack(packed)
        assert result["TCC"] == b"R2"
        assert result["PCA"] == b"2000"

    def test_roundtrip(self):
        elements = {"ARI": b"Y01", "TCC": b"R2", "FCR": b"N", "PCA": b"2000"}
        packed = Field47.pack(elements)
        unpacked = Field47.unpack(packed)
        assert unpacked == elements

    def test_empty_data(self):
        result = Field47.unpack(b"")
        assert result == {}

    def test_incomplete_tag_raises(self):
        with pytest.raises(AS2805ParseError, match="incomplete"):
            Field47.unpack(b"TC")

    def test_no_trailing_backslash(self):
        """Value without trailing backslash — treat remainder as value."""
        data = b"TCCR2"
        result = Field47.unpack(data)
        assert result == {"TCC": b"R2"}

    def test_invalid_tag_length_for_pack(self):
        with pytest.raises(ValueError, match="3 characters"):
            Field47.pack({"TC": b"R2"})

    def test_empty_value(self):
        packed = Field47.pack({"TCC": b""})
        assert packed == b"TCC\\"
        result = Field47.unpack(packed)
        assert result["TCC"] == b""
