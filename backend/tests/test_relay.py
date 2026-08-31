import os
import sys
import time
import json
import pytest
from unittest.mock import MagicMock

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.network.relay import MeshRelayManager
from backend.app.services.node_manager import NodeManager
from backend.app.network.transport import PeerTransportPool


@pytest.fixture
def relay_manager():
    mgr = MeshRelayManager()
    mgr.seen_cache._seen.clear()
    NodeManager.get_instance()._active_peers.clear()
    PeerTransportPool.get_instance().connections.clear()
    return mgr


def test_relay_ttl_decrement_and_hop_increment(relay_manager):
    """Verify that a forwarded event decrements TTL by 1 and increments hop_count by 1."""
    event_dict = {
        "event_id": "evt-hop-101",
        "event_type": "incident.created",
        "origin_node_id": "NODE-ORIGIN",
        "ttl": 5,
        "hop_count": 0,
        "payload": {"title": "Wildfire"},
    }

    result = relay_manager.handle_and_relay_event(event_dict, incoming_sender_id="NODE-ORIGIN")
    assert result["relayed"] is True
    assert result["new_ttl"] == 4
    assert result["new_hop_count"] == 1


def test_relay_drops_packet_when_ttl_expired(relay_manager):
    """Verify that when TTL reaches 1, the relay stops forwarding."""
    event_dict = {
        "event_id": "evt-ttl-expired-1",
        "event_type": "report.created",
        "origin_node_id": "NODE-ORIGIN",
        "ttl": 1,
        "hop_count": 4,
        "payload": {"description": "Smoke plume"},
    }

    result = relay_manager.handle_and_relay_event(event_dict, incoming_sender_id="NODE-ORIGIN")
    assert result["relayed"] is False
    assert result["reason"] == "TTL_EXPIRED"


def test_relay_duplicate_loop_suppression(relay_manager):
    """Verify that an already-seen event is dropped and not forwarded a second time."""
    event_dict = {
        "event_id": "evt-loop-test-1",
        "event_type": "message.created",
        "origin_node_id": "NODE-ORIGIN",
        "ttl": 4,
        "hop_count": 1,
        "payload": {"text": "All clear"},
    }

    # First attempt: forwarded
    r1 = relay_manager.handle_and_relay_event(event_dict, incoming_sender_id="NODE-ORIGIN")
    assert r1["relayed"] is True

    # Second attempt (duplicate loop): dropped
    r2 = relay_manager.handle_and_relay_event(event_dict, incoming_sender_id="NODE-RELAY-2")
    assert r2["relayed"] is False
    assert r2["reason"] == "DUPLICATE_SUPPRESSED"


def test_relay_excludes_incoming_sender(relay_manager):
    """Verify adjacent peer broadcast forwards to other peers but not back to the sender."""
    nm = NodeManager.get_instance()
    nm.setup_node("NODE-LOCAL-RELAY", "relay")

    # Peer 1 (Sender): Node-A
    nm.register_peer({
        "node_id": "NODE-A",
        "name": "Sender-A",
        "ip_address": "192.168.1.10",
        "api_port": 8000,
    })
    # Peer 2 (Forward Target): Node-C
    nm.register_peer({
        "node_id": "NODE-C",
        "name": "Recipient-C",
        "ip_address": "192.168.1.30",
        "api_port": 8000,
    })

    mock_conn_a = MagicMock()
    mock_conn_c = MagicMock()
    mock_conn_c.post_event.return_value = True

    pool = PeerTransportPool.get_instance()
    pool.connections["NODE-A"] = mock_conn_a
    pool.connections["NODE-C"] = mock_conn_c

    event_dict = {
        "event_id": "evt-relay-exclude-test",
        "event_type": "incident.created",
        "origin_node_id": "NODE-A",
        "ttl": 3,
        "hop_count": 1,
        "payload": {},
    }

    relay_manager._broadcast_to_adjacent_peers(event_dict, incoming_sender_id="NODE-A")

    # Node-A must NOT be called (split-horizon / no echo)
    mock_conn_a.post_event.assert_not_called()
    # Node-C must be called
    mock_conn_c.post_event.assert_called_once()
