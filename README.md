# as2805-msg

A Python library for encoding and decoding AS2805.2 financial messages.

## Features

- Pack and unpack AS2805.2 messages to/from raw bytes
- All message types: financial (0100-0430), reconciliation (0520-0530), network management (0800-0830)
- Primary and secondary bitmap handling
- All field data types: numeric (BCD), alphanumeric (ASCII), binary, track 2, signed amounts
- Variable-length field support (LLVAR, LLLVAR)
- Sub-field parsers for Field 47 (national TLV), Field 55 (EMV BER-TLV), Field 90 (original data elements), Field 113 (payment token TLV)
- 2-byte length header framing for stream processing
- MAC input extraction for external cryptographic processing
- Configurable field schemas

## Installation

```bash
pip install as2805-msg
```

## Quick Start

### Decode a message

```python
from as2805_msg import AS2805Message

raw = b'\x02\x00\x30\x20\x05\x80\x20\xc0\x00\x04...'  # raw message bytes (no length header)
msg = AS2805Message.unpack(raw)

print(msg.mti)           # "0200"
print(msg[3])            # "000000" (processing code)
print(msg[4])            # "000000001000" (amount)
print(msg[41])           # "TERM0001" (terminal ID)
print(11 in msg)         # True (STAN is present)
```

### Build a message

```python
from as2805_msg import AS2805Message

msg = AS2805Message(mti="0200")
msg[3] = "000000"                       # Processing code: purchase, default accounts
msg[4] = "000000001000"                 # Amount: $10.00
msg[7] = "0302120000"                   # Transmission date/time
msg[11] = "000001"                      # STAN
msg[12] = "120000"                      # Local time
msg[13] = "0302"                        # Local date
msg[15] = "0302"                        # Settlement date
msg[18] = "5411"                        # MCC
msg[22] = "051"                         # POS entry mode: chip with PIN
msg[25] = "00"                          # POS condition code
msg[32] = "123456"                      # Acquiring institution
msg[35] = "4987654321098769D2512"       # Track 2 data
msg[37] = "000000000001"                # Retrieval reference number
msg[41] = "TERM0001"                    # Terminal ID
msg[42] = "MERCHANT0000001"             # Merchant ID
msg[43] = "MERCHANT NAME             SYDNEY    AU"  # Name/location
msg[53] = "0000000000000001"            # Security control info (key set 1)
msg[57] = "000000000000"                # Cash amount
msg[64] = b'\x00' * 8                   # MAC placeholder

raw = msg.pack()
```

### Stream framing

```python
from as2805_msg import AS2805Stream, AS2805Message

# Wrap a message with its 2-byte length header for transmission
msg = AS2805Message(mti="0800")
msg[7] = "0302120000"
msg[11] = "000001"
msg[33] = "123456"
msg[70] = "001"             # Sign On
msg[100] = "999999"

frame = AS2805Stream.write_message(msg)
# frame = b'\x00\x2a' + message_bytes

# Read a message back from a buffer
msg, consumed = AS2805Stream.read_message(frame)

# Read all messages from a buffer containing multiple frames
messages = AS2805Stream.read_all(buffer)
```

### Sub-field parsing

```python
from as2805_msg import AS2805Message, Field47, Field55

msg = AS2805Message.unpack(raw)

# Parse Field 47 TLV sub-elements
tags = Field47.unpack(msg[47])
print(tags["TCC"])    # Terminal Capability Code
print(tags["PCA"])    # Post Code - Card Acceptor

# Parse Field 55 EMV BER-TLV
emv = Field55.unpack(msg[55])
print(emv[b'\x9f\x26'].hex())   # Application cryptogram
print(emv[b'\x9f\x02'].hex())   # Authorised amount

# Build Field 47
msg[47] = Field47.pack({
    "TCC": b"R2",
    "PCA": b"2000",
    "FCA": b"01",
})
```

### MAC input extraction

```python
from as2805_msg import AS2805Message

msg = AS2805Message.unpack(raw)

# Get the bytes over which the MAC should be calculated
# (MTI + bitmap + fields, excluding the MAC field value itself)
mac_input = msg.mac_input()

# Calculate MAC externally and set it
mac_value = your_hsm.calculate_mac(mac_input)
msg[64] = mac_value

raw = msg.pack()
```

## Supported Message Types

| MTI  | Description                              |
|------|------------------------------------------|
| 0100 | Authorisation Request                    |
| 0110 | Authorisation Response                   |
| 0120 | Transaction Disposition Advice           |
| 0121 | Transaction Disposition Advice Repeat    |
| 0130 | Transaction Disposition Advice Response  |
| 0200 | Financial Transaction Request            |
| 0210 | Financial Transaction Request Response   |
| 0220 | Financial Transaction Advice             |
| 0221 | Financial Transaction Advice Repeat      |
| 0230 | Financial Transaction Advice Response    |
| 0420 | Acquirer Reversal Advice                 |
| 0421 | Acquirer Reversal Advice Repeat          |
| 0430 | Acquirer Reversal Advice Response        |
| 0520 | Acquirer Reconciliation Advice           |
| 0521 | Acquirer Reconciliation Advice Repeat    |
| 0530 | Acquirer Reconciliation Advice Response  |
| 0800 | Network Management Request               |
| 0810 | Network Management Request Response      |
| 0820 | Network Management Advice                |
| 0830 | Network Management Advice Response       |

## Field Data Types

| Type   | Description                        | Encoding                              |
|--------|------------------------------------|---------------------------------------|
| `n`    | Numeric                            | BCD, 2 digits per byte                |
| `an`   | Alphanumeric                       | ASCII, 1 byte per character           |
| `ans`  | Alphanumeric + special             | ASCII, 1 byte per character           |
| `a`    | Alphabetic                         | ASCII, 1 byte per character           |
| `b`    | Binary                             | Raw bytes                             |
| `z`    | Track 2                            | BCD-like, 2 symbols per byte          |
| `x+n`  | Signed amount                      | ASCII C/D prefix + BCD digits         |
| `x+n*` | Signed amount (nibble sign)        | BCD with C/D/0 sign nibble            |

## Error Handling

All exceptions inherit from `AS2805Error`:

```python
from as2805_msg import AS2805Error, AS2805ParseError, AS2805BuildError, AS2805FieldError

try:
    msg = AS2805Message.unpack(bad_data)
except AS2805ParseError as e:
    print(e)  # includes field number and description
```

## Specification Reference

This library implements the message encoding defined in:

- **AS 2805.2-2015** (Australian Standard for Financial Transaction Card Originated Messages)
- **eftpos Hub Link Specification (eLS) V23.04.01**

See [FUNC_SPEC.md](FUNC_SPEC.md) for the full functional specification including field definitions, sub-field formats, and encoding rules.

## Requirements

- Python 3.10+

## License

TBD
