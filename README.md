# wol-cli

[![CI](https://github.com/CloudOpsWorld/wol-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/CloudOpsWorld/wol-cli/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/wol-cli.svg)](https://pypi.org/project/wol-cli/)
[![PyPI downloads](https://img.shields.io/pypi/dm/wol-cli.svg)](https://pypi.org/project/wol-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/wol-cli.svg)](https://pypi.org/project/wol-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Wake-on-LAN magic packet sender with VLAN support.

## Features

- **UDP Broadcast**: Standard Wake-on-LAN via UDP broadcast
- **Directed Broadcast**: Auto-compute broadcast address from CIDR notation
- **802.1Q VLAN Support**: Send tagged Ethernet frames directly (Linux only, requires root)
- **Device Aliases**: Save device configurations for quick access

## Installation

### From PyPI

```bash
pip install wol-cli
```

### From GitHub Releases (standalone binary)

Download the appropriate binary for your platform from the [Releases](https://github.com/CloudOpsWorld/wol-cli/releases) page:

- `wol-linux-amd64` - Linux x86_64
- `wol-windows-amd64.exe` - Windows x86_64
- `wol-macos-amd64` - macOS x86_64

### From source

```bash
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

## Usage

### Plain UDP Broadcast (same subnet)

```bash
wol AA:BB:CC:DD:EE:FF
```

### Directed Broadcast

Auto-computes the broadcast address from a CIDR network:

```bash
wol AA:BB:CC:DD:EE:FF --network 192.168.10.0/24
```

### 802.1Q Tagged Frame (Linux only)

Send a VLAN-tagged raw Ethernet frame (requires root):

```bash
sudo wol AA:BB:CC:DD:EE:FF --vlan-id 10 --interface eth0
```

### Using Aliases

Wake a device using its alias name instead of MAC address:

```bash
wol my-server
```

### Options

| Option | Description |
|--------|-------------|
| `--ip IP` | Explicit broadcast/unicast IP (default: 255.255.255.255) |
| `--port PORT` | UDP port (default: 9) |
| `--network CIDR` | Subnet for directed broadcast (e.g., 192.168.10.0/24) |
| `--vlan-id ID` | 802.1Q VLAN ID (1-4094) |
| `--interface IFACE` | Network interface for 802.1Q mode |
| `--version` | Show version |

## Alias Management

Aliases let you save device configurations for quick access. The configuration is stored in an OS-specific location:

| OS | Config Path |
|----|-------------|
| Linux | `~/.config/wol-cli/config.toml` (or `$XDG_CONFIG_HOME/wol-cli/config.toml`) |
| macOS | `~/Library/Application Support/wol-cli/config.toml` |
| Windows | `%APPDATA%\wol-cli\config.toml` |

### Add an Alias

```bash
# Simple alias with just MAC address
wol alias add my-server AA:BB:CC:DD:EE:FF

# Alias with network settings
wol alias add my-server AA:BB:CC:DD:EE:FF --network 192.168.10.0/24

# Alias with VLAN settings
wol alias add my-server AA:BB:CC:DD:EE:FF --vlan-id 100 --interface eth0

# Alias with all options
wol alias add my-server AA:BB:CC:DD:EE:FF --ip 192.168.1.255 --port 7
```

### List Aliases

```bash
wol alias list
```

### Show Alias Details

```bash
wol alias show my-server
```

### Remove an Alias

```bash
wol alias remove my-server
```

### Show Config File Path

```bash
wol alias path
```

## Library Usage

```python
from wol_cli import send_udp, send_dot1q, build_magic_packet

# Send via UDP broadcast
send_udp("AA:BB:CC:DD:EE:FF")

# Send via directed broadcast
send_udp("AA:BB:CC:DD:EE:FF", ip="192.168.10.255")

# Build a magic packet manually
packet = build_magic_packet("AA:BB:CC:DD:EE:FF")
```

### Alias Management (Programmatic)

```python
from wol_cli import add_alias, get_alias, list_aliases, remove_alias, get_config_path

# Add an alias
add_alias("my-server", "AA:BB:CC:DD:EE:FF", network="192.168.10.0/24")

# Get alias configuration
config = get_alias("my-server")
# {'mac': 'AA:BB:CC:DD:EE:FF', 'network': '192.168.10.0/24'}

# List all aliases
aliases = list_aliases()

# Remove an alias
remove_alias("my-server")

# Get config file path
path = get_config_path()
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest -v
```

Run linter:

```bash
ruff check src/ tests/
```

Run type checker:

```bash
mypy src/
```

## Releasing

Releases are automated via GitHub Actions.

### How to Release

1. Update version in **both** files (must match):
   - `pyproject.toml`: `version = "X.Y.Z"`
   - `src/wol_cli/__init__.py`: `__version__ = "X.Y.Z"`

2. Create a PR and merge to `main`/`master`

3. The workflow automatically:
   - Validates versions match
   - Creates tag `vX.Y.Z` (if it doesn't exist)
   - Builds binaries for Linux, Windows, and macOS
   - Creates GitHub release with all artifacts
   - Publishes to PyPI

**Note:** If the tag already exists, no release is created (idempotent).

## License

MIT
