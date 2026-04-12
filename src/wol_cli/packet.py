"""Magic packet construction for Wake-on-LAN."""

import re
import struct


def parse_mac(mac: str) -> bytes:
    """Parse a MAC address string into bytes.

    Accepts formats: AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF, AABB.CCDD.EEFF
    """
    clean = re.sub(r"[:\-.]", "", mac).upper()
    if len(clean) != 12 or not all(c in "0123456789ABCDEF" for c in clean):
        raise ValueError(f"Invalid MAC address: {mac!r}")
    return bytes.fromhex(clean)


def build_magic_packet(mac: str) -> bytes:
    """Build a Wake-on-LAN magic packet for the given MAC address.

    The magic packet consists of 6 bytes of 0xFF followed by the target
    MAC address repeated 16 times.
    """
    mac_bytes = parse_mac(mac)
    return b"\xff" * 6 + mac_bytes * 16


def checksum(data: bytes) -> int:
    """Calculate IP/UDP checksum."""
    if len(data) % 2:
        data += b"\x00"
    s: int = sum(struct.unpack(f"!{len(data)//2}H", data))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF
