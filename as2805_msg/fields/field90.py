"""Field 90 — Original Data Elements, composite sub-field parser.

Fixed 42-digit numeric field split into 5 sub-fields:
  - Original MTI (4 digits)
  - Original STAN (6 digits)
  - Original Transmission Date/Time (10 digits)
  - Acquiring Institution ID (11 digits, right-justified zero-padded)
  - Forwarding Institution ID (11 digits, right-justified zero-padded)
"""

from __future__ import annotations

from .. import codec


class Field90:
    """Parse and build Field 90 Original Data Elements."""

    @staticmethod
    def unpack(value: str) -> dict[str, str]:
        """Parse the 42-digit string into sub-fields.

        Returns dict with keys: mti, stan, transmission_dt, acq_inst, fwd_inst.
        """
        if len(value) != 42:
            raise ValueError(f"Field 90 must be 42 digits, got {len(value)}")
        return {
            "mti": value[0:4],
            "stan": value[4:10],
            "transmission_dt": value[10:20],
            "acq_inst": value[20:31],
            "fwd_inst": value[31:42],
        }

    @staticmethod
    def pack(elements: dict[str, str]) -> str:
        """Build a 42-digit string from sub-field dict."""
        mti = elements["mti"].zfill(4)
        stan = elements["stan"].zfill(6)
        transmission_dt = elements["transmission_dt"].zfill(10)
        acq_inst = elements["acq_inst"].zfill(11)
        fwd_inst = elements["fwd_inst"].zfill(11)
        result = mti + stan + transmission_dt + acq_inst + fwd_inst
        if len(result) != 42:
            raise ValueError(f"Field 90 pack produced {len(result)} digits, expected 42")
        return result
