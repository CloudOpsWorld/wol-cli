"""Command-line interface for Wake-on-LAN tool."""

import argparse
import sys

from . import __version__
from .transport import send_udp, send_dot1q, broadcast_from_network


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="wol",
        description="Send a Wake-on-LAN magic packet, with optional VLAN support.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plain UDP broadcast (same subnet)
  wol AA:BB:CC:DD:EE:FF

  # Directed broadcast - auto-computes 192.168.10.255
  wol AA:BB:CC:DD:EE:FF --network 192.168.10.0/24

  # 802.1Q tagged raw frame (Linux, must be root)
  sudo wol AA:BB:CC:DD:EE:FF --vlan-id 10 --interface eth0
        """,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("mac", help="Target MAC address (AA:BB:CC:DD:EE:FF)")
    parser.add_argument(
        "--ip",
        default="255.255.255.255",
        help="Explicit broadcast/unicast IP (UDP modes, default: 255.255.255.255)",
    )
    parser.add_argument(
        "--port", type=int, default=9, help="UDP port (default: 9)"
    )
    parser.add_argument(
        "--network",
        metavar="CIDR",
        help="VLAN subnet in CIDR notation - derives directed broadcast IP (e.g. 192.168.10.0/24)",
    )
    parser.add_argument(
        "--vlan-id",
        type=int,
        metavar="ID",
        help="802.1Q VLAN ID 1-4094 - sends a tagged raw Ethernet frame (requires --interface and root)",
    )
    parser.add_argument(
        "--interface",
        metavar="IFACE",
        help="Egress network interface for raw 802.1Q mode (e.g. eth0)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        if args.vlan_id is not None:
            # Mode 3: raw 802.1Q
            if not args.interface:
                parser.error("--vlan-id requires --interface")
            send_dot1q(args.mac, args.vlan_id, args.interface, args.port)

        elif args.network:
            # Mode 2: directed broadcast via CIDR
            bcast = broadcast_from_network(args.network)
            print(f"[INFO] Directed broadcast for {args.network} -> {bcast}")
            send_udp(args.mac, bcast, args.port)

        else:
            # Mode 1: plain UDP broadcast
            send_udp(args.mac, args.ip, args.port)

        return 0

    except PermissionError:
        print("[ERROR] Raw socket requires root privileges. Re-run with sudo.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
