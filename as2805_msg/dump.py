"""Hex dump and wire-level debug utilities for AS2805 messages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .bitmap import parse_bitmap
from .schema import ELS_SCHEMA, FieldSchema, decode_field

if TYPE_CHECKING:
    from . import codec


def dump(msg, schema: FieldSchema | None = None) -> str:
    """Produce a detailed field-by-field view of a message.

    Each line shows the field number, name, type spec, raw hex, and decoded value.
    """
    if schema is None:
        schema = ELS_SCHEMA

    lines: list[str] = []
    lines.append(f"MTI: {msg.mti}")
    lines.append(f"Fields: {sorted(msg.fields.keys())}")
    lines.append("")

    for fnum in sorted(msg.fields.keys()):
        value = msg.fields[fnum]
        if fnum in schema:
            spec = schema.get(fnum)
            name = spec.name
            type_desc = f"{spec.field_type} {spec.max_length} {spec.length_type}"
        else:
            name = f"Field {fnum:03d}"
            type_desc = "?"

        if isinstance(value, bytes):
            hex_str = value.hex(" ")
            val_str = f"({len(value)} bytes)"
        else:
            val_str = repr(value)
            hex_str = ""

        if hex_str:
            lines.append(f"  [{fnum:03d}] {name:<40s} {type_desc:<18s} [{hex_str}] {val_str}")
        else:
            lines.append(f"  [{fnum:03d}] {name:<40s} {type_desc:<18s} {val_str}")

    return "\n".join(lines)


def dump_raw(data: bytes) -> str:
    """Classic hex dump of raw bytes with offset, hex, and ASCII columns.

    Output format::

        00000000  02 00 30 20 05 80 20 c0  00 04 00 00 00 ...  |..0 .. ........|
    """
    lines: list[str] = []
    for offset in range(0, len(data), 16):
        chunk = data[offset:offset + 16]
        hex_parts = []
        for i, b in enumerate(chunk):
            hex_parts.append(f"{b:02x}")
            if i == 7:
                hex_parts.append("")  # extra space at midpoint

        hex_col = " ".join(hex_parts)
        # Pad hex column to fixed width (49 chars for 16 bytes with midpoint gap)
        hex_col = hex_col.ljust(49)

        ascii_col = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

        lines.append(f"{offset:08x}  {hex_col}  |{ascii_col}|")

    return "\n".join(lines)
