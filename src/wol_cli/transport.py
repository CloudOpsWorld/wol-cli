"""Network transport methods for Wake-on-LAN packets."""

import ipaddress
import socket
import struct
import sys

from .packet import build_magic_packet, parse_mac, checksum

ETH_P_8021Q = 0x8100
ETH_P_IP = 0x0800
IPPROTO_UDP = 17


def send_udp(mac: str, ip: str = "255.255.255.255", port: int = 9) -> None:
    """Send a magic packet via UDP broadcast.

    Args:
        mac: Target MAC address
        ip: Broadcast IP address (default: 255.255.255.255)
        port: UDP port (default: 9)
    """
    packet = build_magic_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.connect((ip, port))
        sock.send(packet)
    print(f"[UDP] Magic packet sent to {mac} via {ip}:{port}")


def broadcast_from_network(cidr: str) -> str:
    """Compute the broadcast address for a given CIDR network."""
    net = ipaddress.IPv4Network(cidr, strict=False)
    return str(net.broadcast_address)


def build_udp_payload(magic: bytes, dst_ip: str, port: int) -> bytes:
    """Wrap magic packet in a minimal IPv4/UDP frame (no IP options)."""
    src_ip_bytes = socket.inet_aton("0.0.0.0")
    dst_ip_bytes = socket.inet_aton(dst_ip)

    udp_len = 8 + len(magic)
    # UDP pseudo-header for checksum
    pseudo = src_ip_bytes + dst_ip_bytes + struct.pack("!BBH", 0, IPPROTO_UDP, udp_len)
    udp_header_no_cs = struct.pack("!HHHH", port, port, udp_len, 0)
    udp_cs = checksum(pseudo + udp_header_no_cs + magic)
    udp_header = struct.pack("!HHHH", port, port, udp_len, udp_cs)

    ip_len = 20 + udp_len
    ip_header_no_cs = struct.pack(
        "!BBHHHBBH4s4s",
        0x45, 0,          # version+IHL, DSCP/ECN
        ip_len,           # total length
        0, 0,             # identification, flags+fragment offset
        64, IPPROTO_UDP,  # TTL, protocol
        0,                # checksum placeholder
        src_ip_bytes,
        dst_ip_bytes,
    )
    ip_cs = checksum(ip_header_no_cs)
    ip_header = struct.pack(
        "!BBHHHBBH4s4s",
        0x45, 0, ip_len, 0, 0, 64, IPPROTO_UDP,
        ip_cs, src_ip_bytes, dst_ip_bytes,
    )

    return ip_header + udp_header + magic


def build_dot1q_frame(
    magic: bytes,
    src_mac: bytes,
    dst_mac: bytes,
    vlan_id: int,
    dst_ip: str,
    port: int,
) -> bytes:
    """Build a complete 802.1Q tagged Ethernet frame."""
    if not (0 < vlan_id < 4095):
        raise ValueError(f"VLAN ID must be 1-4094, got {vlan_id}")

    tci = vlan_id & 0x0FFF  # PCP=0, DEI=0, VID=vlan_id
    payload = build_udp_payload(magic, dst_ip, port)

    return (
        dst_mac
        + src_mac
        + struct.pack("!HHH", ETH_P_8021Q, tci, ETH_P_IP)
        + payload
    )


def get_iface_mac(iface: str) -> bytes:
    """Read the hardware MAC of a local interface (Linux /sys)."""
    try:
        path = f"/sys/class/net/{iface}/address"
        with open(path) as f:
            return parse_mac(f.read().strip())
    except FileNotFoundError:
        raise RuntimeError(f"Interface '{iface}' not found (or not on Linux)")


def send_dot1q(mac: str, vlan_id: int, iface: str, port: int = 9) -> None:
    """Send a magic packet via 802.1Q tagged raw Ethernet frame.

    This mode requires Linux and root privileges.

    Args:
        mac: Target MAC address
        vlan_id: VLAN ID (1-4094)
        iface: Network interface name (e.g., eth0)
        port: UDP port (default: 9)
    """
    if sys.platform != "linux":
        raise RuntimeError("802.1Q raw socket mode is only supported on Linux")

    magic = build_magic_packet(mac)
    dst_mac = bytes.fromhex("ffffffffffff")  # Ethernet broadcast
    src_mac = get_iface_mac(iface)
    dst_ip = "255.255.255.255"

    frame = build_dot1q_frame(magic, src_mac, dst_mac, vlan_id, dst_ip, port)

    # ETH_P_ALL = 0x0003 -> send raw frames
    ETH_P_ALL = 3
    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) as sock:
        sock.bind((iface, 0))
        sock.send(frame)

    print(f"[802.1Q] Magic packet sent to {mac} on VLAN {vlan_id} via {iface}")
