"""Message-level field presence validation (M/C/O rules per MTI).

Each MTI has a set of rules mapping field numbers to:
- "M" = Mandatory (must be present)
- "C" = Conditional (may be required depending on context)
- "O" = Optional

Fields not listed for a given MTI are not expected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .message import AS2805Message


@dataclass
class ValidationError:
    """A single validation issue."""

    field: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"Field {self.field:03d} ({self.rule}): {self.message}"


# ---------------------------------------------------------------------------
# Field presence rules per MTI
# Keys are field numbers; values are "M", "C", or "O".
# Sourced from eLS V23.04.01 message summary tables.
# ---------------------------------------------------------------------------

_RULES_0100: dict[int, str] = {
    2: "M", 3: "M", 4: "M", 7: "M", 11: "M", 12: "M", 13: "M", 14: "C",
    18: "M", 22: "M", 23: "C", 25: "M", 28: "C", 32: "M", 35: "C",
    37: "M", 41: "M", 42: "M", 43: "M", 47: "C", 48: "C", 52: "C",
    53: "C", 55: "C", 57: "C", 64: "C", 111: "C", 113: "C", 128: "C",
}

_RULES_0110: dict[int, str] = {
    2: "C", 3: "M", 4: "M", 7: "M", 11: "M", 14: "C",
    25: "C", 28: "C", 30: "C", 32: "M", 37: "M", 38: "C",
    39: "M", 44: "C", 47: "C", 53: "C", 54: "C",
    55: "C", 58: "C", 59: "C", 64: "C", 111: "C", 113: "C", 128: "C",
}

_RULES_0200: dict[int, str] = {
    2: "M", 3: "M", 4: "M", 7: "M", 11: "M", 12: "M", 13: "M", 14: "C",
    15: "M", 18: "M", 22: "M", 23: "C", 25: "M", 28: "C", 32: "M", 35: "C",
    37: "M", 41: "M", 42: "M", 43: "M", 47: "C", 48: "C", 52: "C",
    53: "C", 55: "C", 57: "C", 64: "C", 111: "C", 113: "C", 128: "C",
}

_RULES_0210: dict[int, str] = {
    2: "C", 3: "M", 4: "M", 7: "M", 11: "M", 14: "C",
    15: "M", 25: "C", 28: "C", 30: "C", 32: "M", 37: "M", 38: "C",
    39: "M", 44: "C", 47: "C", 53: "C", 54: "C",
    55: "C", 57: "C", 58: "C", 59: "C", 64: "C", 111: "C", 113: "C", 128: "C",
}

_RULES_0220: dict[int, str] = {
    2: "M", 3: "M", 4: "M", 7: "M", 11: "M", 12: "M", 13: "M", 14: "C",
    15: "M", 18: "M", 22: "M", 23: "C", 25: "M", 28: "C", 32: "M", 35: "C",
    37: "M", 38: "C", 39: "M", 41: "M", 42: "M", 43: "M",
    47: "C", 48: "C", 52: "C", 53: "C", 55: "C", 57: "C", 64: "C", 111: "C", 113: "C", 128: "C",
}

_RULES_0221 = dict(_RULES_0220)  # Repeat has same layout

_RULES_0230: dict[int, str] = {
    3: "M", 7: "M", 11: "M", 32: "M", 39: "M", 53: "C", 64: "C", 111: "C", 128: "C",
}

_RULES_0420: dict[int, str] = {
    2: "M", 3: "M", 4: "M", 7: "M", 11: "M", 12: "M", 13: "M", 14: "C",
    15: "M", 18: "C", 22: "M", 23: "C", 25: "M", 28: "C", 32: "M", 35: "C",
    37: "M", 38: "C", 41: "M", 42: "M", 47: "C", 52: "C",
    53: "C", 55: "C", 57: "C", 90: "M", 95: "C", 64: "C", 111: "C", 113: "C", 128: "C",
}

_RULES_0421 = dict(_RULES_0420)  # Repeat has same layout

_RULES_0430: dict[int, str] = {
    3: "M", 7: "M", 11: "M", 32: "M", 39: "M", 53: "C", 64: "C", 111: "C", 128: "C",
}

_RULES_0520: dict[int, str] = {
    7: "M", 11: "M", 33: "M", 66: "M", 70: "C", 100: "M", 128: "C",
}

_RULES_0521 = dict(_RULES_0520)

_RULES_0530: dict[int, str] = {
    7: "M", 11: "M", 33: "M", 39: "M", 66: "C", 70: "C", 100: "M", 128: "C",
}

_RULES_0800: dict[int, str] = {
    7: "M", 11: "M", 33: "M", 48: "C", 53: "C", 70: "M", 100: "M", 111: "C", 128: "C",
}

_RULES_0810: dict[int, str] = {
    7: "M", 11: "M", 33: "M", 39: "M", 48: "C", 53: "C",
    70: "M", 100: "M", 111: "C", 128: "C",
}

_RULES_0820: dict[int, str] = {
    7: "M", 11: "M", 33: "M", 48: "C", 53: "C", 70: "M", 100: "M", 111: "C", 128: "C",
}

_RULES_0830: dict[int, str] = {
    7: "M", 11: "M", 33: "M", 39: "M", 53: "C", 70: "M", 100: "M", 111: "C", 128: "C",
}

FIELD_RULES: dict[str, dict[int, str]] = {
    "0100": _RULES_0100,
    "0110": _RULES_0110,
    "0200": _RULES_0200,
    "0210": _RULES_0210,
    "0220": _RULES_0220,
    "0221": _RULES_0221,
    "0230": _RULES_0230,
    "0420": _RULES_0420,
    "0421": _RULES_0421,
    "0430": _RULES_0430,
    "0520": _RULES_0520,
    "0521": _RULES_0521,
    "0530": _RULES_0530,
    "0800": _RULES_0800,
    "0810": _RULES_0810,
    "0820": _RULES_0820,
    "0830": _RULES_0830,
}


def validate_message(msg: AS2805Message) -> list[ValidationError]:
    """Validate field presence for a message based on its MTI.

    Returns an empty list if the message is valid, otherwise a list
    of :class:`ValidationError` instances describing each issue.
    """
    errors: list[ValidationError] = []

    rules = FIELD_RULES.get(msg.mti)
    if rules is None:
        errors.append(ValidationError(0, "MTI", f"No validation rules for MTI {msg.mti}"))
        return errors

    # Check mandatory fields are present
    for field_num, rule in rules.items():
        if rule == "M" and field_num not in msg.fields:
            errors.append(
                ValidationError(field_num, "M", "Mandatory field is missing")
            )

    # Check for unexpected fields (not in the rule set for this MTI)
    for field_num in msg.fields:
        if field_num not in rules:
            errors.append(
                ValidationError(field_num, "-", "Field not expected for this MTI")
            )

    return errors
