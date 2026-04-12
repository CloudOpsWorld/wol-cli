"""Wake-on-LAN magic packet sender with VLAN support."""

__version__ = "1.0.0"

from .packet import build_magic_packet, parse_mac
from .transport import broadcast_from_network, send_dot1q, send_udp

__all__ = [
    "__version__",
    "build_magic_packet",
    "parse_mac",
    "send_udp",
    "send_dot1q",
    "broadcast_from_network",
]
