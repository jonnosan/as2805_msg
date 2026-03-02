"""Integration tests — realistic full message round-trips."""

from as2805_msg import AS2805Message, AS2805Stream, Field47, Field55, Field90


class TestPOSPurchaseMessage:
    """Build a realistic 0200 POS purchase message, pack/unpack, verify."""

    def test_full_pos_purchase_roundtrip(self):
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"                             # Purchase, default accounts
        msg[4] = "000000005000"                       # $50.00
        msg[7] = "0302120000"                         # Transmission date/time
        msg[11] = "000001"                            # STAN
        msg[12] = "120000"                            # Local time
        msg[13] = "0302"                              # Local date
        msg[14] = "2512"                              # Expiry
        msg[15] = "0302"                              # Settlement date
        msg[18] = "5411"                              # MCC: grocery
        msg[22] = "051"                               # POS entry: chip + PIN
        msg[25] = "00"                                # POS condition code
        msg[32] = "123456"                            # Acquiring institution
        msg[35] = "4987654321098769D2512"             # Track 2
        msg[37] = "000000000001"                      # RRN
        msg[41] = "TERM0001"                          # Terminal ID
        msg[42] = "MERCHANT0000001"                   # Merchant ID
        msg[43] = "GROCERY STORE           SYDNEY      AU"  # 40 chars
        msg[47] = "TCCR2\\PCA2000\\FCA01\\"              # Field 47 sub-elements
        msg[52] = b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0"  # PIN block
        msg[53] = "0000000000000001"                  # Security control (key set 1)
        msg[57] = "000000000000"                      # Cash amount = 0
        msg[64] = b"\x00" * 8                         # MAC placeholder

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)

        # Verify all fields
        assert msg2.mti == "0200"
        assert msg2[3] == "000000"
        assert msg2[4] == "000000005000"
        assert msg2[7] == "0302120000"
        assert msg2[11] == "000001"
        assert msg2[12] == "120000"
        assert msg2[13] == "0302"
        assert msg2[14] == "2512"
        assert msg2[15] == "0302"
        assert msg2[18] == "5411"
        assert msg2[22] == "051"
        assert msg2[25] == "00"
        assert msg2[32] == "123456"
        assert msg2[35] == "4987654321098769D2512"
        assert msg2[37] == "000000000001"
        assert msg2[41] == "TERM0001"
        assert msg2[42] == "MERCHANT0000001"
        assert msg2[43] == "GROCERY STORE           SYDNEY      AU"
        assert msg2[47] == "TCCR2\\PCA2000\\FCA01\\"
        assert msg2[52] == b"\x12\x34\x56\x78\x9A\xBC\xDE\xF0"
        assert msg2[53] == "0000000000000001"
        assert msg2[57] == "000000000000"
        assert msg2[64] == b"\x00" * 8

    def test_field47_subfield_parsing(self):
        """Parse Field 47 sub-elements from a packed message."""
        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        msg[4] = "000000001000"
        msg[47] = "TCCR2\\PCA2000\\FCA01\\"
        msg[53] = "0000000000000001"

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)

        tags = Field47.unpack(msg2[47].encode("ascii"))
        assert tags["TCC"] == b"R2"
        assert tags["PCA"] == b"2000"
        assert tags["FCA"] == b"01"

    def test_field55_emv_data_roundtrip(self):
        """Pack a message with EMV data in Field 55."""
        # Build some realistic EMV TLV data
        emv_elements = {
            b"\x9f\x26": b"\x11\x22\x33\x44\x55\x66\x77\x88",  # AC
            b"\x9f\x27": b"\x80",                                 # CID
            b"\x9f\x10": b"\x06\x01\x0a\x03\xa4\x80\x00",       # IAD
            b"\x9f\x37": b"\xAA\xBB\xCC\xDD",                    # UN
            b"\x9f\x36": b"\x00\x01",                             # ATC
            b"\x82": b"\x19\x80",                                  # AIP
        }
        emv_data = Field55.pack(emv_elements)

        msg = AS2805Message(mti="0200")
        msg[3] = "000000"
        msg[4] = "000000005000"
        msg[55] = emv_data
        msg[53] = "0000000000000001"
        msg[128] = b"\x00" * 8

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)

        parsed_emv = Field55.unpack(msg2[55])
        assert parsed_emv[b"\x9f\x26"] == b"\x11\x22\x33\x44\x55\x66\x77\x88"
        assert parsed_emv[b"\x9f\x27"] == b"\x80"
        assert parsed_emv[b"\x82"] == b"\x19\x80"


