"""Tests for as2805_msg.codec — low-level encoding primitives."""

import pytest

from as2805_msg.codec import (
    ascii_decode,
    ascii_encode,
    bcd_decode,
    bcd_encode,
    signed_amount_decode,
    signed_amount_encode,
    signed_nibble_decode,
    signed_nibble_encode,
    track2_decode,
    track2_encode,
)


# ---------------------------------------------------------------------------
# BCD
# ---------------------------------------------------------------------------

class TestBCDEncode:
    def test_even_digits(self):
        assert bcd_encode("1234", 2) == b"\x12\x34"

    def test_odd_digits_left_padded(self):
        assert bcd_encode("123", 2) == b"\x01\x23"

    def test_single_digit(self):
        assert bcd_encode("5", 1) == b"\x05"

    def test_zeros(self):
        assert bcd_encode("000000", 3) == b"\x00\x00\x00"

    def test_non_digit_raises(self):
        with pytest.raises(ValueError, match="Non-digit"):
            bcd_encode("12A4", 2)

    def test_long_number(self):
        assert bcd_encode("0302120000", 5) == b"\x03\x02\x12\x00\x00"


class TestBCDDecode:
    def test_even(self):
        assert bcd_decode(b"\x12\x34") == "1234"

    def test_with_num_digits_odd(self):
        assert bcd_decode(b"\x01\x23", 3) == "123"

    def test_with_num_digits_even(self):
        assert bcd_decode(b"\x12\x34", 4) == "1234"

    def test_single_byte(self):
        assert bcd_decode(b"\x05", 1) == "5"

    def test_roundtrip(self):
        for digits in ["0", "12", "123", "1234", "0302120000", "999999999999"]:
            num_bytes = (len(digits) + 1) // 2
            assert bcd_decode(bcd_encode(digits, num_bytes), len(digits)) == digits


# ---------------------------------------------------------------------------
# ASCII
# ---------------------------------------------------------------------------

class TestASCIIEncode:
    def test_exact_length(self):
        assert ascii_encode("HELLO", 5) == b"HELLO"

    def test_right_padded(self):
        assert ascii_encode("HI", 5) == b"HI   "

    def test_exceeds_length_raises(self):
        with pytest.raises(ValueError, match="exceeds"):
            ascii_encode("TOOLONG", 3)


class TestASCIIDecode:
    def test_strips_trailing_spaces(self):
        assert ascii_decode(b"HI   ") == "HI"

    def test_no_trailing_spaces(self):
        assert ascii_decode(b"HELLO") == "HELLO"

    def test_all_spaces(self):
        assert ascii_decode(b"     ") == ""


# ---------------------------------------------------------------------------
# Track 2
# ---------------------------------------------------------------------------

class TestTrack2Encode:
    def test_with_separator(self):
        result = track2_encode("4987654321098769D2512")
        # 21 symbols -> 11 bytes (padded to 22 nibbles)
        assert len(result) == 11
        # First nibble = 4, second = 9
        assert result[0] == 0x49

    def test_even_length(self):
        result = track2_encode("1234D5678")
        # 9 symbols -> padded to 10 -> 5 bytes
        assert len(result) == 5

    def test_invalid_char_raises(self):
        with pytest.raises(ValueError, match="Invalid track 2"):
            track2_encode("1234X5678")


class TestTrack2Decode:
    def test_with_separator(self):
        encoded = track2_encode("4987654321098769D2512")
        assert track2_decode(encoded, 21) == "4987654321098769D2512"

    def test_roundtrip(self):
        for data in ["1234D5678", "4987654321098769D25120001234"]:
            encoded = track2_encode(data)
            assert track2_decode(encoded, len(data)) == data


# ---------------------------------------------------------------------------
# Signed amount (x+n)
# ---------------------------------------------------------------------------

class TestSignedAmount:
    def test_credit_encode(self):
        result = signed_amount_encode("C", "00001000")
        assert result == b"C" + bcd_encode("00001000", 4)

    def test_debit_encode(self):
        result = signed_amount_encode("D", "00001000")
        assert result[0:1] == b"D"

    def test_invalid_sign_raises(self):
        with pytest.raises(ValueError, match="Sign must be"):
            signed_amount_encode("X", "1234")

    def test_roundtrip(self):
        for sign, digits in [("C", "00000000"), ("D", "00001000"), ("C", "99999999")]:
            encoded = signed_amount_encode(sign, digits)
            dec_sign, dec_digits = signed_amount_decode(encoded)
            assert dec_sign == sign
            assert dec_digits == digits


# ---------------------------------------------------------------------------
# Signed nibble (x+n*)
# ---------------------------------------------------------------------------

class TestSignedNibble:
    def test_credit_encode(self):
        result = signed_nibble_encode("C", "00000001000")
        # First nibble = 0xC, then 11 digit nibbles = 12 total nibbles = 6 bytes
        assert len(result) == 6
        assert (result[0] >> 4) == 0xC

    def test_debit_encode(self):
        result = signed_nibble_encode("D", "00000001000")
        assert (result[0] >> 4) == 0xD

    def test_unsigned_encode(self):
        result = signed_nibble_encode("0", "00000001000")
        assert (result[0] >> 4) == 0x0

    def test_roundtrip(self):
        for sign, digits in [("0", "00000000000"), ("C", "00000001000"), ("D", "99999999999")]:
            encoded = signed_nibble_encode(sign, digits)
            dec_sign, dec_digits = signed_nibble_decode(encoded)
            assert dec_sign == sign
            assert dec_digits == digits
