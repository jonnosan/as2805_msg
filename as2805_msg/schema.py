"""Field specifications and encoding/decoding dispatch for AS2805 data elements."""

from __future__ import annotations

from dataclasses import dataclass

from . import codec
from .errors import AS2805FieldError


@dataclass(frozen=True)
class FieldSpec:
    """Specification for a single AS2805 data element."""

    number: int
    name: str
    field_type: str       # "n", "an", "ans", "a", "b", "z", "x+n", "x+n*"
    max_length: int       # max digits/chars/bytes (for 'b' fields, in bytes not bits)
    length_type: str      # "fixed", "llvar", "lllvar"
    description: str = ""


class FieldSchema:
    """Registry of field specifications."""

    def __init__(self) -> None:
        self._specs: dict[int, FieldSpec] = {}

    def get(self, field_number: int) -> FieldSpec:
        spec = self._specs.get(field_number)
        if spec is None:
            raise AS2805FieldError(field_number, "No specification registered for this field")
        return spec

    def register(self, spec: FieldSpec) -> None:
        self._specs[spec.number] = spec

    def __contains__(self, field_number: int) -> bool:
        return field_number in self._specs


# ---------------------------------------------------------------------------
# Field encoding / decoding dispatch
# ---------------------------------------------------------------------------

def encode_field(spec: FieldSpec, value) -> bytes:
    """Encode a Python value into raw field bytes (without length prefix)."""
    try:
        return _encode_value(spec, value)
    except (ValueError, TypeError) as e:
        raise AS2805FieldError(spec.number, str(e)) from e


def decode_field(spec: FieldSpec, data: bytes, offset: int) -> tuple:
    """Decode a field from *data* starting at *offset*.

    Returns (python_value, bytes_consumed).
    """
    try:
        return _decode_value(spec, data, offset)
    except (ValueError, IndexError) as e:
        raise AS2805FieldError(spec.number, str(e)) from e


# ---------------------------------------------------------------------------
# Internal encode/decode by field_type
# ---------------------------------------------------------------------------

def _field_byte_length(spec: FieldSpec, num_digits_or_chars: int) -> int:
    """Compute the byte length for a given number of digits/chars."""
    ft = spec.field_type
    if ft == "n":
        return (num_digits_or_chars + 1) // 2
    if ft in ("a", "an", "ans"):
        return num_digits_or_chars
    if ft == "b":
        return num_digits_or_chars
    if ft == "z":
        return (num_digits_or_chars + 1) // 2
    if ft == "x+n":
        # 1 byte sign + BCD digits
        digits = num_digits_or_chars  # max_length includes sign position count
        return 1 + (digits + 1) // 2
    if ft == "x+n*":
        # sign nibble + digit nibbles, packed 2 per byte
        total_nibbles = 1 + num_digits_or_chars
        return (total_nibbles + 1) // 2
    raise ValueError(f"Unknown field type: {ft}")


def _read_length_prefix(spec: FieldSpec, data: bytes, offset: int) -> tuple[int, int]:
    """Read a LLVAR/LLLVAR length prefix. Returns (content_length, prefix_bytes_consumed)."""
    if spec.length_type == "llvar":
        if offset + 1 > len(data):
            raise ValueError("Not enough data for LLVAR length prefix")
        length = int(codec.bcd_decode(data[offset:offset + 1], 2))
        return length, 1
    if spec.length_type == "lllvar":
        if spec.number == 48:
            # Field 48: 3-byte ASCII length prefix
            if offset + 3 > len(data):
                raise ValueError("Not enough data for Field 48 ASCII length prefix")
            length = int(data[offset:offset + 3].decode("ascii"))
            return length, 3
        if offset + 2 > len(data):
            raise ValueError("Not enough data for LLLVAR length prefix")
        length = int(codec.bcd_decode(data[offset:offset + 2], 4))
        return length, 2
    if spec.length_type == "llllvar":
        # LLLLVAR: 4-digit BCD prefix = 2 bytes (per AS 2805.2:2025 Table I.2)
        if offset + 2 > len(data):
            raise ValueError("Not enough data for LLLLVAR length prefix")
        length = int(codec.bcd_decode(data[offset:offset + 2], 4))
        return length, 2
    raise ValueError(f"Unexpected length_type: {spec.length_type}")


