"""Field 111 — Encryption Data (AES), per DR AS 2805.2:2025.

Field 111 carries AES encryption data structured as one or more *data sets*.
Each data set contains ISO 13492-style tag-length-value elements.

Wire format::

    <DataSetID: 2 hex digits> <Length: 4 hex digits> <TLV items...>

DataSetID identifies the purpose:
  01 = PIN encryption
  02 = MAC
  03 = Data encryption
  04 = Key exchange

Within each data set, items are encoded as::

    <Tag: 1 byte> <Length: 1 byte (or 2 if len > 127)> <Value: N bytes>

Known tags (from AS 2805.2:2025 clause 4.4.28):
  80 = Control (b 1)
  81 = Key-set identifier (b 4)
  82 = Derived information / Device ID + transaction counter (b 8)
  83 = Algorithm (n 2)
  84 = Key length (n 4)
  85 = Key protection (n 2)
  86 = Key index (n 2 or n 5)
  87 = PIN block format (n 2) / Encrypted data (b var)
  88 = Encrypted PIN block (b 16) / Key checksum value (b var)
  89 = Additional encrypted PIN block (b 16)
"""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import AS2805ParseError


TAG_NAMES: dict[int, str] = {
    0x80: "Control",
    0x81: "Key-set identifier",
    0x82: "Derived information",
    0x83: "Algorithm",
    0x84: "Key length",
    0x85: "Key protection",
    0x86: "Key index",
    0x87: "PIN block format / Encrypted data",
    0x88: "Encrypted PIN block / Key checksum value",
    0x89: "Additional encrypted PIN block",
}

DATASET_NAMES: dict[int, str] = {
    0x01: "PIN encryption",
    0x02: "MAC",
    0x03: "Data encryption",
    0x04: "Key exchange",
}


@dataclass
class DataSet:
    """A single data set within Field 111."""

    dataset_id: int
    elements: dict[int, bytes]

    @property
    def name(self) -> str:
        return DATASET_NAMES.get(self.dataset_id, f"Unknown ({self.dataset_id:02X})")


class Field111:
    """Parse and build Field 111 Encryption Data content."""

    @staticmethod
    def unpack(data: bytes) -> list[DataSet]:
        """Parse Field 111 content into a list of data sets.

        Each data set contains a dict of {tag: value_bytes}.
        """
        results: list[DataSet] = []
        pos = 0
        while pos < len(data):
            if pos + 3 > len(data):
                raise AS2805ParseError(
                    f"Field 111: incomplete data set header at offset {pos}"
                )
            # Data set ID: 1 byte
            dataset_id = data[pos]
            pos += 1
            # Data set length: 2 bytes BCD (4 digits)
            len_hi = data[pos]
            len_lo = data[pos + 1]
            ds_length = (len_hi >> 4) * 1000 + (len_hi & 0x0F) * 100 + (len_lo >> 4) * 10 + (len_lo & 0x0F)
            pos += 2

            if pos + ds_length > len(data):
                raise AS2805ParseError(
                    f"Field 111: data set {dataset_id:02X} length {ds_length} "
                    f"exceeds available data at offset {pos}"
                )

            # Parse TLV elements within this data set
            elements = _parse_tlv(data, pos, pos + ds_length)
            results.append(DataSet(dataset_id=dataset_id, elements=elements))
            pos += ds_length

        return results

    @staticmethod
    def pack(datasets: list[DataSet]) -> bytes:
        """Build Field 111 content from a list of data sets."""
        parts: list[bytes] = []
        for ds in datasets:
            tlv_bytes = _build_tlv(ds.elements)
            ds_len = len(tlv_bytes)
            # Encode length as 2-byte BCD
            len_str = str(ds_len).zfill(4)
            len_bytes = bytes([
                (int(len_str[0]) << 4) | int(len_str[1]),
                (int(len_str[2]) << 4) | int(len_str[3]),
            ])
            parts.append(bytes([ds.dataset_id]) + len_bytes + tlv_bytes)
        return b"".join(parts)


def _parse_tlv(data: bytes, start: int, end: int) -> dict[int, bytes]:
    """Parse simple TLV items (1-byte tag, 1-or-2-byte length, value)."""
    elements: dict[int, bytes] = {}
    pos = start
    while pos < end:
        if pos + 2 > end:
            raise AS2805ParseError(
                f"Field 111: incomplete TLV at offset {pos}"
            )
        tag = data[pos]
        pos += 1

        length_byte = data[pos]
        pos += 1
        if length_byte & 0x80:
            # Long form: next N bytes encode the length
            num_len_bytes = length_byte & 0x7F
            if pos + num_len_bytes > end:
                raise AS2805ParseError(
                    f"Field 111: incomplete long-form length at offset {pos}"
                )
            length = int.from_bytes(data[pos:pos + num_len_bytes], "big")
            pos += num_len_bytes
        else:
            length = length_byte

        if pos + length > end:
            raise AS2805ParseError(
                f"Field 111: tag {tag:02X} value length {length} "
                f"exceeds data set boundary"
            )
        elements[tag] = data[pos:pos + length]
        pos += length

    return elements


def _build_tlv(elements: dict[int, bytes]) -> bytes:
    """Build TLV bytes from {tag: value} dict."""
    parts: list[bytes] = []
    for tag in sorted(elements):
        value = elements[tag]
        parts.append(bytes([tag]))
        length = len(value)
        if length > 127:
            # Long form
            len_bytes = length.to_bytes((length.bit_length() + 7) // 8, "big")
            parts.append(bytes([0x80 | len(len_bytes)]))
            parts.append(len_bytes)
        else:
            parts.append(bytes([length]))
        parts.append(value)
    return b"".join(parts)
