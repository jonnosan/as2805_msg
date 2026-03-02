"""AS2805Stream — 2-byte length-header message framing."""

from __future__ import annotations

import struct

from .errors import AS2805ParseError
from .message import AS2805Message
from .schema import FieldSchema


class AS2805Stream:
    """Handles reading/writing AS2805 messages with 2-byte length framing."""

    @staticmethod
    def read_message(
        data: bytes, offset: int = 0, schema: FieldSchema | None = None
    ) -> tuple[AS2805Message, int]:
        """Read a single length-prefixed message from a buffer.

        Returns (message, total_bytes_consumed) including the 2-byte header.
        """
        if offset + 2 > len(data):
            raise AS2805ParseError("Not enough data for message length header")

        msg_len = struct.unpack_from("!H", data, offset)[0]
        if offset + 2 + msg_len > len(data):
            raise AS2805ParseError(
                f"Message length {msg_len} exceeds available data "
                f"({len(data) - offset - 2} bytes available)"
            )

        msg_bytes = data[offset + 2: offset + 2 + msg_len]
        msg = AS2805Message.unpack(msg_bytes, schema)
        return msg, 2 + msg_len

    @staticmethod
    def write_message(
        msg: AS2805Message, schema: FieldSchema | None = None
    ) -> bytes:
        """Pack a message and prepend its 2-byte big-endian length header."""
        body = msg.pack(schema)
        header = struct.pack("!H", len(body))
        return header + body

    @staticmethod
    def read_all(
        data: bytes, schema: FieldSchema | None = None
    ) -> list[AS2805Message]:
        """Read all consecutive length-prefixed messages from a buffer."""
        messages: list[AS2805Message] = []
        offset = 0
        while offset < len(data):
            msg, consumed = AS2805Stream.read_message(data, offset, schema)
            messages.append(msg)
            offset += consumed
        return messages
