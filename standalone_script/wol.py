#!/usr/bin/env python3
"""
Wake-on-LAN magic packet sender with VLAN support.

Modes:
  UDP broadcast (default)     — standard LAN/subnet delivery
  --network CIDR              — auto-computes directed broadcast for a VLAN subnet
  --vlan-id + --interface     — 802.1Q tagged raw Ethernet frame (Linux, requires root)

Usage:
  python wol.py AA:BB:CC:DD:EE:FF
  python wol.py AA:BB:CC:DD:EE:FF --network 192.168.10.0/24
  python wol.py AA:BB:CC:DD:EE:FF --vlan-id 10 --interface eth0
"""

import argparse
import ipaddress
import re
import socket
import struct
import sys


# ──────────────────────────────────────────────
# Magic packet
# ──────────────────────────────────────────────

def parse_mac(mac: str) -> bytes:
    clean = re.sub(r"[:\-.]", "", mac).upper()
    if len(clean) != 12 or not all(c in "0123456789ABCDEF" for c in clean):
        raise ValueError(f"Invalid MAC address: {mac!r}")
    return bytes.fromhex(clean)


def build_magic_packet(mac: str) -> bytes:
    mac_bytes = parse_mac(mac)
    return b"\xff" * 6 + mac_bytes * 16


# ──────────────────────────────────────────────
# Mode 1 & 2: UDP (plain broadcast or directed)
# ──────────────────────────────────────────────

def send_udp(mac: str, ip: str, port: int) -> None:
    packet = build_magic_packet(mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.connect((ip, port))
        sock.send(packet)
    print(f"[UDP] Magic packet sent to {mac} via {ip}:{port}")


def broadcast_from_network(cidr: str) -> str:
    net = ipaddress.IPv4Network(cidr, strict=False)
    return str(net.broadcast_address)


# ──────────────────────────────────────────────
# Mode 3: 802.1Q tagged raw Ethernet frame
# ──────────────────────────────────────────────
#
# Frame layout (bytes):
#   [ DST MAC 6 ][ SRC MAC 6 ][ 0x8100 2 ][ TCI 2 ][ 0x0800 2 ]
#   [ IPv4 header 20 ][ UDP header 8 ][ magic packet 102 ]
#
# Requires: Linux, CAP_NET_RAW (root), known egress interface.

ETH_P_8021Q = 0x8100
ETH_P_IP    = 0x0800
IPPROTO_UDP = 17


def checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"
    s = sum(struct.unpack(f"!{len(data)//2}H", data))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF


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
        raise ValueError(f"VLAN ID must be 1–4094, got {vlan_id}")

    tci = vlan_id & 0x0FFF          # PCP=0, DEI=0, VID=vlan_id
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


def send_dot1q(mac: str, vlan_id: int, iface: str, port: int) -> None:
    if sys.platform != "linux":
        raise RuntimeError("802.1Q raw socket mode is only supported on Linux")

    magic      = build_magic_packet(mac)
    dst_mac    = bytes.fromhex("ffffffffffff")   # Ethernet broadcast
    src_mac    = get_iface_mac(iface)
    dst_ip     = "255.255.255.255"

    frame = build_dot1q_frame(magic, src_mac, dst_mac, vlan_id, dst_ip, port)

    # ETH_P_ALL = 0x0003 → send raw frames
    ETH_P_ALL = 3
    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) as sock:
        sock.bind((iface, 0))
        sock.send(frame)

    print(f"[802.1Q] Magic packet sent to {mac} on VLAN {vlan_id} via {iface}")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Send a Wake-on-LAN magic packet, with optional VLAN support.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plain UDP broadcast (same subnet)
  python wol.py AA:BB:CC:DD:EE:FF

  # Directed broadcast — auto-computes 192.168.10.255
  python wol.py AA:BB:CC:DD:EE:FF --network 192.168.10.0/24

  # 802.1Q tagged raw frame (Linux, must be root)
  sudo python wol.py AA:BB:CC:DD:EE:FF --vlan-id 10 --interface eth0
        """,
    )
    parser.add_argument("mac", help="Target MAC address (AA:BB:CC:DD:EE:FF)")
    parser.add_argument("--ip",        default="255.255.255.255",
                        help="Explicit broadcast/unicast IP (UDP modes, default: 255.255.255.255)")
    parser.add_argument("--port",      type=int, default=9,
                        help="UDP port (default: 9)")
    parser.add_argument("--network",   metavar="CIDR",
                        help="VLAN subnet in CIDR notation — derives directed broadcast IP (e.g. 192.168.10.0/24)")
    parser.add_argument("--vlan-id",   type=int, metavar="ID",
                        help="802.1Q VLAN ID 1–4094 — sends a tagged raw Ethernet frame (requires --interface and root)")
    parser.add_argument("--interface", metavar="IFACE",
                        help="Egress network interface for raw 802.1Q mode (e.g. eth0)")

    args = parser.parse_args()

    try:
        if args.vlan_id is not None:
            # ── Mode 3: raw 802.1Q ──────────────────────────
            if not args.interface:
                parser.error("--vlan-id requires --interface")
            send_dot1q(args.mac, args.vlan_id, args.interface, args.port)

        elif args.network:
            # ── Mode 2: directed broadcast via CIDR ─────────
            bcast = broadcast_from_network(args.network)
            print(f"[INFO] Directed broadcast for {args.network} → {bcast}")
            send_udp(args.mac, bcast, args.port)

        else:
            # ── Mode 1: plain UDP broadcast ──────────────────
            send_udp(args.mac, args.ip, args.port)

    except PermissionError:
        sys.exit("[ERROR] Raw socket requires root privileges. Re-run with sudo.")
    except Exception as e:
        sys.exit(f"[ERROR] {e}")


if __name__ == "__main__":
    main()