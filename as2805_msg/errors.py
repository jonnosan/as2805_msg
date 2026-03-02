"""Exception hierarchy for as2805-msg."""


class AS2805Error(Exception):
    """Base exception for all AS2805 library errors."""


class AS2805ParseError(AS2805Error):
    """Error decoding a message from bytes."""


class AS2805BuildError(AS2805Error):
    """Error encoding a message to bytes."""


class AS2805FieldError(AS2805Error):
    """Invalid field data (wrong type, length, or value)."""

    def __init__(self, field_number: int, message: str):
        self.field_number = field_number
        super().__init__(f"Field {field_number:03d}: {message}")


class AS2805BitmapError(AS2805Error):
    """Corrupt or inconsistent bitmap."""
