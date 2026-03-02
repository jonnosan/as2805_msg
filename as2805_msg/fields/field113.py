"""Field 113 — Payment Token Data, TLV sub-element parser.

Each sub-element: 3-byte ASCII decimal tag ID + 3-byte ASCII decimal length + value bytes.
"""

from __future__ import annotations

from ..errors import AS2805ParseError


class Field113:
    """Parse and build Field 113 TLV sub-elements."""

    @staticmethod
    def unpack(data: bytes) -> dict[str, bytes]:
        """Parse TLV sub-elements from raw field bytes.

        Returns a dict mapping tag ID strings (e.g. "001") to raw value bytes.
        """
        result: dict[str, bytes] = {}
        pos = 0
        while pos < len(data):
            if pos + 6 > len(data):
                raise AS2805ParseError(
                    f"Field 113: incomplete TLV header at offset {pos}"
                )
            tag = data[pos:pos + 3].decode("ascii")
            length_str = data[pos + 3:pos + 6].decode("ascii")
            try:
                length = int(length_str)
            except ValueError:
                raise AS2805ParseError(
                    f"Field 113: invalid length {length_str!r} for tag {tag!r}"
                )
            pos += 6
            if pos + length > len(data):
                raise AS2805ParseError(
                    f"Field 113: tag {tag!r} length {length} exceeds available data"
                )
            result[tag] = data[pos:pos + length]
            pos += length
        return result

    @staticmethod
    def pack(elements: dict[str, bytes]) -> bytes:
        """Build Field 113 content from a dict of {tag_id: value}."""
        parts: list[bytes] = []
        for tag, value in elements.items():
            tag_bytes = tag.encode("ascii")
            if len(tag_bytes) != 3:
                raise ValueError(f"Field 113 tag must be exactly 3 characters: {tag!r}")
            length_bytes = str(len(value)).zfill(3).encode("ascii")
            parts.append(tag_bytes + length_bytes + value)
        return b"".join(parts)
