"""Wake-on-LAN magic packet sender with VLAN support."""

__version__ = "1.2.0"

from .config import add_alias, get_alias, get_config_path, list_aliases, remove_alias
from .packet import build_magic_packet, parse_mac
from .transport import broadcast_from_network, send_dot1q, send_udp

__all__ = [
    "__version__",
    "add_alias",
    "broadcast_from_network",
    "build_magic_packet",
    "get_alias",
    "get_config_path",
    "list_aliases",
    "parse_mac",
    "remove_alias",
    "send_dot1q",
    "send_udp",
]
