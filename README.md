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

### Options

| Option | Description |
|--------|-------------|
| `--ip IP` | Explicit broadcast/unicast IP (default: 255.255.255.255) |
| `--port PORT` | UDP port (default: 9) |
| `--network CIDR` | Subnet for directed broadcast (e.g., 192.168.10.0/24) |
| `--vlan-id ID` | 802.1Q VLAN ID (1-4094) |
| `--interface IFACE` | Network interface for 802.1Q mode |
| `--version` | Show version |

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

Releases are fully automated via GitHub Actions.

### Automatic Release (on merge to master)

When you merge a PR to `main`/`master`, a new release is automatically created:

1. Version is auto-bumped based on commit messages:
   - `breaking:` or `major:` → **major** (1.0.0 → 2.0.0)
   - `feat:` or `feature:` → **minor** (1.0.0 → 1.1.0)
   - Other commits → **patch** (1.0.0 → 1.0.1)

2. The workflow automatically:
   - Calculates the next semantic version
   - Updates `pyproject.toml` and `src/wol_cli/__init__.py`
   - Creates and pushes the version tag
   - Builds binaries for Linux, Windows, and macOS
   - Creates a GitHub release with all artifacts
   - Publishes to PyPI

### Manual Release

You can also trigger a release manually:

1. Go to **Actions** → **Release** → **Run workflow**
2. Select version bump type: `patch`, `minor`, or `major`
3. Click **Run workflow**

## License

MIT
