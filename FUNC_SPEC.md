# Functional Specification: AS2805 Message Library

## 1. Overview

A Python library for encoding and decoding AS2805.2 format messages.

The library handles the binary wire format of AS2805 messages: framing, message type indicators, bitmaps, and field-level encoding/decoding for all data element types defined in the specification.

## 2. Scope

### In Scope

- Parsing raw AS2805 message bytes into structured Python objects
- Building AS2805 message bytes from structured Python objects
- All message types used on eftpos Hub interchange links (0100/0110, 0200/0210, 0220/0221/0230, 0420/0421/0430, 0520/0521/0530, 0800/0810, 0820/0830)
- Primary and secondary bitmaps
- All field data types defined in Appendix H of the eLS specification
- 2-byte message length header (framing)
- Field 47 (Additional Data - National) sub-element TLV parsing
- Field 55 (ICC Related Data) BER-TLV parsing
- Field 113 (Payment Token Data) TLV parsing
- Field 90 (Original Data Elements) composite sub-field parsing

### Out of Scope

- Cryptographic operations (MAC generation/verification, PIN encryption, session key exchange)
- TCP/IP transport and connection management
- Transaction processing logic, routing, or business rules
- Hub-specific validation rules (Appendix E)
- Settlement/reconciliation processing logic

## 3. Message Structure

### 3.1 Framing

Each AS2805 message on the wire is preceded by a **2-byte binary length header** in network byte order (big-endian), indicating the length of the following message in bytes, exclusive of the header itself.

```
| Length (2 bytes, big-endian) | Message body (N bytes) |
```

Example: a 200-byte message is preceded by bytes `0x00 0xC8`.

### 3.2 Message Body Layout

```
| MTI (4 bytes) | Primary Bitmap (8 bytes) | [Secondary Bitmap (8 bytes)] | Data Fields... |
```

- **Message Type Indicator (MTI)**: 4 numeric digits encoded as BCD (2 bytes) representing the message class, function, and origin (e.g., `0200`, `0810`).
- **Primary Bitmap**: 64 bits (8 bytes) indicating presence of fields 1-64.
- **Secondary Bitmap**: 64 bits (8 bytes), present when bit 1 of the primary bitmap is set, indicating presence of fields 65-128.
- **Data Fields**: Encoded sequentially in field-number order for each bit set in the bitmap(s).

### 3.3 MTI Classification

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

Note: The repeat bit (bit 0 of the 4th MTI digit) is not included in MAC calculations per AS2805.2-2007 clause 2.3.

## 4. Data Element Types

All encoding follows AS2805.2-2007 Appendix I as referenced by eLS Appendix H.

| Type   | Description                                      | Encoding                                                    |
|--------|--------------------------------------------------|-------------------------------------------------------------|
| `b`    | Binary data                                      | Raw bytes. Length specified in bits (multiples of 8).        |
| `n`    | Numeric digits 0-9                               | BCD packed, 2 digits per byte. Odd-length fields are right-justified, left-padded with 0. |
| `z`    | Track 2 data                                     | BCD-like, 2 symbols per byte, using ISO 7813 character set. |
| `a`    | Alphabetic characters (A-Z, a-z)                 | ASCII, 1 byte per character, MSB zero.                      |
| `an`   | Alphanumeric                                     | ASCII, 1 byte per character, MSB zero.                      |
| `ans`  | Alphanumeric + special characters                | ASCII, 1 byte per character, MSB zero. Field 48 may contain non-printable values despite `ans` designation. |
| `x+n`  | Signed amount                                    | ASCII 'C' (0x43) or 'D' (0x44) prefix followed by BCD-packed numeric digits. |
| `x+n*` | Signed amount (nibble sign)                      | BCD-packed, first nibble is 0x0 (unsigned), 0xC (credit), or 0xD (debit), remaining nibbles are numeric digits. |

### 4.1 Field Length Encoding

Fields are categorised by their length type:

| Length Type       | Description                                                                                    |
|-------------------|------------------------------------------------------------------------------------------------|
| **Fixed**         | Length is fixed and defined by the specification. No length prefix in the wire format.          |
| **LLVAR**         | Variable length, prefixed with 2-digit BCD length (max 99).                                    |
| **LLLVAR**        | Variable length, prefixed with 3-digit BCD length (max 999).                                   |

