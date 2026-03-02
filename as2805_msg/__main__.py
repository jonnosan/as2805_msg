"""CLI entry point: python -m as2805_msg

Usage:
    python -m as2805_msg decode <hex_string>
    python -m as2805_msg dump <hex_string>
    echo <hex_string> | python -m as2805_msg decode
    python -m as2805_msg decode --framed <hex_string>
"""

from __future__ import annotations

import sys

from .dump import dump, dump_raw
from .message import AS2805Message
from .stream import AS2805Stream


def _read_hex_input(args: list[str]) -> str:
    """Get hex string from args or stdin."""
    # Filter out flags
    hex_args = [a for a in args if not a.startswith("--")]
    if hex_args:
        return "".join(hex_args)
    # Read from stdin
    return sys.stdin.read().strip()


def _hex_to_bytes(hex_str: str) -> bytes:
    """Convert a hex string (with optional spaces/newlines) to bytes."""
    cleaned = hex_str.replace(" ", "").replace("\n", "").replace("\r", "")
    return bytes.fromhex(cleaned)


def cmd_decode(args: list[str]) -> None:
    """Decode and pretty-print a message."""
    framed = "--framed" in args
    hex_str = _read_hex_input(args)
    data = _hex_to_bytes(hex_str)

    if framed:
        messages = AS2805Stream.read_all(data)
    else:
        messages = [AS2805Message.unpack(data)]

    for i, msg in enumerate(messages):
        if i > 0:
            print("---")
        print(str(msg))


def cmd_dump(args: list[str]) -> None:
    """Decode with detailed hex dump view."""
    framed = "--framed" in args
    hex_str = _read_hex_input(args)
    data = _hex_to_bytes(hex_str)

    # Always show raw hex dump
    print("=== Raw Hex Dump ===")
    print(dump_raw(data))
    print()

    if framed:
        messages = AS2805Stream.read_all(data)
    else:
        messages = [AS2805Message.unpack(data)]

    for i, msg in enumerate(messages):
        if i > 0:
            print()
        print(f"=== Message {i + 1} ===")
        print(dump(msg))


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "decode":
        cmd_decode(args)
    elif command == "dump":
        cmd_dump(args)
    else:
        print(f"Unknown command: {command}")
        print(__doc__.strip())
        sys.exit(1)


if __name__ == "__main__":
    main()
