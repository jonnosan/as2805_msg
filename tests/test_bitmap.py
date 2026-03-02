"""Tests for as2805_msg.bitmap — bitmap build/parse."""

import pytest

from as2805_msg.bitmap import build_bitmap, parse_bitmap
from as2805_msg.errors import AS2805BitmapError


class TestBuildBitmap:
    def test_primary_only(self):
        bm = build_bitmap([3, 4, 11])
        assert len(bm) == 8
        # Field 3 = bit 3 -> byte 0, bit 5 (counting from MSB)
        # Field 4 = bit 4 -> byte 0, bit 4
        # Field 11 = bit 11 -> byte 1, bit 5

    def test_secondary_bitmap_auto_set(self):
        bm = build_bitmap([3, 70])
        assert len(bm) == 16
        # Bit 1 of primary should be set (secondary indicator)
        assert bm[0] & 0x80 == 0x80

    def test_empty(self):
        bm = build_bitmap([])
        assert len(bm) == 8
        assert bm == b"\x00" * 8

    def test_field_1_ignored(self):
        # Field 1 is managed automatically
        bm1 = build_bitmap([3])
        bm2 = build_bitmap([1, 3])
        assert bm1 == bm2

    def test_out_of_range_raises(self):
        with pytest.raises(AS2805BitmapError):
            build_bitmap([0])
        with pytest.raises(AS2805BitmapError):
            build_bitmap([129])

    def test_field_64(self):
        bm = build_bitmap([64])
        assert len(bm) == 8
        # Field 64 = last bit of primary bitmap
        assert bm[7] & 0x01 == 0x01

    def test_field_128(self):
        bm = build_bitmap([128])
        assert len(bm) == 16
        # Field 128 = last bit of secondary bitmap
        assert bm[15] & 0x01 == 0x01


class TestParseBitmap:
    def test_roundtrip_primary(self):
        fields_in = {3, 4, 7, 11, 41, 42}
        bm = build_bitmap(fields_in)
        fields_out, consumed = parse_bitmap(bm)
        assert consumed == 8
        assert fields_out == fields_in

    def test_roundtrip_secondary(self):
        fields_in = {3, 4, 7, 11, 64, 70, 128}
        bm = build_bitmap(fields_in)
        fields_out, consumed = parse_bitmap(bm)
        assert consumed == 16
        # parse_bitmap includes field 1 (secondary indicator)
        assert fields_out == fields_in | {1}

    def test_not_enough_data_primary(self):
        with pytest.raises(AS2805BitmapError):
            parse_bitmap(b"\x00" * 7)

    def test_not_enough_data_secondary(self):
        # Primary bitmap with bit 1 set but only 8 bytes
        data = bytearray(8)
        data[0] = 0x80
        with pytest.raises(AS2805BitmapError):
            parse_bitmap(bytes(data))

    def test_offset(self):
        prefix = b"\xff\xff"
        bm = build_bitmap([3, 11])
        data = prefix + bm
        fields, consumed = parse_bitmap(data, offset=2)
        assert consumed == 8
        assert fields == {3, 11}
