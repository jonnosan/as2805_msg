"""Tests for as2805_msg.dump — hex dump utilities."""

from as2805_msg import AS2805Message, dump, dump_raw


class TestDump:
    def test_dump_contains_field_names(self):
        msg = AS2805Message(mti="0800", fields={
            7: "0302120000",
            11: "000001",
            33: "12345",
            70: "001",
            100: "67890",
        })
        output = dump(msg)
        assert "MTI: 0800" in output
        assert "Transmission Date" in output
        assert "Systems Trace" in output
        assert "Network Management" in output

    def test_dump_shows_binary_hex(self):
        msg = AS2805Message(mti="0800", fields={
            7: "0302120000",
            11: "000001",
            33: "12345",
            70: "001",
            100: "67890",
            128: b"\xAA\xBB\xCC\xDD\xEE\xFF\x00\x11",
        })
        output = dump(msg)
        assert "aa bb cc dd" in output

    def test_dump_shows_type_info(self):
        msg = AS2805Message(mti="0800", fields={
            7: "0302120000",
            11: "000001",
            33: "12345",
            70: "001",
            100: "67890",
        })
        output = dump(msg)
        # Should contain field type info like "n 10 fixed"
        assert "fixed" in output


class TestDumpRaw:
    def test_dump_raw_short(self):
        data = bytes(range(16))
        output = dump_raw(data)
        assert "00000000" in output
        assert "00 01 02" in output
        # ASCII column
        assert "|" in output

    def test_dump_raw_multiline(self):
        data = bytes(range(32))
        output = dump_raw(data)
        assert "00000010" in output  # second line offset

    def test_dump_raw_non_printable(self):
        data = b"\x00\x01\x02\x41\x42\x43"
        output = dump_raw(data)
        assert "ABC" in output
        assert "..." in output

    def test_dump_raw_empty(self):
        output = dump_raw(b"")
        assert output == ""
