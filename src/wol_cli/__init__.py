"""Wake-on-LAN magic packet sender with VLAN support."""

__version__ = "0.1.0"

from .packet import build_magic_packet, parse_mac
from .transport import send_udp, send_dot1q, broadcast_from_network

__all__ = [
    "__version__",
    "build_magic_packet",
    "parse_mac",
    "send_udp",
    "send_dot1q",
    "broadcast_from_network",
]
