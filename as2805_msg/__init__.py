"""as2805-msg — encode and decode AS2805.2 financial messages."""

from .bitmap import build_bitmap, parse_bitmap
from .codec import bcd_decode, bcd_encode
from .errors import (
    AS2805BitmapError,
    AS2805BuildError,
    AS2805Error,
    AS2805FieldError,
    AS2805ParseError,
)
from .fields import Field47, Field55, Field90, Field113
from .message import AS2805Message
from .schema import ELS_SCHEMA, FieldSchema, FieldSpec
from .stream import AS2805Stream

__all__ = [
    "AS2805Message",
    "AS2805Stream",
    "Field47",
    "Field55",
    "Field90",
    "Field113",
    "FieldSpec",
    "FieldSchema",
    "ELS_SCHEMA",
    "AS2805Error",
    "AS2805ParseError",
    "AS2805BuildError",
    "AS2805FieldError",
    "AS2805BitmapError",
    "bcd_encode",
    "bcd_decode",
    "build_bitmap",
    "parse_bitmap",
]
