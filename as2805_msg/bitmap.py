"""AS2805 primary and secondary bitmap operations."""

from __future__ import annotations

from collections.abc import Iterable

from .errors import AS2805BitmapError


def build_bitmap(fields: Iterable[int]) -> bytes:
    """Build primary (and secondary if needed) bitmap bytes from field numbers.

    Field numbers are 1-128.  Bit 1 of the primary bitmap is automatically
    set when any field > 64 is present (indicating secondary bitmap).

    Returns 8 bytes (primary only) or 16 bytes (primary + secondary).
    """
    field_set = set(fields)
    # Field 1 (secondary bitmap indicator) is managed automatically
    field_set.discard(1)

    need_secondary = any(f > 64 for f in field_set)

    primary = bytearray(8)
    secondary = bytearray(8)

    if need_secondary:
        # Set bit 1 of primary bitmap
        primary[0] |= 0x80

    for f in field_set:
        if f < 1 or f > 128:
            raise AS2805BitmapError(f"Field number {f} out of range 1-128")
        if f <= 64:
            byte_idx = (f - 1) // 8
            bit_idx = 7 - ((f - 1) % 8)
            primary[byte_idx] |= (1 << bit_idx)
        else:
            adj = f - 65
            byte_idx = adj // 8
            bit_idx = 7 - (adj % 8)
            secondary[byte_idx] |= (1 << bit_idx)

    if need_secondary:
        return bytes(primary) + bytes(secondary)
    return bytes(primary)


def parse_bitmap(data: bytes, offset: int = 0) -> tuple[set[int], int]:
    """Parse bitmap bytes starting at ``offset``.

    Returns (set of field numbers present, number of bytes consumed).
    Field 1 is included in the result if the secondary bitmap is present.
    """
    if offset + 8 > len(data):
        raise AS2805BitmapError("Not enough data for primary bitmap")

    fields: set[int] = set()
    consumed = 8

    # Parse primary bitmap (fields 1-64)
    for i in range(64):
        byte_idx = i // 8
        bit_idx = 7 - (i % 8)
        if data[offset + byte_idx] & (1 << bit_idx):
            fields.add(i + 1)

    # Check for secondary bitmap (bit 1)
    if 1 in fields:
        if offset + 16 > len(data):
            raise AS2805BitmapError("Not enough data for secondary bitmap")
        consumed = 16
        for i in range(64):
            byte_idx = i // 8
            bit_idx = 7 - (i % 8)
            if data[offset + 8 + byte_idx] & (1 << bit_idx):
                fields.add(65 + i)

    return fields, consumed
