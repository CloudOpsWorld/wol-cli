"""Tests for CLI module."""

import pytest
from wol_cli.cli import create_parser


class TestCreateParser:
    def test_mac_argument_required(self):
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_mac_argument_parsed(self):
        parser = create_parser()
        args = parser.parse_args(["AA:BB:CC:DD:EE:FF"])
        assert args.mac == "AA:BB:CC:DD:EE:FF"

    def test_default_values(self):
        parser = create_parser()
        args = parser.parse_args(["AA:BB:CC:DD:EE:FF"])
        assert args.ip == "255.255.255.255"
        assert args.port == 9
        assert args.network is None
        assert args.vlan_id is None
        assert args.interface is None

    def test_custom_port(self):
        parser = create_parser()
        args = parser.parse_args(["AA:BB:CC:DD:EE:FF", "--port", "7"])
        assert args.port == 7

    def test_network_option(self):
        parser = create_parser()
        args = parser.parse_args(["AA:BB:CC:DD:EE:FF", "--network", "192.168.10.0/24"])
        assert args.network == "192.168.10.0/24"

    def test_vlan_options(self):
        parser = create_parser()
        args = parser.parse_args([
            "AA:BB:CC:DD:EE:FF",
            "--vlan-id", "100",
            "--interface", "eth0"
        ])
        assert args.vlan_id == 100
        assert args.interface == "eth0"
