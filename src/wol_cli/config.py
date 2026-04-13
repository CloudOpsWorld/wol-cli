"""Configuration management for wol-cli."""

import os
import sys
from pathlib import Path
from typing import Any, cast

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]


def get_config_dir() -> Path:
    """Get the configuration directory based on OS."""
    if sys.platform == "win32":
        # Windows: %APPDATA%\wol-cli
        base = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
        return Path(base) / "wol-cli"
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/wol-cli
        return Path.home() / "Library" / "Application Support" / "wol-cli"
    else:
        # Linux/Unix: ~/.config/wol-cli
        xdg_config = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        return Path(xdg_config) / "wol-cli"


def get_config_path() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.toml"


def load_config() -> dict[str, Any]:
    """Load configuration from file."""
    config_path = get_config_path()
    if not config_path.exists():
        return {"aliases": {}}

    with open(config_path, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)
        return data


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Format TOML manually (simple implementation)
    lines = []

    if "aliases" in config and config["aliases"]:
        lines.append("[aliases]")
        for name, settings in sorted(config["aliases"].items()):
            parts = []
            for key, value in settings.items():
                if isinstance(value, str):
                    parts.append(f'{key} = "{value}"')
                elif isinstance(value, int):
                    parts.append(f"{key} = {value}")
                elif isinstance(value, bool):
                    parts.append(f"{key} = {'true' if value else 'false'}")
            lines.append(f"{name} = {{ {', '.join(parts)} }}")

    with open(config_path, "w") as f:
        f.write("\n".join(lines) + "\n" if lines else "")


def get_alias(name: str) -> dict[str, Any] | None:
    """Get alias configuration by name."""
    config = load_config()
    aliases = cast(dict[str, dict[str, Any]], config.get("aliases", {}))
    return aliases.get(name)


def add_alias(
    name: str,
    mac: str,
    ip: str | None = None,
    port: int | None = None,
    network: str | None = None,
    vlan_id: int | None = None,
    interface: str | None = None,
) -> None:
    """Add or update an alias."""
    config = load_config()
    if "aliases" not in config:
        config["aliases"] = {}

    alias_config: dict[str, Any] = {"mac": mac}
    if ip:
        alias_config["ip"] = ip
    if port:
        alias_config["port"] = port
    if network:
        alias_config["network"] = network
    if vlan_id:
        alias_config["vlan_id"] = vlan_id
    if interface:
        alias_config["interface"] = interface

    config["aliases"][name] = alias_config
    save_config(config)


def remove_alias(name: str) -> bool:
    """Remove an alias. Returns True if alias existed."""
    config = load_config()
    if "aliases" in config and name in config["aliases"]:
        del config["aliases"][name]
        save_config(config)
        return True
    return False


def list_aliases() -> dict[str, dict[str, Any]]:
    """List all aliases."""
    config = load_config()
    return cast(dict[str, dict[str, Any]], config.get("aliases", {}))
