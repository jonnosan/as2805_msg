"""Field 47 — Additional Data National, backslash-delimited sub-element parser.

Each sub-element: 3-byte ASCII tag + variable-length value + backslash delimiter.
Example: ``TCC R2\\PCA2000\\``
"""

from __future__ import annotations

from ..errors import AS2805ParseError


class Field47:
    """Parse and build Field 47 backslash-delimited sub-elements."""

    @staticmethod
    def unpack(data: bytes) -> dict[str, bytes]:
        r"""Parse sub-elements from raw field bytes.

        Format: TAG(3 bytes) + VALUE(variable) + ``\`` separator, repeated.

        Returns a dict mapping tag ID strings to raw value bytes.
        """
        result: dict[str, bytes] = {}
        pos = 0
        while pos < len(data):
            if pos + 3 > len(data):
                raise AS2805ParseError(
                    f"Field 47: incomplete tag at offset {pos}"
                )
            tag = data[pos:pos + 3].decode("ascii")
            pos += 3
            # Find the next backslash delimiter
            sep = data.find(ord("\\"), pos)
            if sep == -1:
                # No trailing backslash — treat remainder as value
                result[tag] = data[pos:]
                break
            result[tag] = data[pos:sep]
            pos = sep + 1  # skip past the backslash
        return result

    @staticmethod
    def pack(elements: dict[str, bytes]) -> bytes:
        r"""Build Field 47 content from a dict of {tag: value}.

        Each element is encoded as TAG(3 bytes) + VALUE + ``\``.
        """
        parts: list[bytes] = []
        for tag, value in elements.items():
            tag_bytes = tag.encode("ascii")
            if len(tag_bytes) != 3:
                raise ValueError(f"Field 47 tag must be exactly 3 characters: {tag!r}")
            parts.append(tag_bytes + value + b"\\")
        return b"".join(parts)
