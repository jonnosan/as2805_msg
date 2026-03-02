"""Asyncio stream reader/writer for AS2805 length-prefixed messages."""

from __future__ import annotations

import asyncio
import struct

from .message import AS2805Message
from .schema import ELS_SCHEMA, FieldSchema


class AsyncAS2805Stream:
    """Read and write AS2805 messages over an asyncio stream.

    Messages are framed with a 2-byte big-endian length prefix, identical
    to :class:`~as2805_msg.stream.AS2805Stream`.
    """

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        schema: FieldSchema | None = None,
    ):
        self.reader = reader
        self.writer = writer
        self.schema = schema or ELS_SCHEMA

    async def read_message(self) -> AS2805Message:
        """Read a single length-prefixed message.

        Raises :class:`asyncio.IncompleteReadError` if the connection
        closes before a complete message is received.
        """
        header = await self.reader.readexactly(2)
        length = struct.unpack("!H", header)[0]
        body = await self.reader.readexactly(length)
        return AS2805Message.unpack(body, self.schema)

    async def write_message(self, msg: AS2805Message) -> None:
        """Pack and write a length-prefixed message, then drain."""
        body = msg.pack(self.schema)
        header = struct.pack("!H", len(body))
        self.writer.write(header + body)
        await self.writer.drain()

    async def __aiter__(self):
        """Yield messages until the connection closes."""
        try:
            while True:
                yield await self.read_message()
        except (asyncio.IncompleteReadError, ConnectionError):
            return
