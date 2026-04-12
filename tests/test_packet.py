"""Tests for magic packet construction."""

import pytest

from wol_cli.packet import build_magic_packet, checksum, parse_mac


class TestParseMac:
    def test_colon_separated(self):
        result = parse_mac("AA:BB:CC:DD:EE:FF")
        assert result == b"\xaa\xbb\xcc\xdd\xee\xff"

    def test_dash_separated(self):
        result = parse_mac("AA-BB-CC-DD-EE-FF")
        assert result == b"\xaa\xbb\xcc\xdd\xee\xff"

    def test_dot_separated(self):
        result = parse_mac("AABB.CCDD.EEFF")
        assert result == b"\xaa\xbb\xcc\xdd\xee\xff"

    def test_lowercase(self):
        result = parse_mac("aa:bb:cc:dd:ee:ff")
        assert result == b"\xaa\xbb\xcc\xdd\xee\xff"

    def test_no_separator(self):
        result = parse_mac("AABBCCDDEEFF")
        assert result == b"\xaa\xbb\xcc\xdd\xee\xff"

    def test_invalid_length(self):
        with pytest.raises(ValueError, match="Invalid MAC address"):
            parse_mac("AA:BB:CC:DD:EE")

    def test_invalid_characters(self):
        with pytest.raises(ValueError, match="Invalid MAC address"):
            parse_mac("GG:HH:II:JJ:KK:LL")


class TestBuildMagicPacket:
    def test_packet_length(self):
        packet = build_magic_packet("AA:BB:CC:DD:EE:FF")
        # 6 bytes of 0xFF + 16 * 6 bytes of MAC = 102 bytes
        assert len(packet) == 102

    def test_packet_header(self):
        packet = build_magic_packet("AA:BB:CC:DD:EE:FF")
        assert packet[:6] == b"\xff" * 6

    def test_packet_payload(self):
        packet = build_magic_packet("AA:BB:CC:DD:EE:FF")
        mac_bytes = b"\xaa\xbb\xcc\xdd\xee\xff"
        assert packet[6:] == mac_bytes * 16


class TestChecksum:
    def test_even_length_data(self):
        # Simple test with known values
        data = b"\x00\x01\x00\x02"
        result = checksum(data)
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF

    def test_odd_length_data(self):
        # Should handle odd-length data by padding
        data = b"\x00\x01\x02"
        result = checksum(data)
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF

    def test_empty_data(self):
        result = checksum(b"")
        assert result == 0xFFFF
