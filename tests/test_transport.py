"""Tests for transport module."""

import pytest
from wol_cli.transport import broadcast_from_network, build_dot1q_frame
from wol_cli.packet import build_magic_packet


class TestBroadcastFromNetwork:
    def test_class_c_network(self):
        assert broadcast_from_network("192.168.1.0/24") == "192.168.1.255"

    def test_class_b_network(self):
        assert broadcast_from_network("172.16.0.0/16") == "172.16.255.255"

    def test_slash_25(self):
        assert broadcast_from_network("192.168.1.0/25") == "192.168.1.127"

    def test_non_zero_host(self):
        # strict=False allows non-network addresses
        assert broadcast_from_network("192.168.1.50/24") == "192.168.1.255"


class TestBuildDot1qFrame:
    def test_frame_structure(self):
        magic = build_magic_packet("AA:BB:CC:DD:EE:FF")
        src_mac = b"\x11\x22\x33\x44\x55\x66"
        dst_mac = b"\xff\xff\xff\xff\xff\xff"

        frame = build_dot1q_frame(
            magic=magic,
            src_mac=src_mac,
            dst_mac=dst_mac,
            vlan_id=100,
            dst_ip="255.255.255.255",
            port=9,
        )

        # Check Ethernet header
        assert frame[:6] == dst_mac
        assert frame[6:12] == src_mac
        # Check 802.1Q tag (0x8100)
        assert frame[12:14] == b"\x81\x00"

    def test_invalid_vlan_id_zero(self):
        magic = build_magic_packet("AA:BB:CC:DD:EE:FF")
        with pytest.raises(ValueError, match="VLAN ID must be 1-4094"):
            build_dot1q_frame(
                magic=magic,
                src_mac=b"\x11\x22\x33\x44\x55\x66",
                dst_mac=b"\xff\xff\xff\xff\xff\xff",
                vlan_id=0,
                dst_ip="255.255.255.255",
                port=9,
            )

    def test_invalid_vlan_id_too_high(self):
        magic = build_magic_packet("AA:BB:CC:DD:EE:FF")
        with pytest.raises(ValueError, match="VLAN ID must be 1-4094"):
            build_dot1q_frame(
                magic=magic,
                src_mac=b"\x11\x22\x33\x44\x55\x66",
                dst_mac=b"\xff\xff\xff\xff\xff\xff",
                vlan_id=4095,
                dst_ip="255.255.255.255",
                port=9,
            )
