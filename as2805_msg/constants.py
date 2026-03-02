"""Reference constants for AS2805 message fields — response codes, transaction types, etc."""


class ResponseCode:
    """Field 39 response code lookup."""

    # code -> (description, action)
    CODES: dict[str, tuple[str, str]] = {
        "00": ("Approved", "Complete"),
        "01": ("Refer to Card Issuer", "Decline"),
        "04": ("Pick up card", "Decline, retain card"),
        "05": ("Do not Honour", "Decline"),
        "06": ("Error", "Decline"),
        "08": ("Honour with signature", "Approve after signature"),
        "12": ("Invalid Transaction", "Decline"),
        "13": ("Invalid Amount", "Decline"),
        "14": ("Invalid Card Number", "Decline"),
        "15": ("No such Issuer", "Decline"),
        "19": ("Re-enter transaction", "Decline, retry"),
        "21": ("No action taken", "Unmatched reversal"),
        "30": ("Format Error", "Decline"),
        "31": ("Bank not supported by switch", "Decline"),
        "33": ("Expired card", "Decline, retain card"),
        "34": ("Suspected fraud", "Decline, retain card"),
        "36": ("Restricted card", "Decline, retain card"),
        "38": ("Allowable PIN tries exceeded", "Decline, retain card"),
        "39": ("No Credit Account", "Decline"),
        "40": ("Requested Function Not supported", "Decline"),
        "41": ("Lost card", "Decline, retain card"),
        "43": ("Stolen card", "Decline, retain card"),
        "44": ("No Investment account", "Decline"),
        "51": ("Not sufficient funds", "Decline"),
        "52": ("No Cheque account", "Decline"),
        "53": ("No Savings account", "Decline"),
        "54": ("Expired card", "Decline"),
        "55": ("Invalid PIN", "Decline"),
        "56": ("No card record", "Decline"),
        "57": ("Transaction not permitted to Cardholder", "Decline"),
        "58": ("Transaction not permitted to terminal", "Decline"),
        "59": ("Suspected Fraud", "Decline"),
        "61": ("Exceeds withdrawal amount limits", "Decline"),
        "64": ("Original amount incorrect", "Decline"),
        "65": ("Exceeds Withdrawal Frequency Limit", "Decline"),
        "67": ("Hot Card", "Decline, retain card"),
        "75": ("PIN tries exceeded", "Decline"),
        "76": ("Approved, no original found", "Complete"),
        "77": ("Intervention required, sign off", "Re-sign-on"),
        "78": ("Intervention required", "No action"),
        "91": ("Issuer not available", "Decline, retry"),
        "92": ("No route", "Decline"),
        "94": ("Duplicate transmission", "Decline"),
        "95": ("Reconcile error", "Reconcile"),
        "96": ("System malfunction", "Decline"),
        "97": ("Settlement date advanced", "Complete"),
        "98": ("MAC error", "Decline, request key change"),
    }

    @classmethod
    def lookup(cls, code: str) -> tuple[str, str]:
        """Return (description, action) for a response code, or defaults."""
        return cls.CODES.get(code, (f"Unknown ({code})", "Unknown"))


class TransactionType:
    """Field 3 positions 1-2: transaction type codes."""

    PURCHASE = "00"
    CASH_OUT = "01"
    PURCHASE_CASH_OUT = "09"
    REFUND = "20"
    DEPOSIT = "21"
    BALANCE_ENQUIRY = "30"
    BALANCE_ENQUIRY_ALT = "31"
    ACCOUNT_VERIFY = "33"

    NAMES: dict[str, str] = {
        "00": "Purchase",
        "01": "Cash-out",
        "09": "Purchase with Cash-out",
        "20": "Refund",
        "21": "Deposit",
        "30": "Balance Enquiry",
        "31": "Balance Enquiry",
        "33": "Account Verify",
    }

    @classmethod
    def name(cls, code: str) -> str:
        return cls.NAMES.get(code, f"Unknown ({code})")


class AccountType:
    """Field 3 positions 3-4 (source) and 5-6 (destination): account type codes."""

    DEFAULT = "00"
    SAVINGS = "10"
    CHEQUE = "20"
    CREDIT = "30"

    NAMES: dict[str, str] = {
        "00": "Default",
        "10": "Savings",
        "20": "Cheque",
        "30": "Credit",
    }

    @classmethod
    def name(cls, code: str) -> str:
        return cls.NAMES.get(code, f"Unknown ({code})")