def _write_length_prefix(spec: FieldSpec, content_length: int) -> bytes:
    """Write a LLVAR/LLLVAR/LLLLVAR length prefix."""
    if spec.length_type == "llvar":
        return codec.bcd_encode(str(content_length).zfill(2), 1)
    if spec.length_type == "lllvar":
        if spec.number == 48:
            return str(content_length).zfill(3).encode("ascii")
        return codec.bcd_encode(str(content_length).zfill(4), 2)
    if spec.length_type == "llllvar":
        return codec.bcd_encode(str(content_length).zfill(4), 2)
    raise ValueError(f"Unexpected length_type: {spec.length_type}")


def _encode_value(spec: FieldSpec, value) -> bytes:
    ft = spec.field_type

    if ft == "n":
        digits = str(value)
        if spec.length_type == "fixed":
            num_bytes = (spec.max_length + 1) // 2
            padded = digits.zfill(spec.max_length)
            return codec.bcd_encode(padded, num_bytes)
        else:
            # Variable length numeric
            num_bytes = (len(digits) + 1) // 2
            prefix = _write_length_prefix(spec, len(digits))
            return prefix + codec.bcd_encode(digits, num_bytes)

    if ft in ("a", "an", "ans"):
        text = str(value)
        if spec.length_type == "fixed":
            return codec.ascii_encode(text, spec.max_length)
        else:
            encoded = text.encode("ascii")
            prefix = _write_length_prefix(spec, len(encoded))
            return prefix + encoded

    if ft == "b":
        raw = bytes(value)
        if spec.length_type == "fixed":
            if len(raw) != spec.max_length:
                raise ValueError(
                    f"Binary field requires exactly {spec.max_length} bytes, got {len(raw)}"
                )
            return raw
        else:
            prefix = _write_length_prefix(spec, len(raw))
            return prefix + raw

    if ft == "z":
        text = str(value)
        num_bytes = (len(text) + 1) // 2
        if spec.length_type == "fixed":
            return codec.track2_encode(text)
        else:
            prefix = _write_length_prefix(spec, len(text))
            return prefix + codec.track2_encode(text)

    if ft == "x+n":
        text = str(value)
        sign = text[0]
        digits = text[1:]
        if spec.length_type == "fixed":
            padded = digits.zfill(spec.max_length)
            return codec.signed_amount_encode(sign, padded)
        else:
            prefix = _write_length_prefix(spec, 1 + len(digits))
            return prefix + codec.signed_amount_encode(sign, digits)

    if ft == "x+n*":
        text = str(value)
        sign = text[0]
        digits = text[1:]
        if spec.length_type == "fixed":
            padded = digits.zfill(spec.max_length)
            return codec.signed_nibble_encode(sign, padded)
        else:
            prefix = _write_length_prefix(spec, 1 + len(digits))
            return prefix + codec.signed_nibble_encode(sign, digits)

    raise ValueError(f"Unknown field type: {ft}")


def _decode_value(spec: FieldSpec, data: bytes, offset: int):
    ft = spec.field_type

    if spec.length_type == "fixed":
        return _decode_fixed(spec, data, offset)

    # Variable length: read prefix first
    content_length, prefix_size = _read_length_prefix(spec, data, offset)
    pos = offset + prefix_size

    if ft == "n":
        num_bytes = (content_length + 1) // 2
        value = codec.bcd_decode(data[pos:pos + num_bytes], content_length)
        return value, prefix_size + num_bytes

    if ft in ("a", "an", "ans"):
        value = data[pos:pos + content_length].decode("ascii")
        return value, prefix_size + content_length

    if ft == "b":
        value = bytes(data[pos:pos + content_length])
        return value, prefix_size + content_length

    if ft == "z":
        num_bytes = (content_length + 1) // 2
        value = codec.track2_decode(data[pos:pos + num_bytes], content_length)
        return value, prefix_size + num_bytes

    raise ValueError(f"Unknown variable-length field type: {ft}")


def _decode_fixed(spec: FieldSpec, data: bytes, offset: int):
    ft = spec.field_type

    if ft == "n":
        num_bytes = (spec.max_length + 1) // 2
        value = codec.bcd_decode(data[offset:offset + num_bytes], spec.max_length)
        return value, num_bytes

    if ft in ("a", "an", "ans"):
        value = codec.ascii_decode(data[offset:offset + spec.max_length])
        return value, spec.max_length

    if ft == "b":
        value = bytes(data[offset:offset + spec.max_length])
        return value, spec.max_length

    if ft == "z":
        num_bytes = (spec.max_length + 1) // 2
        value = codec.track2_decode(data[offset:offset + num_bytes], spec.max_length)
        return value, num_bytes

    if ft == "x+n":
        # 1 byte ASCII sign + BCD digits
        num_digit_bytes = (spec.max_length + 1) // 2
        total = 1 + num_digit_bytes
        sign, digits = codec.signed_amount_decode(data[offset:offset + total])
        # Ensure digit count matches
        digits = digits[-spec.max_length:]
        return sign + digits, total

    if ft == "x+n*":
        # sign nibble + digit nibbles
        total_nibbles = 1 + spec.max_length
        num_bytes = (total_nibbles + 1) // 2
        sign, digits = codec.signed_nibble_decode(data[offset:offset + num_bytes])
        digits = digits[-spec.max_length:]
        return sign + digits, num_bytes

    raise ValueError(f"Unknown fixed field type: {ft}")


