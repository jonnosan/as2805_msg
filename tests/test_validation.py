"""Tests for as2805_msg.validation — message-level field presence rules."""

from as2805_msg import AS2805Message, validate_message, ValidationError


class TestValidateMessage:
    def test_valid_0800_sign_on(self):
        msg = AS2805Message(mti="0800", fields={
            7: "0302120000",
            11: "000001",
            33: "12345",
            70: "001",
            100: "67890",
        })
        errors = validate_message(msg)
        assert errors == []

    def test_missing_mandatory_field(self):
        msg = AS2805Message(mti="0800", fields={
            7: "0302120000",
            11: "000001",
            # missing 33, 70, 100
        })
        errors = validate_message(msg)
        missing = {e.field for e in errors if e.rule == "M"}
        assert 33 in missing
        assert 70 in missing
        assert 100 in missing

    def test_unexpected_field(self):
        msg = AS2805Message(mti="0800", fields={
            7: "0302120000",
            11: "000001",
            33: "12345",
            43: "SHOULD NOT BE HERE",  # not expected for 0800
            70: "001",
            100: "67890",
        })
        errors = validate_message(msg)
        unexpected = [e for e in errors if e.rule == "-"]
        assert len(unexpected) == 1
        assert unexpected[0].field == 43

    def test_unknown_mti(self):
        msg = AS2805Message(mti="9999")
        errors = validate_message(msg)
        assert len(errors) == 1
        assert "No validation rules" in errors[0].message

    def test_valid_0200_purchase(self):
        msg = AS2805Message(mti="0200", fields={
            2: "4111111111111111",
            3: "003000",
            4: "000000010000",
            7: "0302120000",
            11: "000001",
            12: "120000",
            13: "0302",
            15: "0302",
            18: "5411",
            22: "051",
            25: "00",
            32: "12345",
            37: "000000000001",
            41: "TERM0001",
            42: "MERCHANT0000001",
            43: "GROCERY STORE           SYDNEY      AU",
            53: "2600000000000000",
        })
        errors = validate_message(msg)
        assert errors == []

    def test_0810_response(self):
        msg = AS2805Message(mti="0810", fields={
            7: "0302120000",
            11: "000001",
            33: "12345",
            39: "00",
            70: "001",
            100: "67890",
        })
        errors = validate_message(msg)
        assert errors == []


class TestMessageValidateMethod:
    def test_validate_via_method(self):
        msg = AS2805Message(mti="0800", fields={
            7: "0302120000",
            11: "000001",
            33: "12345",
            70: "001",
            100: "67890",
        })
        assert msg.validate() == []


class TestValidationError:
    def test_str(self):
        err = ValidationError(field=7, rule="M", message="Mandatory field is missing")
        assert "007" in str(err)
        assert "Mandatory" in str(err)
