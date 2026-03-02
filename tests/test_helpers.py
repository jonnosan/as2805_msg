"""Tests for as2805_msg.helpers — human-friendly value objects."""

from decimal import Decimal

from as2805_msg import AS2805Message
from as2805_msg.helpers import Amount, POSEntryModeInfo, ProcessingCode, ResponseCodeInfo


class TestAmount:
    def test_cents(self):
        a = Amount(raw="000000010000")
        assert a.cents == 10000

    def test_dollars(self):
        a = Amount(raw="000000010000")
        assert a.dollars == Decimal("100.00")

    def test_str(self):
        a = Amount(raw="000000010050")
        assert str(a) == "$100.50"

    def test_zero(self):
        a = Amount(raw="000000000000")
        assert a.cents == 0
        assert a.dollars == Decimal("0.00")


class TestProcessingCode:
    def test_purchase_from_savings(self):
        pc = ProcessingCode(raw="003000")
        assert pc.transaction_type == "00"
        assert pc.source_account == "30"
        assert pc.destination_account == "00"
        assert "Purchase" in pc.transaction_type_name
        assert "Credit" in pc.source_account_name

    def test_str(self):
        pc = ProcessingCode(raw="003000")
        s = str(pc)
        assert "Purchase" in s

    def test_refund(self):
        pc = ProcessingCode(raw="200000")
        assert pc.transaction_type == "20"
        assert "Refund" in pc.transaction_type_name


class TestResponseCodeInfo:
    def test_approved(self):
        rc = ResponseCodeInfo(code="00")
        assert rc.is_approved
        assert rc.description == "Approved"
        assert rc.action == "Complete"

    def test_declined(self):
        rc = ResponseCodeInfo(code="05")
        assert not rc.is_approved
        assert "not honour" in rc.description.lower() or "Do not honour" in rc.description

    def test_str(self):
        rc = ResponseCodeInfo(code="00")
        assert "00" in str(rc)
        assert "Approved" in str(rc)


class TestPOSEntryModeInfo:
    def test_chip(self):
        info = POSEntryModeInfo(raw="051")
        assert "Chip" in info.entry_mode_name
        assert "PIN" in info.pin_capability_name

    def test_properties(self):
        info = POSEntryModeInfo(raw="051")
        assert info.entry_mode == "05"
        assert info.pin_capability == "1"


class TestMessageProperties:
    def test_amount_property(self):
        msg = AS2805Message(mti="0200", fields={4: "000000010000"})
        assert msg.amount is not None
        assert msg.amount.cents == 10000

    def test_amount_none_when_missing(self):
        msg = AS2805Message(mti="0200")
        assert msg.amount is None

    def test_processing_code_property(self):
        msg = AS2805Message(mti="0200", fields={3: "003000"})
        assert msg.processing_code is not None
        assert "Purchase" in msg.processing_code.transaction_type_name

    def test_response_code_property(self):
        msg = AS2805Message(mti="0210", fields={39: "00"})
        assert msg.response_code is not None
        assert msg.response_code.is_approved

    def test_pos_entry_mode_property(self):
        msg = AS2805Message(mti="0200", fields={22: "051"})
        assert msg.pos_entry_mode is not None
        assert "Chip" in msg.pos_entry_mode.entry_mode_name