class TestNetworkManagementMessage:
    def test_sign_on_request(self):
        msg = AS2805Message(mti="0800")
        msg[7] = "0302120000"
        msg[11] = "000001"
        msg[33] = "123456"
        msg[70] = "001"         # Sign On
        msg[100] = "999999"

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)

        assert msg2.mti == "0800"
        assert msg2[70] == "001"
        assert msg2[100] == "999999"

    def test_sign_on_response(self):
        msg = AS2805Message(mti="0810")
        msg[7] = "0302120000"
        msg[11] = "000001"
        msg[33] = "123456"
        msg[39] = "00"          # Approved
        msg[70] = "001"
        msg[100] = "999999"

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)

        assert msg2.mti == "0810"
        assert msg2[39] == "00"

    def test_echo_test(self):
        msg = AS2805Message(mti="0800")
        msg[7] = "0302120000"
        msg[11] = "000002"
        msg[33] = "123456"
        msg[70] = "301"         # Echo Test
        msg[100] = "999999"

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)
        assert msg2[70] == "301"


class TestReversalMessage:
    def test_reversal_with_field90(self):
        msg = AS2805Message(mti="0420")
        msg[3] = "000000"
        msg[4] = "000000005000"
        msg[7] = "0302120100"
        msg[11] = "000002"
        msg[12] = "120100"
        msg[13] = "0302"
        msg[15] = "0302"
        msg[22] = "051"
        msg[25] = "00"
        msg[32] = "123456"
        msg[37] = "000000000001"
        msg[41] = "TERM0001"
        msg[42] = "MERCHANT0000001"
        msg[53] = "0000000000000001"
        msg[57] = "000000000000"
        # Field 90: original data elements
        msg[90] = Field90.pack({
            "mti": "0200",
            "stan": "000001",
            "transmission_dt": "0302120000",
            "acq_inst": "123456",
            "fwd_inst": "0",
        })
        msg[128] = b"\x00" * 8

        raw = msg.pack()
        msg2 = AS2805Message.unpack(raw)

        assert msg2.mti == "0420"
        assert msg2[90] is not None

        f90 = Field90.unpack(msg2[90])
        assert f90["mti"] == "0200"
        assert f90["stan"] == "000001"
        assert f90["transmission_dt"] == "0302120000"


class TestStreamIntegration:
    def test_multiple_messages_in_stream(self):
        msgs = []
        for i in range(5):
            m = AS2805Message(mti="0200")
            m[3] = "000000"
            m[4] = "000000001000"
            m[11] = str(i + 1).zfill(6)
            msgs.append(m)

        buffer = b"".join(AS2805Stream.write_message(m) for m in msgs)
        parsed = AS2805Stream.read_all(buffer)

        assert len(parsed) == 5
        for i, m in enumerate(parsed):
            assert m[11] == str(i + 1).zfill(6)


class TestMACInputIntegration:
    def test_mac_input_for_advice_repeat(self):
        """Verify 0420 and 0421 produce same MAC input."""
        fields = {
            3: "000000",
            4: "000000005000",
            7: "0302120000",
            11: "000001",
            32: "123456",
            53: "0000000000000001",
            128: b"\x00" * 8,
        }
        msg_420 = AS2805Message(mti="0420", fields=dict(fields))
        msg_421 = AS2805Message(mti="0421", fields=dict(fields))

        assert msg_420.mac_input() == msg_421.mac_input()
