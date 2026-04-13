"""Tests for configuration module."""

import os
from pathlib import Path
from unittest import mock

import pytest

from wol_cli.config import (
    add_alias,
    get_alias,
    get_config_dir,
    list_aliases,
    load_config,
    remove_alias,
    save_config,
)


class TestGetConfigDir:
    def test_linux(self) -> None:
        with mock.patch("sys.platform", "linux"):
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}, clear=False):
                result = get_config_dir()
                assert result == Path("/custom/config/wol-cli")

    def test_linux_default(self) -> None:
        with mock.patch("sys.platform", "linux"):
            with mock.patch.dict(os.environ, {}, clear=True):
                with mock.patch("pathlib.Path.home", return_value=Path("/home/user")):
                    result = get_config_dir()
                    assert result == Path("/home/user/.config/wol-cli")

    def test_macos(self) -> None:
        with mock.patch("sys.platform", "darwin"):
            with mock.patch("pathlib.Path.home", return_value=Path("/Users/user")):
                result = get_config_dir()
                assert result == Path("/Users/user/Library/Application Support/wol-cli")

    def test_windows(self) -> None:
        with mock.patch("sys.platform", "win32"):
            with mock.patch.dict(os.environ, {"APPDATA": "C:\\Users\\user\\AppData\\Roaming"}):
                result = get_config_dir()
                assert result == Path("C:\\Users\\user\\AppData\\Roaming/wol-cli")


class TestConfigOperations:
    @pytest.fixture
    def temp_config(self, tmp_path: Path) -> Path:
        """Create a temporary config directory."""
        config_dir = tmp_path / "wol-cli"
        config_dir.mkdir()
        return config_dir / "config.toml"

    @pytest.fixture
    def mock_config_path(self, temp_config: Path) -> mock.MagicMock:
        """Mock get_config_path to use temp directory."""
        with mock.patch("wol_cli.config.get_config_path", return_value=temp_config) as m:
            yield m

    def test_load_empty_config(self, mock_config_path: mock.MagicMock) -> None:
        config = load_config()
        assert config == {"aliases": {}}

    def test_save_and_load_config(
        self, mock_config_path: mock.MagicMock, temp_config: Path
    ) -> None:
        config = {
            "aliases": {
                "test-server": {"mac": "AA:BB:CC:DD:EE:FF", "port": 9}
            }
        }
        save_config(config)
        loaded = load_config()
        assert loaded["aliases"]["test-server"]["mac"] == "AA:BB:CC:DD:EE:FF"

    def test_add_alias(self, mock_config_path: mock.MagicMock) -> None:
        add_alias("my-pc", "11:22:33:44:55:66")
        alias = get_alias("my-pc")
        assert alias is not None
        assert alias["mac"] == "11:22:33:44:55:66"

    def test_add_alias_with_options(self, mock_config_path: mock.MagicMock) -> None:
        add_alias(
            "my-server",
            "AA:BB:CC:DD:EE:FF",
            ip="192.168.1.255",
            port=7,
            network="192.168.1.0/24",
        )
        alias = get_alias("my-server")
        assert alias is not None
        assert alias["mac"] == "AA:BB:CC:DD:EE:FF"
        assert alias["ip"] == "192.168.1.255"
        assert alias["port"] == 7
        assert alias["network"] == "192.168.1.0/24"

    def test_remove_alias(self, mock_config_path: mock.MagicMock) -> None:
        add_alias("to-remove", "AA:BB:CC:DD:EE:FF")
        assert get_alias("to-remove") is not None

        result = remove_alias("to-remove")
        assert result is True
        assert get_alias("to-remove") is None

    def test_remove_nonexistent_alias(self, mock_config_path: mock.MagicMock) -> None:
        result = remove_alias("nonexistent")
        assert result is False

    def test_list_aliases(self, mock_config_path: mock.MagicMock) -> None:
        add_alias("server1", "11:11:11:11:11:11")
        add_alias("server2", "22:22:22:22:22:22")

        aliases = list_aliases()
        assert "server1" in aliases
        assert "server2" in aliases
        assert aliases["server1"]["mac"] == "11:11:11:11:11:11"

    def test_update_existing_alias(self, mock_config_path: mock.MagicMock) -> None:
        add_alias("my-pc", "11:11:11:11:11:11")
        add_alias("my-pc", "22:22:22:22:22:22", ip="10.0.0.1")

        alias = get_alias("my-pc")
        assert alias is not None
        assert alias["mac"] == "22:22:22:22:22:22"
        assert alias["ip"] == "10.0.0.1"
