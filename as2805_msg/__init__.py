"""as2805-msg — encode and decode AS2805.2 financial messages."""

from .async_stream import AsyncAS2805Stream
from .bitmap import build_bitmap, parse_bitmap
from .builders import MessageBuilder
from .codec import bcd_decode, bcd_encode
from .constants import (
    NMIC,
    MTI,
    AccountType,
    POSConditionCode,
    POSEntryMode,
    ResponseCode,
    TransactionType,
)
from .dump import dump, dump_raw
from .errors import (
    AS2805BitmapError,
    AS2805BuildError,
    AS2805Error,
    AS2805FieldError,
    AS2805ParseError,
)
from .fields import Field47, Field48, Field55, Field90, Field111, DataSet, Field113
from .helpers import Amount, POSEntryModeInfo, ProcessingCode, ResponseCodeInfo
from .message import AS2805Message
from .schema import ELS_SCHEMA, FieldSchema, FieldSpec
from .stream import AS2805Stream
from .validation import FIELD_RULES, ValidationError, validate_message

__all__ = [
    # Core
    "AS2805Message",
    "AS2805Stream",
    "AsyncAS2805Stream",
    # Fields
    "Field47",
    "Field48",
    "Field55",
    "Field90",
    "Field111",
    "DataSet",
    "Field113",
    # Schema
    "FieldSpec",
    "FieldSchema",
    "ELS_SCHEMA",
    # Errors
    "AS2805Error",
    "AS2805ParseError",
    "AS2805BuildError",
    "AS2805FieldError",
    "AS2805BitmapError",
    # Codec
    "bcd_encode",
    "bcd_decode",
    "build_bitmap",
    "parse_bitmap",
    # Constants
    "ResponseCode",
    "TransactionType",
    "AccountType",
    "POSEntryMode",
    "POSConditionCode",
    "NMIC",
    "MTI",
    # Helpers
    "Amount",
    "ProcessingCode",
    "ResponseCodeInfo",
    "POSEntryModeInfo",
    # Builders
    "MessageBuilder",
    # Dump
    "dump",
    "dump_raw",
    # Validation
    "validate_message",
    "ValidationError",
    "FIELD_RULES",
]