Special case: Field 48 uses a 3-byte ASCII-encoded length prefix rather than BCD.

### 4.2 Field 90 - Original Data Elements

Field 90 is a fixed-length 42-digit numeric field with composite sub-fields:

| Position | Length | Sub-field                        |
|----------|--------|----------------------------------|
| 1-4      | 4      | Original Message Type Indicator  |
| 5-10     | 6      | Original STAN                    |
| 11-20    | 10     | Original Transmission Date/Time  |
| 21-31    | 11     | Acquiring Institution ID (right-justified, zero-padded) |
| 32-42    | 11     | Forwarding Institution ID (right-justified, zero-padded) |

Note: The Acquiring Institution and Forwarding Institution sub-fields share a byte boundary (the rightmost digit of Acquiring Institution and the leftmost digit of Forwarding Institution are encoded in the same octet).

## 5. Data Element Definitions

The following table defines all data elements (fields) used across eLS message types. Field numbers correspond to AS2805.2 data element numbers.

| Field | Name                                  | Type   | Length     | Length Type |
|-------|---------------------------------------|--------|------------|-------------|
| 001   | Bitmap, Secondary                     | b      | 64 bits    | Fixed       |
| 002   | Primary Account Number (PAN)          | n      | ..19       | LLVAR       |
| 003   | Processing Code                       | n      | 6          | Fixed       |
| 004   | Amount, Transaction                   | n      | 12         | Fixed       |
| 007   | Transmission Date & Time              | n      | 10         | Fixed       |
| 011   | Systems Trace Audit Number (STAN)     | n      | 6          | Fixed       |
| 012   | Time, Local Transaction               | n      | 6          | Fixed       |
| 013   | Date, Local Transaction               | n      | 4          | Fixed       |
| 014   | Expiry Date                           | n      | 4          | Fixed       |
| 015   | Date, Settlement                      | n      | 4          | Fixed       |
| 018   | Merchant's Type (MCC)                 | n      | 4          | Fixed       |
| 022   | POS Entry Mode                        | n      | 3          | Fixed       |
| 023   | Card Sequence Number                  | n      | 3          | Fixed       |
| 025   | POS Condition Code                    | n      | 2          | Fixed       |
| 028   | Amount, Transaction Fee               | x+n    | 8          | Fixed       |
| 030   | Amount, Transaction Processing Fee    | x+n    | 8          | Fixed       |
| 032   | Acquiring Institution ID Code         | n      | ..11       | LLVAR       |
| 033   | Forwarding Institution ID Code        | n      | ..11       | LLVAR       |
| 035   | Track 2 Data                          | z      | ..37       | LLVAR       |
| 037   | Retrieval Reference Number            | an     | 12         | Fixed       |
| 038   | Authorisation ID Response             | an     | 6          | Fixed       |
| 039   | Response Code                         | an     | 2          | Fixed       |
| 041   | Card Acceptor Terminal ID             | ans    | 8          | Fixed       |
| 042   | Card Acceptor Identification Code     | ans    | 15         | Fixed       |
| 043   | Card Acceptor Name/Location           | ans    | 40         | Fixed       |
| 044   | Additional Response Data              | ans    | ..25       | LLVAR       |
| 047   | Additional Data - National            | ans    | ..999      | LLLVAR      |
| 048   | Additional Data - Private             | ans    | ..999      | LLLVAR      |
| 052   | PIN Data                              | b      | 64 bits    | Fixed       |
| 053   | Security Related Control Information  | n      | 16         | Fixed       |
| 054   | Additional Amounts                    | an     | ..120      | LLLVAR      |
| 055   | ICC Related Data                      | b      | ..999      | LLLVAR      |
| 057   | Amount, Cash                          | n      | 12         | Fixed       |
| 058   | Ledger Balance                        | x+n*   | 12         | Fixed       |
| 059   | Account Balance, Cleared Funds        | x+n*   | 12         | Fixed       |
| 064   | Message Authentication Code (MAC)     | b      | 64 bits    | Fixed       |
| 066   | Settlement Code                       | n      | 1          | Fixed       |
| 070   | Network Management Information Code   | n      | 3          | Fixed       |
| 090   | Original Data Elements                | n      | 42         | Fixed       |
| 095   | Replacement Amounts                   | an     | 42         | Fixed       |
| 100   | Receiving Institution ID Code         | n      | ..11       | LLVAR       |
| 113   | Payment Token Data                    | b      | ..999      | LLLVAR      |
| 128   | Message Authentication Code (MAC)     | b      | 64 bits    | Fixed       |

