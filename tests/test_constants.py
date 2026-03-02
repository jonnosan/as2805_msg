"""Tests for as2805_msg.constants — reference data lookups."""

from as2805_msg import (
    MTI,
    NMIC,
    AccountType,
    POSConditionCode,
    POSEntryMode,
    ResponseCode,
    TransactionType,
)


class TestResponseCode:
    def test_approved(self):
        desc, action = ResponseCode.lookup("00")
        assert desc == "Approved"
        assert action == "Complete"

    def test_nsf(self):
        desc, action = ResponseCode.lookup("51")
        assert desc == "Not sufficient funds"
        assert action == "Decline"

    def test_unknown_code(self):
        desc, action = ResponseCode.lookup("ZZ")
        assert "Unknown" in desc
        assert action == "Unknown"

    def test_all_codes_have_descriptions(self):
        for code, (desc, action) in ResponseCode.CODES.items():
            assert len(code) == 2
            assert desc
            assert action


class TestTransactionType:
    def test_purchase(self):
        assert TransactionType.name("00") == "Purchase"

    def test_refund(self):
        assert TransactionType.name("20") == "Refund"

    def test_unknown(self):
        assert "Unknown" in TransactionType.name("99")


class TestAccountType:
    def test_savings(self):
        assert AccountType.name("10") == "Savings"

    def test_credit(self):
        assert AccountType.name("30") == "Credit"


class TestPOSEntryMode:
    def test_chip_entry(self):
        name = POSEntryMode.entry_name("051")
        assert "Chip" in name

    def test_pin_capable(self):
        name = POSEntryMode.pin_name("051")
        assert "PIN" in name

    def test_contactless(self):
        name = POSEntryMode.entry_name("071")
        assert "Contactless" in name


class TestPOSConditionCode:
    def test_normal(self):
        assert POSConditionCode.name("00") == "Normal"

    def test_moto(self):
        assert "Mail" in POSConditionCode.name("08") or "telephone" in POSConditionCode.name("08")


class TestNMIC:
    def test_sign_on(self):
        assert NMIC.name("001") == "Sign On"

    def test_echo_test(self):
        assert NMIC.name("301") == "Echo Test"


class TestMTI:
    def test_financial_request(self):
        name = MTI.name("0200")
        assert "Financial" in name

    def test_network_request(self):
        name = MTI.name("0800")
        assert "Network" in name

    def test_unknown_mti(self):
        assert "Unknown" in MTI.name("9999")
