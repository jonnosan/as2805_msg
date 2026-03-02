"""Field 55 — ICC Related Data, BER-TLV parser.

Implements parsing and building of BER-TLV structures per ISO/IEC 7816 / X.690.
"""

from __future__ import annotations

from ..errors import AS2805ParseError


class Field55:
    """Parse and build Field 55 BER-TLV data."""

    @staticmethod
    def unpack(data: bytes) -> dict[bytes, bytes]:
        """Parse BER-TLV encoded data.

        Returns a dict mapping tag bytes to value bytes.
        """
        result: dict[bytes, bytes] = {}
        pos = 0
        while pos < len(data):
            tag, pos = _read_tag(data, pos)
            length, pos = _read_length(data, pos)
            if pos + length > len(data):
                raise AS2805ParseError(
                    f"Field 55: tag {tag.hex()} length {length} exceeds data"
                )
            value = data[pos:pos + length]
            result[tag] = value
            pos += length
        return result

    @staticmethod
    def pack(elements: dict[bytes, bytes]) -> bytes:
        """Build BER-TLV encoded data from {tag: value}."""
        parts: list[bytes] = []
        for tag, value in elements.items():
            parts.append(tag)
            parts.append(_encode_length(len(value)))
            parts.append(value)
        return b"".join(parts)


def _read_tag(data: bytes, pos: int) -> tuple[bytes, int]:
    """Read a BER-TLV tag. Returns (tag_bytes, new_pos)."""
    if pos >= len(data):
        raise AS2805ParseError("Field 55: unexpected end of data reading tag")
    first = data[pos]
    # Check if multi-byte tag: low 5 bits of first byte all set
    if (first & 0x1F) == 0x1F:
        # Multi-byte tag
        end = pos + 1
        while end < len(data):
            if (data[end] & 0x80) == 0:
                end += 1
                break
            end += 1
        else:
            raise AS2805ParseError("Field 55: unterminated multi-byte tag")
        return bytes(data[pos:end]), end
    return bytes([first]), pos + 1


def _read_length(data: bytes, pos: int) -> tuple[int, int]:
    """Read a BER-TLV length. Returns (length_value, new_pos)."""
    if pos >= len(data):
        raise AS2805ParseError("Field 55: unexpected end of data reading length")
    first = data[pos]
    if first < 0x80:
        return first, pos + 1
    if first == 0x80:
        raise AS2805ParseError("Field 55: indefinite length not supported")
    num_bytes = first & 0x7F
    if pos + 1 + num_bytes > len(data):
        raise AS2805ParseError("Field 55: not enough data for multi-byte length")
    length = 0
    for i in range(num_bytes):
        length = (length << 8) | data[pos + 1 + i]
    return length, pos + 1 + num_bytes


def _encode_length(length: int) -> bytes:
    """Encode a BER-TLV length."""
    if length < 0x80:
        return bytes([length])
    # Determine number of bytes needed
    temp = length
    num_bytes = 0
    while temp > 0:
        temp >>= 8
        num_bytes += 1
    result = bytearray([0x80 | num_bytes])
    for i in range(num_bytes - 1, -1, -1):
        result.append((length >> (i * 8)) & 0xFF)
    return bytes(result)