## 6. Field 47 - Additional Data National (TLV Sub-elements)

Field 47 contains sub-elements in a tag-value format. Each sub-element consists of:

```
| Tag (3 bytes ASCII) | Length (3 bytes ASCII) | Value (variable) |
```

Tags and their lengths are encoded as zero-padded ASCII decimal strings.

### 6.1 Known Tags

| Tag ID | Name                                        | Type | Max Length |
|--------|---------------------------------------------|------|------------|
| ARI    | Account Reference Indicator                 | an   | 3          |
| TCC    | Terminal Capability Code                    | an   | 2          |
| FCR    | Faulty Card Reader                          | an   | 1          |
| PCA    | Post Code - Card Acceptor                   | n    | 4          |
| FCA    | Format of Card Acceptor Name/Location       | an   | 2          |
| BAI    | Business Application Indicator              | an   | 2          |
| CTP    | Cash Type Indicator                         | an   | 2          |
| FSC    | Fraud Score                                 | n    | 4          |
| FCC    | Fraud Sub-classification Code               | an   | 4          |
| ECM    | eCommerce Indicator                         | an   | 2          |
| DCP    | Deferred Card Present                       | an   | 2          |
| CAV    | Cardholder Authentication Verification      | ans  | variable   |
| OLT    | Open Loop Transit                           | ans  | variable   |

## 7. Field 55 - ICC Related Data (BER-TLV)

Field 55 contains EMV chip data encoded as BER-TLV (Basic Encoding Rules - Tag Length Value) per ISO/IEC 7816 / X.690.

The library must parse and build BER-TLV structures supporting:
- Single-byte and multi-byte tags
- Short form and long form lengths
- Nested constructed TLV objects

### 7.1 Common EMV Tags in eLS

| Tag    | Name                                    | Request | Response |
|--------|-----------------------------------------|---------|----------|
| 9F26   | Application Cryptogram (AC)             | M       | -        |
| 9F27   | Cryptogram Information Data             | M       | -        |
| 9F10   | Issuer Application Data                 | M       | -        |
| 9F37   | Unpredictable Number                    | M       | -        |
| 9F36   | Application Transaction Counter (ATC)   | M       | -        |
| 9F02   | Amount, Authorised                      | M       | -        |
| 9F03   | Amount, Other                           | M       | -        |
| 9F1A   | Terminal Country Code                   | M       | -        |
| 5F2A   | Transaction Currency Code               | M       | -        |
| 9A     | Transaction Date                        | M       | -        |
| 9C     | Transaction Type                        | M       | -        |
| 9F34   | Cardholder Verification Method Results  | C       | -        |
| 9F33   | Terminal Capabilities                   | M       | -        |
| 9F35   | Terminal Type                           | M       | -        |
| 95     | Terminal Verification Results           | M       | -        |
| 82     | Application Interchange Profile         | M       | -        |
| 9F09   | Application Version Number (Terminal)   | C       | -        |
| 84     | Dedicated File Name                     | M       | -        |
| 5F34   | PAN Sequence Number                     | C       | -        |
| 91     | Issuer Authentication Data              | -       | O        |
| 71     | Issuer Script Template 1               | -       | O        |
| 72     | Issuer Script Template 2               | -       | O        |

## 8. Field 113 - Payment Token Data (TLV)

Field 113 contains token-related data encoded as TLV sub-elements. Each element consists of:

```
| Tag ID (3 bytes, numeric) | Length (3 bytes, numeric) | Value (variable) |
```

### 8.1 Known Tags

