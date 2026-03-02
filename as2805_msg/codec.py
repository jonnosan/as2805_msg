"""Low-level encoding/decoding primitives for AS2805 field types."""

from __future__ import annotations


def bcd_encode(digits: str, num_bytes: int) -> bytes:
    """Encode a decimal digit string as BCD-packed bytes.

    Odd-length digit strings are left-padded with '0' before packing.
    ``num_bytes`` is the number of output bytes expected.
    """
    if not all(c in "0123456789" for c in digits):
        raise ValueError(f"Non-digit character in BCD input: {digits!r}")
    # Pad to even length matching num_bytes * 2 nibbles
    padded = digits.zfill(num_bytes * 2)
    result = bytearray(num_bytes)
    for i in range(num_bytes):
        high = int(padded[i * 2])
        low = int(padded[i * 2 + 1])
        result[i] = (high << 4) | low
    return bytes(result)


def bcd_decode(data: bytes, num_digits: int | None = None) -> str:
    """Decode BCD-packed bytes to a decimal digit string.

    If ``num_digits`` is given, the result is right-justified (leading zeros
    from left-padding are stripped to that count).
    """
    digits = []
    for b in data:
        digits.append(str((b >> 4) & 0x0F))
        digits.append(str(b & 0x0F))
    result = "".join(digits)
    if num_digits is not None:
        # Take the rightmost num_digits
        result = result[-num_digits:] if num_digits <= len(result) else result.zfill(num_digits)
    return result


def ascii_encode(text: str, length: int, pad: str = " ") -> bytes:
    """Encode a string as fixed-length ASCII, right-padded with ``pad``."""
    if len(text) > length:
        raise ValueError(f"Text {text!r} exceeds max length {length}")
    return text.ljust(length, pad).encode("ascii")


def ascii_decode(data: bytes) -> str:
    """Decode ASCII bytes, stripping trailing spaces."""
    return data.decode("ascii").rstrip(" ")


def track2_encode(data: str) -> bytes:
    """Encode track 2 data (digits 0-9 and separator 'D'), 2 symbols per byte."""
    data_upper = data.upper()
    if not all(c in "0123456789D" for c in data_upper):
        raise ValueError(f"Invalid track 2 character in: {data!r}")
    # Pad to even length
    symbols = data_upper
    if len(symbols) % 2 != 0:
        symbols += "0"
    result = bytearray()
    for i in range(0, len(symbols), 2):
        high = 0x0D if symbols[i] == "D" else int(symbols[i])
        low = 0x0D if symbols[i + 1] == "D" else int(symbols[i + 1])
        result.append((high << 4) | low)
    return bytes(result)


def track2_decode(data: bytes, num_symbols: int) -> str:
    """Decode track 2 data bytes to a string of digits and 'D' separators."""
    symbols = []
    for b in data:
        high = (b >> 4) & 0x0F
        low = b & 0x0F
        symbols.append("D" if high == 0x0D else str(high))
        symbols.append("D" if low == 0x0D else str(low))
    return "".join(symbols[:num_symbols])


def signed_amount_encode(sign: str, digits: str) -> bytes:
    """Encode x+n field: ASCII 'C' or 'D' prefix + BCD-packed digits."""
    if sign not in ("C", "D"):
        raise ValueError(f"Sign must be 'C' or 'D', got {sign!r}")
    num_bytes = (len(digits) + 1) // 2
    return sign.encode("ascii") + bcd_encode(digits, num_bytes)


def signed_amount_decode(data: bytes) -> tuple[str, str]:
    """Decode x+n field. Returns (sign, digit_string)."""
    sign = chr(data[0])
    if sign not in ("C", "D"):
        raise ValueError(f"Invalid sign byte: 0x{data[0]:02x}")
    digits = bcd_decode(data[1:])
    return sign, digits


def signed_nibble_encode(sign: str, digits: str) -> bytes:
    """Encode x+n* field: first nibble is sign (0/C/D), rest are BCD digits."""
    sign_map = {"0": 0x0, "C": 0xC, "D": 0xD}
    if sign not in sign_map:
        raise ValueError(f"Sign must be '0', 'C', or 'D', got {sign!r}")
    # Total nibbles = 1 (sign) + len(digits)
    all_nibbles = [sign_map[sign]] + [int(d) for d in digits]
    # Pad to even number of nibbles
    if len(all_nibbles) % 2 != 0:
        all_nibbles.append(0)
    result = bytearray()
    for i in range(0, len(all_nibbles), 2):
        result.append((all_nibbles[i] << 4) | all_nibbles[i + 1])
    return bytes(result)


def signed_nibble_decode(data: bytes) -> tuple[str, str]:
    """Decode x+n* field. Returns (sign, digit_string).

    Sign is '0', 'C', or 'D'.
    """
    first_nibble = (data[0] >> 4) & 0x0F
    sign_map = {0x0: "0", 0xC: "C", 0xD: "D"}
    sign = sign_map.get(first_nibble)
    if sign is None:
        raise ValueError(f"Invalid sign nibble: 0x{first_nibble:x}")
    # Remaining nibbles are digits
    nibbles = []
    nibbles.append(str(data[0] & 0x0F))
    for b in data[1:]:
        nibbles.append(str((b >> 4) & 0x0F))
        nibbles.append(str(b & 0x0F))
    # The total digit count = (num_bytes * 2) - 1 (sign nibble)
    digit_str = "".join(nibbles)
    return sign, digit_str
