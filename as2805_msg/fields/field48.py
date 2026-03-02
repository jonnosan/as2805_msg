"""Field 48 — Additional Data Private, session key exchange parser.

Field 48 carries encrypted data for network management (sign-on proof-of-endpoint,
session key exchange). The content is raw binary — not restricted to printable ASCII
despite the field's ``ans`` type designation.

For sign-on (0800/0810): contains an encrypted random value for proof-of-endpoint.
For key change (0820): contains encrypted session keys (PIN Protect + MAC keys).

The wire-level 3-byte ASCII length prefix is handled by schema.py; this module
parses the *content* of the field.
"""

from __future__ import annotations

from ..errors import AS2805ParseError


class Field48:
    """Parse and build Field 48 content.

    The field content is treated as opaque binary data since it contains
    encrypted key material. This parser provides a structured view of the
    key blocks when the format is known.
    """

    @staticmethod
    def unpack(data: bytes) -> dict[str, bytes]:
        """Parse Field 48 content.

        For sign-on messages, the data is a single encrypted random value.
        For key change messages, the data contains two key blocks
        (PIN Protect Key + MAC Key), each 16 bytes (double-length 3DES).

        Returns a dict with context-dependent keys:
        - Single block: {"random": <bytes>}
        - Two key blocks (32 bytes): {"ppk": <first 16 bytes>, "mak": <last 16 bytes>}
        - Other: {"raw": <bytes>}
        """
        if len(data) == 32:
            return {
                "ppk": data[:16],
                "mak": data[16:],
            }
        if len(data) > 0:
            return {"raw": data}
        return {}

    @staticmethod
    def pack(elements: dict[str, bytes]) -> bytes:
        """Build Field 48 content from key blocks.

        Accepts:
        - {"ppk": <16 bytes>, "mak": <16 bytes>} for key change
        - {"random": <bytes>} for sign-on proof-of-endpoint
        - {"raw": <bytes>} for opaque data
        """
        if "ppk" in elements and "mak" in elements:
            return elements["ppk"] + elements["mak"]
        if "random" in elements:
            return elements["random"]
        if "raw" in elements:
            return elements["raw"]
        return b""