| Tag ID | Name                          | Type | Length   |
|--------|-------------------------------|------|----------|
| 001    | Funding PAN                   | n    | ..19     |
| 002    | Funding PAN Expiry Date       | n    | 4        |
| 006    | Token Expiry Date             | n    | 4        |
| 009    | Track 2 Equivalent Data       | z    | ..37     |
| 123    | User Validation Method        | n    | 2        |
| 157    | TSP Validation Results        | b    | 4        |
| 174    | Cumulative Transaction Value  | an   | 12       |
| 175    | Domain Control Restriction    | an   | 2        |
| 176    | Counterparty Masked PAN       | ans  | 13..19   |
| 180    | Token Class                   | n    | 2        |
| 304    | Counterparty Name             | ans  | ..45     |
| 305    | Counterparty BSB and Account  | ans  | 16       |
| 306    | Counterparty Date of Birth    | n    | 8        |
| 307    | Counterparty Place of Birth   | ans  | 1..25    |
| 308    | Counterparty Address          | ans  | 1..35    |
| 309    | Counterparty City             | ans  | 1..25    |
| 310    | Counterparty State Code       | ans  | 2..3     |
| 311    | Counterparty Postal Code      | n    | 4        |

## 9. Public API

### 9.1 Core Classes

#### `AS2805Message`

Represents a parsed or constructed AS2805 message.

```python
class AS2805Message:
    mti: str                           # e.g. "0200"
    fields: dict[int, Any]             # field number -> decoded value

    @classmethod
    def unpack(cls, data: bytes) -> "AS2805Message":
        """Decode a message from raw bytes (excluding 2-byte length header)."""

    def pack(self) -> bytes:
        """Encode the message to raw bytes (excluding 2-byte length header)."""

    def __getitem__(self, field: int) -> Any:
        """Get a field value by field number."""

    def __setitem__(self, field: int, value: Any) -> None:
        """Set a field value by field number."""

    def __contains__(self, field: int) -> bool:
        """Check if a field is present."""
```

#### `AS2805Stream`

Handles message framing over a byte stream.

```python
class AS2805Stream:
    @staticmethod
    def read_message(data: bytes, offset: int = 0) -> tuple[AS2805Message, int]:
        """Read a length-prefixed message from a buffer.
        Returns (message, bytes_consumed)."""

    @staticmethod
    def write_message(msg: AS2805Message) -> bytes:
        """Wrap a message with its 2-byte length header."""

    @staticmethod
    def read_all(data: bytes) -> list[AS2805Message]:
        """Read all length-prefixed messages from a buffer."""
```

### 9.2 Field Schema Configuration

The library uses a field schema definition that maps field numbers to their encoding attributes. A default schema matching the eLS specification is provided, but users can supply custom schemas.

```python
@dataclass
class FieldSpec:
    number: int
    name: str
    field_type: str          # "n", "an", "ans", "b", "z", "x+n", "x+n*"
    max_length: int
    length_type: str         # "fixed", "llvar", "lllvar"
    description: str = ""

class FieldSchema:
    """Registry of field specifications."""

    def get(self, field_number: int) -> FieldSpec: ...
    def register(self, spec: FieldSpec) -> None: ...
```

### 9.3 Sub-field Parsers

```python
class Field47:
    """Parse/build Field 47 Additional Data - National TLV sub-elements."""

    @staticmethod
    def unpack(data: bytes) -> dict[str, bytes]:
        """Parse TLV sub-elements. Returns {tag_id: value}."""

    @staticmethod
    def pack(elements: dict[str, bytes]) -> bytes:
        """Build TLV sub-elements from {tag_id: value}."""

class Field55:
    """Parse/build Field 55 ICC Related Data BER-TLV."""

    @staticmethod
    def unpack(data: bytes) -> dict[bytes, bytes]:
        """Parse BER-TLV. Returns {tag: value}."""

    @staticmethod
    def pack(elements: dict[bytes, bytes]) -> bytes:
        """Build BER-TLV from {tag: value}."""

class Field90:
    """Parse/build Field 90 Original Data Elements."""

    @staticmethod
    def unpack(data: bytes) -> dict[str, str]:
        """Parse into sub-fields: mti, stan, transmission_dt, acq_inst, fwd_inst."""

    @staticmethod
    def pack(elements: dict[str, str]) -> bytes:
        """Build from sub-field dict."""

class Field113:
    """Parse/build Field 113 Payment Token Data TLV."""

    @staticmethod
    def unpack(data: bytes) -> dict[str, bytes]:
        """Parse TLV sub-elements. Returns {tag_id: value}."""

    @staticmethod
    def pack(elements: dict[str, bytes]) -> bytes:
        """Build TLV sub-elements from {tag_id: value}."""
```

