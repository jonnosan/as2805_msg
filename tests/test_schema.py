"""Tests for as2805_msg.schema — field specs, encode/decode dispatch."""

import pytest

from as2805_msg.errors import AS2805FieldError
from as2805_msg.schema import (
    ELS_SCHEMA,
    FieldSchema,
    FieldSpec,
    decode_field,
    encode_field,
)


class TestFieldSchema:
    def test_get_existing(self):
        spec = ELS_SCHEMA.get(3)
        assert spec.name == "Processing Code"
        assert spec.field_type == "n"
        assert spec.max_length == 6

    def test_get_missing_raises(self):
        with pytest.raises(AS2805FieldError):
            ELS_SCHEMA.get(999)

    def test_register_custom(self):
        schema = FieldSchema()
        spec = FieldSpec(999, "Custom Field", "an", 10, "fixed")
        schema.register(spec)
        assert schema.get(999) is spec

    def test_contains(self):
        assert 3 in ELS_SCHEMA
        assert 999 not in ELS_SCHEMA


class TestEncodeDecodeFixed:
    def test_numeric_fixed(self):
        spec = ELS_SCHEMA.get(3)  # Processing Code, n6 fixed
        encoded = encode_field(spec, "000000")
        assert encoded == b"\x00\x00\x00"
        value, consumed = decode_field(spec, encoded, 0)
        assert value == "000000"
        assert consumed == 3

    def test_numeric_fixed_amount(self):
        spec = ELS_SCHEMA.get(4)  # Amount, n12 fixed
        encoded = encode_field(spec, "000000001000")
        assert len(encoded) == 6
        value, _ = decode_field(spec, encoded, 0)
        assert value == "000000001000"

    def test_alphanumeric_fixed(self):
        spec = ELS_SCHEMA.get(37)  # RRN, an12 fixed
        encoded = encode_field(spec, "000000000001")
        assert len(encoded) == 12
        value, _ = decode_field(spec, encoded, 0)
        assert value == "000000000001"

    def test_ans_fixed_padded(self):
        spec = ELS_SCHEMA.get(41)  # Terminal ID, ans8 fixed
        encoded = encode_field(spec, "TERM001")
        assert len(encoded) == 8
        assert encoded == b"TERM001 "
        value, _ = decode_field(spec, encoded, 0)
        assert value == "TERM001"

    def test_binary_fixed(self):
        spec = ELS_SCHEMA.get(52)  # PIN Data, b8 fixed
        data = b"\x12\x34\x56\x78\x9a\xbc\xde\xf0"
        encoded = encode_field(spec, data)
        assert encoded == data
        value, _ = decode_field(spec, encoded, 0)
        assert value == data

    def test_binary_wrong_length_raises(self):
        spec = ELS_SCHEMA.get(52)
        with pytest.raises(AS2805FieldError):
            encode_field(spec, b"\x00" * 4)


class TestEncodeDecodeVariable:
    def test_llvar_numeric(self):
        spec = ELS_SCHEMA.get(32)  # Acquiring Institution, n..11 LLVAR
        encoded = encode_field(spec, "123456")
        # LLVAR prefix (1 byte BCD "06") + 3 bytes BCD
        value, consumed = decode_field(spec, encoded, 0)
        assert value == "123456"
        assert consumed == len(encoded)

    def test_llvar_track2(self):
        spec = ELS_SCHEMA.get(35)  # Track 2, z..37 LLVAR
        track2 = "4987654321098769D2512"
        encoded = encode_field(spec, track2)
        value, consumed = decode_field(spec, encoded, 0)
        assert value == track2
        assert consumed == len(encoded)

    def test_lllvar_ans(self):
        spec = ELS_SCHEMA.get(47)  # Additional Data National, ans..999 LLLVAR
        text = "TCC002R2PCA0042000"
        encoded = encode_field(spec, text)
        value, consumed = decode_field(spec, encoded, 0)
        assert value == text
        assert consumed == len(encoded)

    def test_lllvar_binary(self):
        spec = ELS_SCHEMA.get(55)  # ICC Data, b..999 LLLVAR
        data = b"\x9f\x26\x08" + b"\x00" * 8
        encoded = encode_field(spec, data)
        value, consumed = decode_field(spec, encoded, 0)
        assert value == data

    def test_llvar_ans(self):
        spec = ELS_SCHEMA.get(44)  # Additional Response Data, ans..25 LLVAR
        text = "E0001"
        encoded = encode_field(spec, text)
        value, consumed = decode_field(spec, encoded, 0)
        assert value == text


class TestEncodeDecodeSignedAmounts:
    def test_x_plus_n_fixed(self):
        spec = ELS_SCHEMA.get(28)  # Amount Transaction Fee, x+n 8 fixed
        encoded = encode_field(spec, "C00001000")
        value, consumed = decode_field(spec, encoded, 0)
        assert value == "C00001000"

    def test_x_plus_n_star_fixed(self):
        spec = ELS_SCHEMA.get(58)  # Ledger Balance, x+n* 12 fixed
        encoded = encode_field(spec, "C000000010000")
        value, consumed = decode_field(spec, encoded, 0)
        # sign + 12 digits
        assert value[0] in ("C", "D", "0")
        assert len(value) == 13

    def test_x_plus_n_star_debit(self):
        spec = ELS_SCHEMA.get(58)
        encoded = encode_field(spec, "D000000010000")
        value, _ = decode_field(spec, encoded, 0)
        assert value[0] == "D"
