"""Tests for as2805_msg.fields.field111 — Encryption Data (AES) parser."""

import pytest

from as2805_msg import Field111, DataSet
from as2805_msg.fields.field111 import TAG_NAMES, DATASET_NAMES


class TestField111Unpack:
    def test_single_dataset_pin_dukpt(self):
        """Example 1 from DR AS 2805.2:2025 — PIN data set with DUKPT."""
        # Data Set 01 (PIN):
        # 80=06, 81=12345678, 82=9012345600000001, 83=05, 84=0016, 87=04,
        # 88=6F79668FAB6D076CEE042B1E0FE42C36
        ds_content = bytes.fromhex(
            "800106"                              # tag 80, len 1, value 06
            "810412345678"                        # tag 81, len 4, value 12345678
            "82089012345600000001"                # tag 82, len 8
            "830105"                              # tag 83, len 1, value 05
            "84020016"                            # tag 84, len 2, value 0016
            "870104"                              # tag 87, len 1, value 04
            "88106F79668FAB6D076CEE042B1E0FE42C36"  # tag 88, len 16
        )
        # Wrap in data set: ID=01, length as 4-digit BCD
        ds_len = len(ds_content)
        ds_len_bcd = bytes([
            (ds_len // 100 % 10) << 4 | (ds_len // 10 % 10),
            (ds_len % 10) << 4 | 0,
        ])
        # Actually let's compute properly
        ds_len_str = str(ds_len).zfill(4)
        ds_len_bcd = bytes([
            int(ds_len_str[0]) << 4 | int(ds_len_str[1]),
            int(ds_len_str[2]) << 4 | int(ds_len_str[3]),
        ])
        data = bytes([0x01]) + ds_len_bcd + ds_content

        result = Field111.unpack(data)
        assert len(result) == 1
        ds = result[0]
        assert ds.dataset_id == 0x01
        assert ds.name == "PIN encryption"
        assert ds.elements[0x80] == b"\x06"
        assert ds.elements[0x81] == bytes.fromhex("12345678")
        assert ds.elements[0x82] == bytes.fromhex("9012345600000001")
        assert ds.elements[0x83] == b"\x05"
        assert ds.elements[0x88] == bytes.fromhex("6F79668FAB6D076CEE042B1E0FE42C36")

    def test_two_datasets_pin_and_mac(self):
        """Two data sets: PIN (01) and MAC (02)."""
        # PIN data set
        pin_content = bytes.fromhex("800106" "810412345678" "830105")
        pin_len_str = str(len(pin_content)).zfill(4)
        pin_header = bytes([0x01,
            int(pin_len_str[0]) << 4 | int(pin_len_str[1]),
            int(pin_len_str[2]) << 4 | int(pin_len_str[3]),
        ])

        # MAC data set
        mac_content = bytes.fromhex("800106" "810412345678" "830106")
        mac_len_str = str(len(mac_content)).zfill(4)
        mac_header = bytes([0x02,
            int(mac_len_str[0]) << 4 | int(mac_len_str[1]),
            int(mac_len_str[2]) << 4 | int(mac_len_str[3]),
        ])

        data = pin_header + pin_content + mac_header + mac_content
        result = Field111.unpack(data)

        assert len(result) == 2
        assert result[0].dataset_id == 0x01
        assert result[0].name == "PIN encryption"
        assert result[1].dataset_id == 0x02
        assert result[1].name == "MAC"

    def test_empty_data(self):
        result = Field111.unpack(b"")
        assert result == []

    def test_long_form_length(self):
        """Tag with value > 127 bytes uses long-form length encoding."""
        # Create a value of 200 bytes
        value = bytes(range(200))
        # Long form: 81 C8 (0x81 = 1 length byte follows, 0xC8 = 200)
        tlv = bytes([0x87, 0x81, 200]) + value
        ds_len_str = str(len(tlv)).zfill(4)
        ds_header = bytes([0x04,
            int(ds_len_str[0]) << 4 | int(ds_len_str[1]),
            int(ds_len_str[2]) << 4 | int(ds_len_str[3]),
        ])
        data = ds_header + tlv
        result = Field111.unpack(data)
        assert len(result) == 1
        assert result[0].elements[0x87] == value

    def test_incomplete_header_raises(self):
        with pytest.raises(Exception):
            Field111.unpack(b"\x01\x00")  # incomplete header

    def test_truncated_data_raises(self):
        # Data set says 10 bytes but only 2 available
        data = bytes([0x01, 0x00, 0x10, 0x80, 0x01])
        with pytest.raises(Exception):
            Field111.unpack(data)


class TestField111Pack:
    def test_single_dataset(self):
        ds = DataSet(dataset_id=0x02, elements={
            0x80: b"\x02",
            0x81: bytes.fromhex("00000000"),
            0x83: b"\x06",
        })
        packed = Field111.pack([ds])
        # Unpack and verify roundtrip
        result = Field111.unpack(packed)
        assert len(result) == 1
        assert result[0].dataset_id == 0x02
        assert result[0].elements[0x80] == b"\x02"
        assert result[0].elements[0x81] == bytes.fromhex("00000000")
        assert result[0].elements[0x83] == b"\x06"

    def test_roundtrip_two_datasets(self):
        datasets = [
            DataSet(dataset_id=0x01, elements={
                0x80: b"\x06",
                0x81: bytes.fromhex("12345678"),
                0x83: b"\x05",
            }),
            DataSet(dataset_id=0x02, elements={
                0x80: b"\x06",
                0x83: b"\x06",
            }),
        ]
        packed = Field111.pack(datasets)
        result = Field111.unpack(packed)
        assert len(result) == 2
        assert result[0].dataset_id == 0x01
        assert result[1].dataset_id == 0x02
        assert result[0].elements[0x80] == b"\x06"
        assert result[1].elements[0x83] == b"\x06"

    def test_long_form_roundtrip(self):
        """Values > 127 bytes should use long-form length and roundtrip."""
        big_value = bytes(range(256)) * 2  # 512 bytes
        ds = DataSet(dataset_id=0x04, elements={0x87: big_value})
        packed = Field111.pack([ds])
        result = Field111.unpack(packed)
        assert result[0].elements[0x87] == big_value

    def test_empty_datasets(self):
        packed = Field111.pack([])
        assert packed == b""


class TestField111MessageRoundtrip:
    def test_pack_unpack_with_message(self):
        """Test Field 111 through the full message pack/unpack cycle."""
        from as2805_msg import AS2805Message

        # Build Field 111 content
        ds = DataSet(dataset_id=0x02, elements={
            0x80: b"\x02",
            0x81: bytes.fromhex("00000000"),
            0x83: b"\x06",
        })
        f111_bytes = Field111.pack([ds])

        msg = AS2805Message(mti="0800", fields={
            7: "0302120000",
            11: "000001",
            33: "12345",
            70: "001",
            100: "67890",
            111: f111_bytes,
        })

        packed = msg.pack()
        decoded = AS2805Message.unpack(packed)

        assert decoded.mti == "0800"
        assert 111 in decoded
        # Parse the decoded field 111
        datasets = Field111.unpack(decoded[111])
        assert len(datasets) == 1
        assert datasets[0].dataset_id == 0x02
        assert datasets[0].elements[0x83] == b"\x06"


class TestTagAndDatasetNames:
    def test_known_tags(self):
        assert TAG_NAMES[0x80] == "Control"
        assert TAG_NAMES[0x83] == "Algorithm"
        assert TAG_NAMES[0x88] == "Encrypted PIN block / Key checksum value"

    def test_dataset_names(self):
        assert DATASET_NAMES[0x01] == "PIN encryption"
        assert DATASET_NAMES[0x02] == "MAC"
        assert DATASET_NAMES[0x04] == "Key exchange"

    def test_dataset_name_property(self):
        ds = DataSet(dataset_id=0x03, elements={})
        assert ds.name == "Data encryption"

        ds2 = DataSet(dataset_id=0xFF, elements={})
        assert "Unknown" in ds2.name