### 9.4 Utility Functions

```python
def bcd_encode(digits: str, length: int) -> bytes:
    """Encode decimal digit string as BCD bytes."""

def bcd_decode(data: bytes) -> str:
    """Decode BCD bytes to decimal digit string."""

def build_bitmap(fields: Iterable[int]) -> bytes:
    """Build primary (and secondary if needed) bitmap bytes from field numbers."""

def parse_bitmap(data: bytes) -> tuple[set[int], int]:
    """Parse bitmap bytes, return (set of field numbers, bytes consumed)."""
```

## 10. Error Handling

The library defines a hierarchy of exceptions:

| Exception                  | Description                                                |
|----------------------------|------------------------------------------------------------|
| `AS2805Error`              | Base exception for all library errors.                     |
| `AS2805ParseError`         | Error decoding a message from bytes.                       |
| `AS2805BuildError`         | Error encoding a message to bytes.                         |
| `AS2805FieldError`         | Invalid field data (wrong type, length, or value).         |
| `AS2805BitmapError`        | Corrupt or inconsistent bitmap.                            |

Error messages must include the field number and a description of the problem for diagnostic purposes.

## 11. Processing Code (Field 3)

Field 3 is a 6-digit numeric field with three 2-digit sub-fields:

| Position | Name                  | Description                         |
|----------|-----------------------|-------------------------------------|
| 1-2      | Transaction Type      | Type of transaction                 |
| 3-4      | Source Account        | Account to debit (from)             |
| 5-6      | Destination Account   | Account to credit (to)              |

### 11.1 Transaction Types

| Code | Description                |
|------|----------------------------|
| 00   | Purchase                   |
| 01   | Cash-out / Withdrawal      |
| 09   | Purchase with Cash-out     |
| 20   | Refund                     |
| 21   | Deposit                    |
| 30   | Balance Enquiry            |
| 31   | Balance Enquiry            |
| 33   | Account Verify             |

### 11.2 Account Types

| Code | Description              |
|------|--------------------------|
| 00   | Default / Not specified  |
| 10   | Savings                  |
| 20   | Cheque / Current         |
| 30   | Credit                   |

## 12. Response Codes (Field 39)

A 2-character alphanumeric response code. Key values:

| Code | Description                           | Action                      |
|------|---------------------------------------|-----------------------------|
| 00   | Approved                              | Complete                    |
| 01   | Refer to Card Issuer                  | Decline                     |
| 05   | Do not Honour                         | Decline                     |
| 12   | Invalid Transaction                   | Decline                     |
| 13   | Invalid Amount                        | Decline                     |
| 14   | Invalid Card Number                   | Decline                     |
| 19   | Re-enter transaction                  | Decline - retry             |
| 21   | No action taken                       | Unmatched reversal          |
| 30   | Format Error                          | Decline                     |
| 51   | Not sufficient funds                  | Decline                     |
| 54   | Expired card                          | Decline                     |
| 55   | Invalid PIN                           | Decline                     |
| 76   | Approved (no original found)          | Complete                    |
| 77   | Intervention required - sign off      | Re-sign-on                  |
| 78   | Intervention required                 | No action                   |
| 91   | Issuer or switch inoperative          | Decline - retry             |
| 96   | System malfunction                    | Decline                     |

## 13. Network Management Messages

Network management messages (08xx) carry session establishment, key exchange, echo test, and sign-off functions. They are identified by Field 70 (Network Management Information Code):

| NMIC | Function              |
|------|-----------------------|
| 001  | Sign On               |
| 002  | Sign Off              |
| 161  | Session Key Change    |
| 301  | Echo Test             |

### 13.1 Network Management Message Fields

