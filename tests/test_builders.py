"""Tests for as2805_msg.builders — message factory helpers."""

from as2805_msg import AS2805Message, MessageBuilder


class TestSignOn:
    def test_sign_on_creates_0800(self):
        msg = MessageBuilder.sign_on("12345", "67890", stan="000001")
        assert msg.mti == "0800"
        assert msg[70] == "001"
        assert msg[33] == "12345"
        assert msg[100] == "67890"
        assert msg[11] == "000001"
        assert 7 in msg

    def test_sign_on_auto_stan(self):
        msg = MessageBuilder.sign_on("12345", "67890")
        assert len(msg[11]) == 6
        assert msg[11].isdigit()


class TestSignOnResponse:
    def test_sign_on_response(self):
        req = MessageBuilder.sign_on("12345", "67890", stan="000001")
        resp = MessageBuilder.sign_on_response(req)
        assert resp.mti == "0810"
        assert resp[39] == "00"
        assert resp[70] == "001"
        assert resp[11] == "000001"
        assert resp[33] == "12345"

    def test_custom_response_code(self):
        req = MessageBuilder.sign_on("12345", "67890", stan="000001")
        resp = MessageBuilder.sign_on_response(req, response_code="05")
        assert resp[39] == "05"


class TestEchoTest:
    def test_echo_test_creates_0800(self):
        msg = MessageBuilder.echo_test("12345", "67890", stan="000002")
        assert msg.mti == "0800"
        assert msg[70] == "301"
        assert msg[11] == "000002"


class TestSignOff:
    def test_sign_off_creates_0800(self):
        msg = MessageBuilder.sign_off("12345", "67890", stan="000003")
        assert msg.mti == "0800"
        assert msg[70] == "002"


class TestReversalFrom:
    def test_reversal_from_0200(self):
        original = AS2805Message(mti="0200", fields={
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
            53: "2600000000000000",
        })

        rev = MessageBuilder.reversal_from(original)
        assert rev.mti == "0420"
        assert rev[2] == "4111111111111111"
        assert rev[4] == "000000010000"
        assert 90 in rev  # Original Data Elements

    def test_reversal_preserves_fields(self):
        original = AS2805Message(mti="0200", fields={
            2: "4111111111111111",
            3: "003000",
            4: "000000010000",
            7: "0302120000",
            11: "000001",
            12: "120000",
            13: "0302",
            22: "051",
            25: "00",
            32: "12345",
            37: "000000000001",
            41: "TERM0001",
            42: "MERCHANT0000001",
            53: "2600000000000000",
        })
        rev = MessageBuilder.reversal_from(original)
        assert rev[22] == "051"
        assert rev[25] == "00"


class TestAdviceFrom:
    def test_advice_from_0200(self):
        original = AS2805Message(mti="0200", fields={
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

        adv = MessageBuilder.advice_from(original)
        assert adv.mti == "0220"
        assert adv[39] == "00"
        assert adv[2] == "4111111111111111"
        assert adv[43] == "GROCERY STORE           SYDNEY      AU"

    def test_advice_custom_response(self):
        original = AS2805Message(mti="0200", fields={
            2: "4111111111111111",
            3: "003000",
            4: "000000010000",
            7: "0302120000",
            11: "000001",
            12: "120000",
            13: "0302",
            22: "051",
            25: "00",
            32: "12345",
            37: "000000000001",
            41: "TERM0001",
            42: "MERCHANT0000001",
            43: "GROCERY STORE           SYDNEY      AU",
            53: "2600000000000000",
        })
        adv = MessageBuilder.advice_from(original, response_code="05")
        assert adv[39] == "05"
