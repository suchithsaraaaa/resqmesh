import time
import json
import socket
import pytest
from pathlib import Path

from backend.app.services.node_manager import NodeManager
from backend.app.network.discovery import DiscoveryEngine, get_local_ip


@pytest.fixture
def mock_node_manager(tmp_path):
    """Fixture providing isolated NodeManager with temporary directory."""
    nm = NodeManager(data_dir=tmp_path)
    nm.setup_node("Test-Node-Alpha", "commander", 8000)
    return nm


def test_local_ip_resolution():
    """Verify local IPv4 address resolution returns a non-empty string."""
    ip = get_local_ip()
    assert isinstance(ip, str)
    assert len(ip.split(".")) == 4


def test_peer_registration_via_discovery(mock_node_manager):
    """Verify incoming discovery beacon registers remote peer and ignores self."""
    engine = DiscoveryEngine(node_manager=mock_node_manager)

    # 1. Simulate discovery of a remote peer
    remote_peer_packet = {
        "node_id": "NODE-REMOTE-01",
        "name": "Laptop-Beta",
        "role": "responder",
        "ip_address": "192.168.1.42",
        "api_port": 8000,
        "latency_ms": 5.4,
        "discovery_method": "UDP_Broadcast",
    }
    engine._on_peer_discovered(remote_peer_packet)

    active_peers = mock_node_manager.get_active_peers()
    assert len(active_peers) == 1
    assert active_peers[0]["node_id"] == "NODE-REMOTE-01"
    assert active_peers[0]["name"] == "Laptop-Beta"

    # 2. Simulate discovery of self -> must be ignored
    self_packet = {
        "node_id": mock_node_manager.node_id,
        "name": "Test-Node-Alpha",
        "role": "commander",
        "ip_address": "127.0.0.1",
        "api_port": 8000,
        "discovery_method": "UDP_Broadcast",
    }
    engine._on_peer_discovered(self_packet)

    # Peer count must still be 1
    assert len(mock_node_manager.get_active_peers()) == 1


def test_peer_timeout_and_offline_status(mock_node_manager):
    """Verify peer transitions to offline when no beacon is received within timeout."""
    engine = DiscoveryEngine(node_manager=mock_node_manager)

    # Register peer with an old last_seen timestamp
    stale_peer = {
        "node_id": "NODE-STALE-99",
        "name": "Stale-Node",
        "role": "responder",
        "ip_address": "192.168.1.99",
        "api_port": 8000,
        "discovery_method": "mDNS",
    }
    engine._on_peer_discovered(stale_peer)

    # Artificially age the peer beyond 30-second threshold
    mock_node_manager._active_peers["NODE-STALE-99"]["last_seen"] = time.time() - 45.0

    active_peers = mock_node_manager.get_active_peers(timeout_seconds=30.0)
    assert len(active_peers) == 0
    assert mock_node_manager._active_peers["NODE-STALE-99"]["status"] == "offline"


def test_discovery_engine_lifecycle(mock_node_manager):
    """Verify engine start and clean shutdown."""
    engine = DiscoveryEngine(node_manager=mock_node_manager)
    # Start engine
    engine.start()
    assert engine.is_running is True

    # Stop engine
    engine.stop()
    assert engine.is_running is False