| Field | Name                                 | 0800 | 0810 | 0820 | 0830 |
|-------|--------------------------------------|------|------|------|------|
| 007   | Transmission Date & Time             | M    | M    | M    | M    |
| 011   | STAN                                 | M    | M    | M    | M    |
| 033   | Forwarding Institution ID            | M    | M    | M    | M    |
| 039   | Response Code                        | -    | M    | -    | M    |
| 048   | Additional Data - Private            | C    | C    | C    | -    |
| 053   | Security Related Control Information | -    | -    | M    | M    |
| 070   | Network Management Information Code  | M    | M    | M    | M    |
| 100   | Receiving Institution ID             | M    | M    | M    | M    |

## 14. Reconciliation Messages

Reconciliation (05xx) messages carry settlement totals for balancing between acquirers, the hub, and issuers.

| Field | Name                                 | 0520/0521 | 0530 |
|-------|--------------------------------------|-----------|------|
| 003   | Processing Code                      | M         | M    |
| 007   | Transmission Date & Time             | M         | M    |
| 011   | STAN                                 | M         | M    |
| 015   | Date, Settlement                     | M         | M    |
| 032   | Acquiring Institution ID             | M         | M    |
| 033   | Forwarding Institution ID            | M         | M    |
| 039   | Response Code                        | -         | M    |
| 053   | Security Related Control Information | M         | M    |
| 066   | Settlement Code                      | M         | -    |
| 070   | Network Management Information Code  | M         | M    |
| 100   | Receiving Institution ID             | -         | M    |
| 128   | MAC                                  | M         | M    |

## 15. Encoding Rules Summary

### 15.1 Numeric (n) Fields

- BCD packed: two decimal digits per byte.
- Odd-length values: right-justified within the byte, left nibble padded with 0.
- Example: `"123"` encodes as `0x01 0x23`.

### 15.2 Alphanumeric (a, an, ans) Fields

- ASCII encoded, one byte per character.
- Most significant bit of each byte set to zero.
- Fixed-length fields are right-padded with spaces (0x20).

### 15.3 Binary (b) Fields

- Raw binary data. Length defined in bits but must be a multiple of 8.
- Stored and returned as `bytes`.

### 15.4 Track 2 (z) Fields

- BCD-like encoding, 2 symbols per byte.
- Uses ISO 7813 character set including digits 0-9 and separator `D` (0xD).

### 15.5 Signed Amount (x+n) Fields

- First byte: ASCII `'C'` (0x43) for credit or `'D'` (0x44) for debit.
- Remaining bytes: BCD-packed numeric digits.
- When amount is zero, sign may be either `'C'` or `'D'`.

### 15.6 Signed Amount Nibble (x+n*) Fields

- BCD-packed, but first nibble may be `0x0` (unsigned), `0xC` (credit), or `0xD` (debit).
- Remaining nibbles are numeric digits.

### 15.7 Variable-Length Field Prefixes

- **LLVAR**: 2-digit BCD length prefix (1 byte).
- **LLLVAR**: 3-digit BCD length prefix (2 bytes, left-padded with 0 nibble).
- The length value represents the number of bytes of field data following the prefix for binary fields, or the number of characters/digits for other types.

## 16. MAC Calculation Scope

While the library does not perform MAC calculations, it must support:
- Identifying the MAC field position (Field 64 or Field 128).
- Providing the raw message bytes excluding the MAC field value for external MAC calculation.
- The MAC is calculated over all bytes from the MTI through to (but not including) the MAC field itself, excluding the 2-byte length header.
- Per AS2805.2-2007 clause 2.3, the repeat bit is excluded from MAC calculations (i.e., 0220 and 0221 produce the same MAC input).

## 17. Constraints and Assumptions

- All messages conform to AS2805.2-2007 as profiled by eLS V23.04.01.
- The library is encoding-agnostic at the transport level; it operates on `bytes` objects.
- Field values are validated against their type and length constraints during both packing and unpacking.
- The library does not enforce message-level field presence rules (M/C/O) — that is the responsibility of the application layer.
- Python 3.10+ is required.

## 18. References

- AS 2805.2-2015 (Incorporating Amendment Nos 1 and 2)
- eftpos Hub Link Specification (eLS) V23.04.01
- ISO/IEC 7816 (BER-TLV encoding)
- ISO/IEC 646 (ASCII character set)
- ISO 7813 (Track 2 data format)
- EMVCo Payment Tokenisation Specification Technical Framework v2.0
