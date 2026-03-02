"""Tests for as2805_msg.async_stream — asyncio message reader/writer."""

import asyncio
import struct

import pytest

from as2805_msg import AS2805Message, AsyncAS2805Stream


def _make_framed(msg: AS2805Message) -> bytes:
    """Pack a message with 2-byte length header."""
    body = msg.pack()
    return struct.pack("!H", len(body)) + body


class TestAsyncAS2805Stream:
    @pytest.mark.asyncio
    async def test_read_write_roundtrip(self):
        msg = AS2805Message(mti="0800", fields={
            7: "0302120000",
            11: "000001",
            33: "12345",
            70: "001",
            100: "67890",
        })

        # Create in-memory stream pair
        reader = asyncio.StreamReader()
        # We'll simulate by feeding data to the reader
        framed = _make_framed(msg)
        reader.feed_data(framed)
        reader.feed_eof()

        # Create a mock writer
        written_data = bytearray()

        class MockWriter:
            def write(self, data):
                written_data.extend(data)

            async def drain(self):
                pass

        stream = AsyncAS2805Stream(reader, MockWriter())

        # Read the message back
        received = await stream.read_message()
        assert received.mti == "0800"
        assert received[70] == "001"

    @pytest.mark.asyncio
    async def test_write_message(self):
        msg = AS2805Message(mti="0800", fields={
            7: "0302120000",
            11: "000001",
            33: "12345",
            70: "001",
            100: "67890",
        })

        reader = asyncio.StreamReader()
        written_data = bytearray()

        class MockWriter:
            def write(self, data):
                written_data.extend(data)

            async def drain(self):
                pass

        stream = AsyncAS2805Stream(reader, MockWriter())
        await stream.write_message(msg)

        # Verify framing
        assert len(written_data) > 2
        length = struct.unpack("!H", bytes(written_data[:2]))[0]
        assert length == len(written_data) - 2

        # Verify we can decode the body
        body = bytes(written_data[2:])
        decoded = AS2805Message.unpack(body)
        assert decoded.mti == "0800"

    @pytest.mark.asyncio
    async def test_async_iter(self):
        msg1 = AS2805Message(mti="0800", fields={
            7: "0302120000", 11: "000001", 33: "12345", 70: "001", 100: "67890",
        })
        msg2 = AS2805Message(mti="0810", fields={
            7: "0302120000", 11: "000001", 33: "12345", 39: "00", 70: "001", 100: "67890",
        })

        reader = asyncio.StreamReader()
        reader.feed_data(_make_framed(msg1))
        reader.feed_data(_make_framed(msg2))
        reader.feed_eof()

        stream = AsyncAS2805Stream(reader, None)

        messages = []
        async for m in stream:
            messages.append(m)

        assert len(messages) == 2
        assert messages[0].mti == "0800"
        assert messages[1].mti == "0810"

    @pytest.mark.asyncio
    async def test_eof_raises_incomplete_read(self):
        reader = asyncio.StreamReader()
        reader.feed_data(b"\x00")  # incomplete header
        reader.feed_eof()

        stream = AsyncAS2805Stream(reader, None)
        with pytest.raises(asyncio.IncompleteReadError):
            await stream.read_message()
