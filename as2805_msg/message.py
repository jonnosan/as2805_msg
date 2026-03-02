"""AS2805Message — core message pack/unpack."""

from __future__ import annotations

from typing import Any

from . import codec
from .bitmap import build_bitmap, parse_bitmap
from .errors import AS2805BuildError, AS2805FieldError, AS2805ParseError
from .schema import ELS_SCHEMA, FieldSchema, decode_field, encode_field


class AS2805Message:
    """Represents a parsed or constructed AS2805 message."""

    def __init__(self, mti: str = "0200", fields: dict[int, Any] | None = None):
        self.mti = mti
        self.fields: dict[int, Any] = dict(fields) if fields else {}

    def __getitem__(self, field: int) -> Any:
        return self.fields[field]

    def __setitem__(self, field: int, value: Any) -> None:
        self.fields[field] = value

    def __contains__(self, field: int) -> bool:
        return field in self.fields

    def __repr__(self) -> str:
        field_nums = sorted(self.fields.keys())
        return f"AS2805Message(mti={self.mti!r}, fields={field_nums})"

    @classmethod
    def unpack(cls, data: bytes, schema: FieldSchema | None = None) -> "AS2805Message":
        """Decode a message from raw bytes (excluding 2-byte length header)."""
        if schema is None:
            schema = ELS_SCHEMA

        if len(data) < 10:
            raise AS2805ParseError("Message too short (need at least MTI + bitmap)")

        pos = 0

        # MTI: 4 BCD digits = 2 bytes
        mti = codec.bcd_decode(data[pos:pos + 2], 4)
        pos += 2

        # Bitmaps
        field_numbers, bitmap_size = parse_bitmap(data, pos)
        pos += bitmap_size

        # Remove field 1 from parsing list (it's the secondary bitmap indicator)
        field_numbers.discard(1)

        fields: dict[int, Any] = {}
        for fnum in sorted(field_numbers):
            spec = schema.get(fnum)
            value, consumed = decode_field(spec, data, pos)
            fields[fnum] = value
            pos += consumed

        msg = cls(mti=mti, fields=fields)
        return msg

    def pack(self, schema: FieldSchema | None = None) -> bytes:
        """Encode the message to raw bytes (excluding 2-byte length header)."""
        if schema is None:
            schema = ELS_SCHEMA

        # MTI
        if len(self.mti) != 4 or not self.mti.isdigit():
            raise AS2805BuildError(f"Invalid MTI: {self.mti!r}")
        mti_bytes = codec.bcd_encode(self.mti, 2)

        # Encode all field data first (to determine which fields are present)
        field_data: list[tuple[int, bytes]] = []
        for fnum in sorted(self.fields.keys()):
            spec = schema.get(fnum)
            encoded = encode_field(spec, self.fields[fnum])
            field_data.append((fnum, encoded))

        # Build bitmap
        bitmap_bytes = build_bitmap(f for f, _ in field_data)

        # Assemble
        parts = [mti_bytes, bitmap_bytes]
        for _, encoded in field_data:
            parts.append(encoded)

        return b"".join(parts)

    def mac_input(self, schema: FieldSchema | None = None) -> bytes:
        """Return the bytes over which a MAC should be calculated.

        This is the packed message with:
        - The repeat bit cleared in the MTI (bit 0 of 4th digit)
        - The MAC field (64 or 128) value replaced with zeros
        - Excludes the 2-byte length header
        """
        if schema is None:
            schema = ELS_SCHEMA

        # Clear repeat bit: last digit, clear bit 0
        mti_digits = list(self.mti)
        last_digit = int(mti_digits[3])
        mti_digits[3] = str(last_digit & 0xE)  # clear bit 0
        mac_mti = "".join(mti_digits)

        # Determine which MAC field is present
        mac_field = None
        if 128 in self.fields:
            mac_field = 128
        elif 64 in self.fields:
            mac_field = 64

        # Build message with zeroed MAC
        temp = AS2805Message(mti=mac_mti, fields=dict(self.fields))
        if mac_field is not None:
            temp.fields[mac_field] = b"\x00" * 8

        raw = temp.pack(schema)

        # Strip the trailing 8 zero bytes (MAC field value)
        if mac_field is not None:
            raw = raw[:-8]

        return raw