class POSEntryMode:
    """Field 22 POS entry mode codes (3 digits: 2-digit entry mode + 1-digit PIN capability)."""

    CNP = "010"
    MANUAL = "012"
    MAGSTRIPE = "021"
    CHIP_PIN = "051"
    CHIP_NO_PIN = "052"
    CONTACTLESS = "071"
    CONTACTLESS_NO_PIN = "072"

    ENTRY_NAMES: dict[str, str] = {
        "01": "Card Not Present",
        "02": "Magstripe (unspecified)",
        "05": "Chip",
        "07": "Contactless",
        "09": "No terminal used",
    }

    PIN_NAMES: dict[str, str] = {
        "0": "CNP / Unknown",
        "1": "PIN entry capable",
        "2": "No PIN entry capability",
    }

    @classmethod
    def entry_name(cls, code: str) -> str:
        """Describe the entry mode from the first 2 digits of Field 22."""
        return cls.ENTRY_NAMES.get(code[:2], f"Unknown ({code[:2]})")

    @classmethod
    def pin_name(cls, code: str) -> str:
        """Describe PIN capability from the 3rd digit of Field 22."""
        return cls.PIN_NAMES.get(code[2:], f"Unknown ({code[2:]})")


class POSConditionCode:
    """Field 25 POS condition codes."""

    NORMAL = "00"
    CARDHOLDER_NOT_PRESENT = "01"
    MOTO = "08"
    RECURRING = "48"
    INSTALMENT = "74"

    NAMES: dict[str, str] = {
        "00": "Normal",
        "01": "Cardholder not present",
        "08": "Mail/telephone order",
        "48": "Recurring payment",
        "74": "Instalment payment",
    }

    @classmethod
    def name(cls, code: str) -> str:
        return cls.NAMES.get(code, f"Unknown ({code})")


class NMIC:
    """Field 70 Network Management Information Codes."""

    SIGN_ON = "001"
    SIGN_OFF = "002"
    SESSION_KEY_CHANGE = "161"
    ECHO_TEST = "301"

    NAMES: dict[str, str] = {
        "001": "Sign On",
        "002": "Sign Off",
        "161": "Session Key Change",
        "301": "Echo Test",
    }

    @classmethod
    def name(cls, code: str) -> str:
        return cls.NAMES.get(code, f"Unknown ({code})")


class MTI:
    """Message Type Indicator constants."""

    AUTH_REQUEST = "0100"
    AUTH_RESPONSE = "0110"
    TD_ADVICE = "0120"
    TD_ADVICE_REPEAT = "0121"
    TD_ADVICE_RESPONSE = "0130"
    FINANCIAL_REQUEST = "0200"
    FINANCIAL_RESPONSE = "0210"
    FINANCIAL_ADVICE = "0220"
    FINANCIAL_ADVICE_REPEAT = "0221"
    FINANCIAL_ADVICE_RESPONSE = "0230"
    REVERSAL_ADVICE = "0420"
    REVERSAL_ADVICE_REPEAT = "0421"
    REVERSAL_RESPONSE = "0430"
    RECON_ADVICE = "0520"
    RECON_ADVICE_REPEAT = "0521"
    RECON_RESPONSE = "0530"
    NETWORK_REQUEST = "0800"
    NETWORK_RESPONSE = "0810"
    NETWORK_ADVICE = "0820"
    NETWORK_ADVICE_RESPONSE = "0830"

    NAMES: dict[str, str] = {
        "0100": "Authorisation Request",
        "0110": "Authorisation Response",
        "0120": "Transaction Disposition Advice",
        "0121": "Transaction Disposition Advice Repeat",
        "0130": "Transaction Disposition Advice Response",
        "0200": "Financial Transaction Request",
        "0210": "Financial Transaction Request Response",
        "0220": "Financial Transaction Advice",
        "0221": "Financial Transaction Advice Repeat",
        "0230": "Financial Transaction Advice Response",
        "0420": "Acquirer Reversal Advice",
        "0421": "Acquirer Reversal Advice Repeat",
        "0430": "Acquirer Reversal Advice Response",
        "0520": "Acquirer Reconciliation Advice",
        "0521": "Acquirer Reconciliation Advice Repeat",
        "0530": "Acquirer Reconciliation Advice Response",
        "0800": "Network Management Request",
        "0810": "Network Management Request Response",
        "0820": "Network Management Advice",
        "0830": "Network Management Advice Response",
    }

    @classmethod
    def name(cls, code: str) -> str:
        return cls.NAMES.get(code, f"Unknown MTI ({code})")
