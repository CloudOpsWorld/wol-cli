"""Tests for CLI module."""

import pytest

from wol_cli.cli import create_parser


class TestCreateParser:
    def test_mac_argument_required(self) -> None:
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_mac_argument_parsed(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["AA:BB:CC:DD:EE:FF"])
        assert args.target == "AA:BB:CC:DD:EE:FF"

    def test_default_values(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["AA:BB:CC:DD:EE:FF"])
        assert args.ip is None
        assert args.port is None
        assert args.network is None
        assert args.vlan_id is None
        assert args.interface is None

    def test_custom_port(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["AA:BB:CC:DD:EE:FF", "--port", "7"])
        assert args.port == 7

    def test_network_option(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["AA:BB:CC:DD:EE:FF", "--network", "192.168.10.0/24"])
        assert args.network == "192.168.10.0/24"

    def test_vlan_options(self) -> None:
        parser = create_parser()
        args = parser.parse_args([
            "AA:BB:CC:DD:EE:FF",
            "--vlan-id", "100",
            "--interface", "eth0"
        ])
        assert args.vlan_id == 100
        assert args.interface == "eth0"

    def test_alias_name_as_target(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["my-server"])
        assert args.target == "my-server"

    def test_ip_option(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["AA:BB:CC:DD:EE:FF", "--ip", "192.168.1.255"])
        assert args.ip == "192.168.1.255"