# ---------------------------------------------------------------------------
# Default eLS schema
# ---------------------------------------------------------------------------

def _build_els_schema() -> FieldSchema:
    schema = FieldSchema()
    _defs = [
        # (number, name, type, max_length, length_type)
        (1,   "Bitmap, Secondary",                    "b",    8,   "fixed"),
        (2,   "Primary Account Number",               "n",   19,   "llvar"),
        (3,   "Processing Code",                      "n",    6,   "fixed"),
        (4,   "Amount, Transaction",                  "n",   12,   "fixed"),
        (7,   "Transmission Date & Time",             "n",   10,   "fixed"),
        (11,  "Systems Trace Audit Number",           "n",    6,   "fixed"),
        (12,  "Time, Local Transaction",              "n",    6,   "fixed"),
        (13,  "Date, Local Transaction",              "n",    4,   "fixed"),
        (14,  "Expiry Date",                          "n",    4,   "fixed"),
        (15,  "Date, Settlement",                     "n",    4,   "fixed"),
        (18,  "Merchant Type",                        "n",    4,   "fixed"),
        (22,  "POS Entry Mode",                       "n",    3,   "fixed"),
        (23,  "Card Sequence Number",                 "n",    3,   "fixed"),
        (25,  "POS Condition Code",                   "n",    2,   "fixed"),
        (28,  "Amount, Transaction Fee",              "x+n",  8,   "fixed"),
        (30,  "Amount, Transaction Processing Fee",   "x+n",  8,   "fixed"),
        (32,  "Acquiring Institution ID Code",        "n",   11,   "llvar"),
        (33,  "Forwarding Institution ID Code",       "n",   11,   "llvar"),
        (35,  "Track 2 Data",                         "z",   37,   "llvar"),
        (37,  "Retrieval Reference Number",           "an",  12,   "fixed"),
        (38,  "Authorisation ID Response",            "an",   6,   "fixed"),
        (39,  "Response Code",                        "an",   2,   "fixed"),
        (41,  "Card Acceptor Terminal ID",            "ans",  8,   "fixed"),
        (42,  "Card Acceptor Identification Code",    "ans", 15,   "fixed"),
        (43,  "Card Acceptor Name/Location",          "ans", 40,   "fixed"),
        (44,  "Additional Response Data",             "ans", 25,   "llvar"),
        (47,  "Additional Data - National",           "ans", 999,  "lllvar"),
        (48,  "Additional Data - Private",            "ans", 999,  "lllvar"),
        (52,  "PIN Data",                             "b",    8,   "fixed"),
        (53,  "Security Related Control Information", "n",   16,   "fixed"),
        (54,  "Additional Amounts",                   "an",  120,  "lllvar"),
        (55,  "ICC Related Data",                     "b",   999,  "lllvar"),
        (57,  "Amount, Cash",                         "n",   12,   "fixed"),
        (58,  "Ledger Balance",                       "x+n*", 12,  "fixed"),
        (59,  "Account Balance, Cleared Funds",       "x+n*", 12,  "fixed"),
        (64,  "Message Authentication Code",          "b",    8,   "fixed"),
        (66,  "Settlement Code",                      "n",    1,   "fixed"),
        (70,  "Network Management Information Code",  "n",    3,   "fixed"),
        (90,  "Original Data Elements",               "n",   42,   "fixed"),
        (95,  "Replacement Amounts",                  "an",  42,   "fixed"),
        (100, "Receiving Institution ID Code",        "n",   11,   "llvar"),
        (111, "Encryption Data",                       "b",  9999,  "llllvar"),
        (113, "Payment Token Data",                   "b",   999,  "lllvar"),
        (128, "Message Authentication Code",          "b",    8,   "fixed"),
    ]
    for num, name, ft, ml, lt in _defs:
        schema.register(FieldSpec(num, name, ft, ml, lt))
    return schema


ELS_SCHEMA = _build_els_schema()
