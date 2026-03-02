"""Factory helpers for building common AS2805 messages."""

from __future__ import annotations

from datetime import datetime, timezone

from .fields.field90 import Field90
from .message import AS2805Message


def _now_fields() -> tuple[str, str, str, str]:
    """Return (transmission_dt, local_time, local_date, settlement_date) from current UTC time."""
    now = datetime.now(timezone.utc)
    transmission_dt = now.strftime("%m%d%H%M%S")
    local_time = now.strftime("%H%M%S")
    local_date = now.strftime("%m%d")
    settlement_date = now.strftime("%m%d")
    return transmission_dt, local_time, local_date, settlement_date


def _next_stan(counter: list[int] = [0]) -> str:
    """Simple incrementing STAN generator (wraps at 999999)."""
    counter[0] = (counter[0] % 999999) + 1
    return str(counter[0]).zfill(6)


class MessageBuilder:
    """Factory methods for common AS2805 network management messages."""

    @staticmethod
    def sign_on(
        institution_id: str,
        receiving_id: str,
        stan: str | None = None,
    ) -> AS2805Message:
        """Build a 0800 Sign On request."""
        msg = AS2805Message(mti="0800")
        transmission_dt, _, _, _ = _now_fields()
        msg[7] = transmission_dt
        msg[11] = stan or _next_stan()
        msg[33] = institution_id
        msg[70] = "001"  # Sign On
        msg[100] = receiving_id
        return msg

    @staticmethod
    def sign_on_response(
        request: AS2805Message,
        response_code: str = "00",
    ) -> AS2805Message:
        """Build a 0810 Sign On response from a request."""
        msg = AS2805Message(mti="0810")
        msg[7] = request[7]
        msg[11] = request[11]
        msg[33] = request[33]
        msg[39] = response_code
        msg[70] = request[70]
        msg[100] = request[100]
        return msg

    @staticmethod
    def echo_test(
        institution_id: str,
        receiving_id: str,
        stan: str | None = None,
    ) -> AS2805Message:
        """Build a 0800 Echo Test request."""
        msg = AS2805Message(mti="0800")
        transmission_dt, _, _, _ = _now_fields()
        msg[7] = transmission_dt
        msg[11] = stan or _next_stan()
        msg[33] = institution_id
        msg[70] = "301"  # Echo Test
        msg[100] = receiving_id
        return msg

    @staticmethod
    def sign_off(
        institution_id: str,
        receiving_id: str,
        stan: str | None = None,
    ) -> AS2805Message:
        """Build a 0800 Sign Off request."""
        msg = AS2805Message(mti="0800")
        transmission_dt, _, _, _ = _now_fields()
        msg[7] = transmission_dt
        msg[11] = stan or _next_stan()
        msg[33] = institution_id
        msg[70] = "002"  # Sign Off
        msg[100] = receiving_id
        return msg

    @staticmethod
    def reversal_from(original: AS2805Message) -> AS2805Message:
        """Build a 0420 Reversal from an original 0200 request.

        Auto-populates Field 90 (Original Data Elements) from the original message.
        Copies key fields from the original.
        """
        msg = AS2805Message(mti="0420")

        # Copy fields from original
        for f in (2, 3, 4, 7, 11, 12, 13, 14, 15, 18, 22, 23, 25, 28, 32, 35,
                  37, 41, 42, 47, 52, 53, 55, 57):
            if f in original:
                msg[f] = original[f]

        # Build Field 90 from original
        msg[90] = Field90.pack({
            "mti": original.mti,
            "stan": original[11],
            "transmission_dt": original[7],
            "acq_inst": original[32] if 32 in original else "0",
            "fwd_inst": original[33] if 33 in original else "0",
        })

        return msg

    @staticmethod
    def advice_from(
        original: AS2805Message,
        response_code: str = "00",
    ) -> AS2805Message:
        """Build a 0220 Financial Advice from an original 0200.

        Copies relevant fields and adds the response code.
        """
        msg = AS2805Message(mti="0220")

        # Copy fields from original
        for f in (2, 3, 4, 7, 11, 12, 13, 14, 15, 18, 22, 23, 25, 28, 32, 35,
                  37, 38, 41, 42, 43, 47, 48, 52, 53, 55, 57):
            if f in original:
                msg[f] = original[f]

        msg[39] = response_code
        return msg
