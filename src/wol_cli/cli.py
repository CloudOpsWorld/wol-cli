"""Command-line interface for Wake-on-LAN tool."""

import argparse
import sys

from . import __version__
from .config import add_alias, get_alias, get_config_path, list_aliases, remove_alias
from .transport import broadcast_from_network, send_dot1q, send_udp


def create_wake_parser() -> argparse.ArgumentParser:
    """Create the main wake argument parser."""
    parser = argparse.ArgumentParser(
        prog="wol",
        description="Send a Wake-on-LAN magic packet, with optional VLAN support.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Wake using MAC address
  wol AA:BB:CC:DD:EE:FF

  # Wake using alias
  wol my-server

  # Directed broadcast
  wol AA:BB:CC:DD:EE:FF --network 192.168.10.0/24

  # 802.1Q tagged frame (Linux, root required)
  sudo wol AA:BB:CC:DD:EE:FF --vlan-id 10 --interface eth0

  # Manage aliases
  wol alias add my-server AA:BB:CC:DD:EE:FF
  wol alias add my-server AA:BB:CC:DD:EE:FF --network 192.168.10.0/24
  wol alias list
  wol alias remove my-server
        """,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "target",
        help="MAC address (AA:BB:CC:DD:EE:FF) or alias name",
    )
    parser.add_argument(
        "--ip",
        default=None,
        help="Explicit broadcast/unicast IP (default: 255.255.255.255)",
    )
    parser.add_argument(
        "--port", type=int, default=None, help="UDP port (default: 9)"
    )
    parser.add_argument(
        "--network",
        metavar="CIDR",
        help="Network CIDR for directed broadcast (e.g. 192.168.10.0/24)",
    )
    parser.add_argument(
        "--vlan-id",
        type=int,
        metavar="ID",
        help="802.1Q VLAN ID 1-4094 (requires --interface and root)",
    )
    parser.add_argument(
        "--interface",
        metavar="IFACE",
        help="Network interface for raw 802.1Q mode (e.g. eth0)",
    )
    return parser


def create_alias_parser() -> argparse.ArgumentParser:
    """Create the alias management argument parser."""
    parser = argparse.ArgumentParser(
        prog="wol alias",
        description="Manage device aliases for Wake-on-LAN.",
    )
    subparsers = parser.add_subparsers(dest="alias_command", required=True)

    # alias add
    add_parser = subparsers.add_parser("add", help="Add or update an alias")
    add_parser.add_argument("name", help="Alias name")
    add_parser.add_argument("mac", help="MAC address (AA:BB:CC:DD:EE:FF)")
    add_parser.add_argument("--ip", help="Broadcast IP address")
    add_parser.add_argument("--port", type=int, help="UDP port")
    add_parser.add_argument("--network", metavar="CIDR", help="Network CIDR for directed broadcast")
    add_parser.add_argument("--vlan-id", type=int, metavar="ID", help="VLAN ID (1-4094)")
    add_parser.add_argument("--interface", metavar="IFACE", help="Network interface for 802.1Q")

    # alias remove
    remove_parser = subparsers.add_parser("remove", help="Remove an alias")
    remove_parser.add_argument("name", help="Alias name to remove")

    # alias list
    subparsers.add_parser("list", help="List all aliases")

    # alias show
    show_parser = subparsers.add_parser("show", help="Show alias details")
    show_parser.add_argument("name", help="Alias name")

    # alias path
    subparsers.add_parser("path", help="Show config file path")

    return parser


def handle_alias_command(argv: list[str]) -> int:
    """Handle alias subcommands."""
    parser = create_alias_parser()
    args = parser.parse_args(argv)

    if args.alias_command == "add":
        add_alias(
            args.name,
            args.mac,
            ip=args.ip,
            port=args.port,
            network=args.network,
            vlan_id=getattr(args, "vlan_id", None),
            interface=args.interface,
        )
        print(f"Alias '{args.name}' added successfully.")
        return 0

    elif args.alias_command == "remove":
        if remove_alias(args.name):
            print(f"Alias '{args.name}' removed.")
            return 0
        else:
            print(f"Alias '{args.name}' not found.", file=sys.stderr)
            return 1

    elif args.alias_command == "list":
        aliases = list_aliases()
        if not aliases:
            print("No aliases configured.")
            print(f"Config file: {get_config_path()}")
            return 0

        print("Configured aliases:")
        print("-" * 60)
        for name, settings in sorted(aliases.items()):
            mac = settings.get("mac", "N/A")
            extras = []
            if "ip" in settings:
                extras.append(f"ip={settings['ip']}")
            if "port" in settings:
                extras.append(f"port={settings['port']}")
            if "network" in settings:
                extras.append(f"network={settings['network']}")
            if "vlan_id" in settings:
                extras.append(f"vlan={settings['vlan_id']}")
            if "interface" in settings:
                extras.append(f"iface={settings['interface']}")

            extra_str = f" ({', '.join(extras)})" if extras else ""
            print(f"  {name}: {mac}{extra_str}")
        print("-" * 60)
        print(f"Config file: {get_config_path()}")
        return 0

    elif args.alias_command == "show":
        alias_config = get_alias(args.name)
        if not alias_config:
            print(f"Alias '{args.name}' not found.", file=sys.stderr)
            return 1

        print(f"Alias: {args.name}")
        for key, value in alias_config.items():
            print(f"  {key}: {value}")
        return 0

    elif args.alias_command == "path":
        print(get_config_path())
        return 0

    return 1


def resolve_target(target: str) -> tuple[str, dict[str, str | int | None]]:
    """Resolve target to MAC address and optional settings.

    Returns (mac_address, settings_dict).
    If target is a MAC address, returns it directly.
    If target is an alias, returns the alias configuration.
    """
    empty_settings: dict[str, str | int | None] = {}
    # Check if it looks like a MAC address (contains : or -)
    if ":" in target or "-" in target or len(target) == 12:
        return target, empty_settings

    # Try to resolve as alias
    alias_config = get_alias(target)
    if alias_config:
        mac = str(alias_config.pop("mac"))
        settings: dict[str, str | int | None] = {}
        for key, value in alias_config.items():
            if isinstance(value, (str, int)) or value is None:
                settings[key] = value
        return mac, settings

    # Not a MAC and not an alias - assume it's a MAC without separators
    return target, empty_settings


# Keep for backwards compatibility with tests
def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser (for backwards compatibility)."""
    return create_wake_parser()


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    if argv is None:
        argv = sys.argv[1:]

    # Check if first argument is 'alias' subcommand
    if argv and argv[0] == "alias":
        return handle_alias_command(argv[1:])

    # Handle main wake command
    parser = create_wake_parser()

    # If no arguments, show help
    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    try:
        # Resolve target (MAC or alias)
        mac, alias_settings = resolve_target(args.target)

        # Merge alias settings with CLI arguments (CLI takes precedence)
        ip_val = args.ip or alias_settings.get("ip") or "255.255.255.255"
        port_val = args.port or alias_settings.get("port") or 9
        network_val = args.network or alias_settings.get("network")
        vlan_id_val = args.vlan_id or alias_settings.get("vlan_id")
        interface_val = args.interface or alias_settings.get("interface")

        # Ensure proper types
        ip_str = str(ip_val)
        port_int = int(port_val)

        # Check if using alias and show info
        if alias_settings:
            print(f"[INFO] Using alias '{args.target}' -> {mac}")

        if vlan_id_val is not None:
            # Mode 3: raw 802.1Q
            if not interface_val:
                parser.error("--vlan-id requires --interface")
            send_dot1q(mac, int(vlan_id_val), str(interface_val), port_int)

        elif network_val:
            # Mode 2: directed broadcast via CIDR
            network_str = str(network_val)
            bcast = broadcast_from_network(network_str)
            print(f"[INFO] Directed broadcast for {network_str} -> {bcast}")
            send_udp(mac, bcast, port_int)

        else:
            # Mode 1: plain UDP broadcast
            send_udp(mac, ip_str, port_int)

        return 0

    except PermissionError:
        print("[ERROR] Raw socket requires root privileges. Re-run with sudo.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
