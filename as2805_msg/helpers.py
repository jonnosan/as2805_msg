"""Human-friendly value objects for interpreted AS2805 field values."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .constants import AccountType, POSEntryMode, ResponseCode, TransactionType


@dataclass
class Amount:
    """Parsed from Field 4 or 57 (12-digit string representing cents)."""

    raw: str

    @property
    def cents(self) -> int:
        return int(self.raw)

    @property
    def dollars(self) -> Decimal:
        return Decimal(self.raw) / 100

    def __str__(self) -> str:
        return f"${self.dollars:,.2f}"


@dataclass
class ProcessingCode:
    """Parsed from Field 3 (6-digit string)."""

    raw: str

    @property
    def transaction_type(self) -> str:
        """Positions 1-2: transaction type code."""
        return self.raw[:2]

    @property
    def source_account(self) -> str:
        """Positions 3-4: source account type."""
        return self.raw[2:4]

    @property
    def destination_account(self) -> str:
        """Positions 5-6: destination account type."""
        return self.raw[4:6]

    @property
    def transaction_type_name(self) -> str:
        return TransactionType.name(self.transaction_type)

    @property
    def source_account_name(self) -> str:
        return AccountType.name(self.source_account)

    @property
    def destination_account_name(self) -> str:
        return AccountType.name(self.destination_account)

    def __str__(self) -> str:
        return (
            f"{self.transaction_type_name} "
            f"from {self.source_account_name} "
            f"to {self.destination_account_name}"
        )


@dataclass
class ResponseCodeInfo:
    """Parsed from Field 39 (2-character string)."""

    code: str

    @property
    def description(self) -> str:
        return ResponseCode.lookup(self.code)[0]

    @property
    def action(self) -> str:
        return ResponseCode.lookup(self.code)[1]

    @property
    def is_approved(self) -> bool:
        return self.code == "00"

    def __str__(self) -> str:
        return f"{self.code} — {self.description}"


@dataclass
class POSEntryModeInfo:
    """Parsed from Field 22 (3-digit string)."""

    raw: str

    @property
    def entry_mode(self) -> str:
        """First 2 digits."""
        return self.raw[:2]

    @property
    def pin_capability(self) -> str:
        """3rd digit."""
        return self.raw[2:]

    @property
    def entry_mode_name(self) -> str:
        return POSEntryMode.entry_name(self.raw)

    @property
    def pin_capability_name(self) -> str:
        return POSEntryMode.pin_name(self.raw)

    def __str__(self) -> str:
        return f"{self.entry_mode_name}, {self.pin_capability_name}"
