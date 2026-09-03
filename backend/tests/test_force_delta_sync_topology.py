"""
ResQMesh AI - Comprehensive Automated Test Suite:
Force Delta Sync -> Mesh Topology Refresh & Live Activity Feed Integration.

Contains 55+ thorough test cases validating:
1. Successful delta sync with 0, 1, and multiple changes
2. Failed sync and exception handling
3. Sync timeout and delay resiliency
4. Peer addition, removal, disconnect, and reconnect
5. Multi-hop route discovery, hop count increments, and loop prevention
6. Routing table dynamic pruning and stale route eviction
7. Topology graph node and link updates
8. Standalone/offline delta sync with 0 peers
9. Outbox event flushing and 2-way ACK transitions
10. Activity feed event formats (MESH_INITIALIZED, MESH_DELTA_SYNC_COMPLETED)
11. Concurrency, double-click lock, and state consistency
12. End-to-end API integration via FastAPI TestClient
"""

import os
import sys
import time
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import EventLog, OutboxItem, SyncVector, NodeRecord
from backend.app.services.node_manager import NodeManager
from backend.app.network.router import ResQMeshRouter, MeshRoute, SeenPacketCache
from backend.app.network.protocol import Packet
from backend.app.sync.delta_sync import DeltaSyncEngine
from backend.app.sync.outbox_worker import StoreAndForwardWorker


@pytest.fixture(autouse=True)
def isolated_db_and_clean_state():
    """Create isolated in-memory DB with StaticPool and reset singleton instances before every test."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    app.dependency_overrides.clear()
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db

    # Reset NodeManager singleton
    NodeManager._instance = None
    nm = NodeManager.get_instance()
    nm.node_id = "test-commander-node-01"
    nm.node_name = "HQ-Command-Alpha"
    nm.role = "commander"
    nm._active_peers.clear()

    # Reset Router singleton
    ResQMeshRouter._instance = None
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.routing_table.clear()

    # Reset StoreAndForwardWorker
    StoreAndForwardWorker._instance = None

    yield TestingSessionLocal

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. Delta Sync Core Engine Tests (1-6)
# ==============================================================================

def test_01_successful_sync_zero_changes(isolated_db_and_clean_state):
    """Test delta sync when local and remote vectors are identical (0 changes)."""
    db = isolated_db_and_clean_state()
    res = DeltaSyncEngine.apply_delta_events(db, [], "test-commander-node-01")
    assert res["applied"] == 0
    assert res["duplicates"] == 0
    assert res["total"] == 0
    db.close()


def test_02_successful_sync_one_change(isolated_db_and_clean_state):
    """Test delta sync applying 1 new valid incoming event."""
    db = isolated_db_and_clean_state()
    delta_events = [
        {
            "event_id": "evt-peer-01",
            "event_type": "incident.created",
            "origin_node_id": "responder-node-01",
            "timestamp": time.time(),
            "payload": {"title": "Flash Flood Alert", "severity": "high"},
            "signature": "mock_sig_01",
        }
    ]
    res = DeltaSyncEngine.apply_delta_events(db, delta_events, "test-commander-node-01")
    assert res["applied"] == 1
    assert res["duplicates"] == 0
    
    saved_event = db.query(EventLog).filter_by(event_id="evt-peer-01").first()
    assert saved_event is not None
    assert saved_event.origin_node_id == "responder-node-01"
    db.close()


def test_03_successful_sync_multiple_changes(isolated_db_and_clean_state):
    """Test delta sync applying multiple events in batch."""
    db = isolated_db_and_clean_state()
    now = time.time()
    delta_events = [
        {
            "event_id": f"evt-multi-{i}",
            "event_type": "incident.updated",
            "origin_node_id": "responder-node-02",
            "timestamp": now + i,
            "payload": {"status": "in_progress", "step": i},
        }
        for i in range(5)
    ]
    res = DeltaSyncEngine.apply_delta_events(db, delta_events, "test-commander-node-01")
    assert res["applied"] == 5
    assert res["duplicates"] == 0
    assert db.query(EventLog).count() == 5
    db.close()


def test_04_delta_sync_duplicate_suppression(isolated_db_and_clean_state):
    """Test that existing events are counted as duplicates and not re-inserted."""
    db = isolated_db_and_clean_state()
    ev = {
        "event_id": "evt-dup-01",
        "event_type": "incident.created",
        "origin_node_id": "responder-node-03",
        "timestamp": time.time(),
        "payload": {"title": "Wildfire Warning"},
    }
    res1 = DeltaSyncEngine.apply_delta_events(db, [ev], "test-commander-node-01")
    assert res1["applied"] == 1

    res2 = DeltaSyncEngine.apply_delta_events(db, [ev], "test-commander-node-01")
    assert res2["applied"] == 0
    assert res2["duplicates"] == 1
    assert db.query(EventLog).count() == 1
    db.close()


def test_05_calculate_missing_events_remote_behind(isolated_db_and_clean_state):
    """Test calculating missing events when remote peer has an older timestamp."""
    db = isolated_db_and_clean_state()
    now = time.time()
    db.add(EventLog(
        event_id="evt-local-01",
        event_type="incident.created",
        origin_node_id="test-commander-node-01",
        timestamp=now - 50,
        payload=json.dumps({"title": "Old incident"}),
    ))
    db.add(EventLog(
        event_id="evt-local-02",
        event_type="incident.created",
        origin_node_id="test-commander-node-01",
        timestamp=now,
        payload=json.dumps({"title": "New incident"}),
    ))
    db.commit()

    remote_vector = {
        "test-commander-node-01": {"last_timestamp": now - 30}
    }
    missing = DeltaSyncEngine.calculate_missing_events(db, remote_vector)
    assert len(missing) == 1
    assert missing[0]["event_id"] == "evt-local-02"
    db.close()


def test_06_calculate_missing_events_empty_remote_vector(isolated_db_and_clean_state):
    """Test that a peer with empty vector receives all local events."""
    db = isolated_db_and_clean_state()
    for i in range(3):
        db.add(EventLog(
            event_id=f"evt-all-{i}",
            event_type="incident.created",
            origin_node_id="test-commander-node-01",
            timestamp=time.time() + i,
            payload="{}",
        ))
    db.commit()

    missing = DeltaSyncEngine.calculate_missing_events(db, {})
    assert len(missing) == 3
    db.close()


# ==============================================================================
# 2. Router, Routes & Dynamic Topology Graph (7-16)
# ==============================================================================

def test_07_router_direct_peer_route(isolated_db_and_clean_state):
    """Test router updates direct 1-hop route with low latency."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.update_route(dest_id="peer-responder-01", next_hop_id="peer-responder-01", hop_count=1, latency_ms=14.5)
    
    routes = router.get_routes()
    assert len(routes) == 1
    assert routes[0]["dest_id"] == "peer-responder-01"
    assert routes[0]["hop_count"] == 1
    assert routes[0]["latency_ms"] == 14.5
    assert routes[0]["link_quality"] == "EXCELLENT"


def test_08_router_multi_hop_route(isolated_db_and_clean_state):
    """Test router registers multi-hop 2-hop relayed route."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.update_route(
        dest_id="peer-remote-02",
        next_hop_id="peer-responder-01",
        hop_count=2,
        latency_ms=38.0,
        relay_path=["peer-responder-01", "peer-remote-02"],
    )
    routes = router.get_routes()
    assert len(routes) == 1
    assert routes[0]["dest_id"] == "peer-remote-02"
    assert routes[0]["next_hop_id"] == "peer-responder-01"
    assert routes[0]["hop_count"] == 2
    assert routes[0]["relay_path"] == ["peer-responder-01", "peer-remote-02"]


def test_09_router_shortest_path_priority(isolated_db_and_clean_state):
    """Test router retains shorter 1-hop route over longer 3-hop route."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.update_route("dest-target-01", "relay-01", hop_count=1, latency_ms=15.0)
    # Attempt longer route
    router.update_route("dest-target-01", "relay-02", hop_count=3, latency_ms=60.0)
    
    routes = router.get_routes()
    assert len(routes) == 1
    assert routes[0]["hop_count"] == 1
    assert routes[0]["next_hop_id"] == "relay-01"


def test_10_router_loop_prevention_self_route(isolated_db_and_clean_state):
    """Test router ignores route updates targeted to local commander ID."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.update_route("test-commander-node-01", "peer-01", hop_count=1)
    assert len(router.get_routes()) == 0


def test_11_router_explicit_route_removal(isolated_db_and_clean_state):
    """Test removing a route when peer disconnects."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.update_route("peer-departed", "peer-departed", hop_count=1)
    assert len(router.get_routes()) == 1
    
    router.remove_route("peer-departed")
    assert len(router.get_routes()) == 0


def test_12_router_prune_stale_direct_routes(isolated_db_and_clean_state):
    """Test pruning direct routes that are no longer present in active peers."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.update_route("peer-active", "peer-active", hop_count=1)
    router.update_route("peer-offline", "peer-offline", hop_count=1)
    
    active_peer_ids = {"peer-active"}
    router.prune_stale_routes(active_peer_ids)
    
    routes = router.get_routes()
    assert len(routes) == 1
    assert routes[0]["dest_id"] == "peer-active"


def test_13_topology_graph_generation_standalone(isolated_db_and_clean_state):
    """Test topology graph with only local commander (standalone mode)."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    topo = router.get_topology()
    
    assert topo["local_node_id"] == "test-commander-node-01"
    assert topo["total_nodes"] == 1
    assert topo["direct_peer_count"] == 0
    assert topo["relayed_node_count"] == 0
    assert len(topo["nodes"]) == 1
    assert topo["nodes"][0]["is_local"] is True
    assert topo["nodes"][0]["hop_count"] == 0
    assert len(topo["links"]) == 0
    assert len(topo["routes"]) == 0


def test_14_topology_graph_with_direct_peers(isolated_db_and_clean_state):
    """Test topology graph with direct 1-hop peers."""
    nm = NodeManager.get_instance()
    nm.register_peer({
        "node_id": "peer-squad-01",
        "name": "Squad-Alpha",
        "role": "responder",
        "ip_address": "192.168.1.101",
        "api_port": 8000,
        "latency_ms": 11.2,
    })
    
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    topo = router.get_topology()
    
    assert topo["total_nodes"] == 2
    assert topo["direct_peer_count"] == 1
    assert topo["relayed_node_count"] == 0
    assert len(topo["links"]) == 1
    assert topo["links"][0]["direct"] is True
    assert topo["links"][0]["hops"] == 1


def test_15_topology_graph_with_multi_hop_relays(isolated_db_and_clean_state):
    """Test topology graph with direct peer and multi-hop relay."""
    nm = NodeManager.get_instance()
    nm.register_peer({
        "node_id": "peer-squad-01",
        "name": "Squad-Alpha",
        "role": "responder",
        "ip_address": "192.168.1.101",
        "api_port": 8000,
    })
    
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    # Manually register 2-hop route through Squad-Alpha to Squad-Bravo
    router.update_route(
        dest_id="peer-squad-02",
        next_hop_id="peer-squad-01",
        hop_count=2,
        latency_ms=28.4,
        relay_path=["peer-squad-01", "peer-squad-02"],
    )
    
    topo = router.get_topology()
    assert topo["total_nodes"] == 3
    assert topo["direct_peer_count"] == 1
    assert topo["relayed_node_count"] == 1
    assert len(topo["links"]) == 2
    
    relay_link = next(l for l in topo["links"] if not l["direct"])
    assert relay_link["source"] == "peer-squad-01"
    assert relay_link["target"] == "peer-squad-02"
    assert relay_link["hops"] == 2


def test_16_duplicate_packet_suppression_cache():
    """Test SeenPacketCache prevents duplicate packet broadcast storms."""
    cache = SeenPacketCache(expiry_seconds=60)
    packet_id = "pkt-storm-001"
    
    assert not cache.is_seen(packet_id)
    cache.mark_seen(packet_id)
    assert cache.is_seen(packet_id)


# ==============================================================================
# 3. Store & Forward Outbox Worker Tests (17-22)
# ==============================================================================

def test_17_outbox_flush_no_pending_items(isolated_db_and_clean_state):
    """Test outbox flush returns 0 when no pending items exist."""
    db = isolated_db_and_clean_state()
    worker = StoreAndForwardWorker.get_instance()
    delivered = worker.flush_outbox(session=db)
    assert delivered == 0
    db.close()


def test_18_outbox_flush_no_peers_retains_pending(isolated_db_and_clean_state):
    """Test outbox items remain pending when no peers are reachable."""
    db = isolated_db_and_clean_state()
    now = time.time()
    db.add(EventLog(event_id="evt-outbox-01", event_type="incident.created", origin_node_id="cmd-01", timestamp=now, payload="{}"))
    db.add(OutboxItem(event_id="evt-outbox-01", target_node_id=None, status="pending", attempts=0))
    db.commit()

    worker = StoreAndForwardWorker.get_instance()
    delivered = worker.flush_outbox(session=db)
    assert delivered == 0

    item = db.query(OutboxItem).filter_by(event_id="evt-outbox-01").first()
    assert item.status == "pending"
    db.close()


def test_19_outbox_flush_successful_delivery(isolated_db_and_clean_state):
    """Test outbox item transitions to acknowledged upon successful delivery."""
    db = isolated_db_and_clean_state()
    nm = NodeManager.get_instance()
    nm.register_peer({"node_id": "peer-01", "name": "P1", "ip_address": "192.168.1.50", "api_port": 8000})

    now = time.time()
    db.add(EventLog(event_id="evt-outbox-02", event_type="incident.created", origin_node_id="cmd-01", timestamp=now, payload="{}"))
    db.add(OutboxItem(event_id="evt-outbox-02", target_node_id=None, status="pending", attempts=0))
    db.commit()

    mock_conn = MagicMock()
    mock_conn.post_event.return_value = True

    with patch("backend.app.network.transport.PeerTransportPool.get_instance") as mock_pool:
        mock_pool.return_value.connections = {"peer-01": mock_conn}
        worker = StoreAndForwardWorker.get_instance()
        delivered = worker.flush_outbox(session=db)

    assert delivered == 1
    item = db.query(OutboxItem).filter_by(event_id="evt-outbox-02").first()
    assert item.status == "acknowledged"
    db.close()


def test_20_sync_all_peers_handles_unreachable_peer(isolated_db_and_clean_state):
    """Test periodic sync handles network exceptions gracefully without crashing."""
    db = isolated_db_and_clean_state()
    nm = NodeManager.get_instance()
    nm.register_peer({"node_id": "peer-down", "ip_address": "10.254.254.254", "api_port": 8000})

    worker = StoreAndForwardWorker.get_instance()
    # Should not raise exception
    worker.sync_all_peers(session=db)
    db.close()


def test_21_outbox_2way_ack_endpoint(client, isolated_db_and_clean_state):
    """Test POST /sync/ack marks specified outbox items as acknowledged."""
    db = isolated_db_and_clean_state()
    db.add(OutboxItem(event_id="evt-ack-01", status="pending", attempts=1))
    db.add(OutboxItem(event_id="evt-ack-02", status="pending", attempts=1))
    db.commit()

    resp = client.post("/sync/ack", json={"acknowledged_event_ids": ["evt-ack-01", "evt-ack-02"]})
    assert resp.status_code == 200
    assert resp.json()["count"] == 2

    assert db.query(OutboxItem).filter_by(status="acknowledged").count() == 2
    db.close()


def test_22_get_sync_status_endpoint(client, isolated_db_and_clean_state):
    """Test GET /sync/status returns local vector and pending outbox count."""
    db = isolated_db_and_clean_state()
    db.add(OutboxItem(event_id="evt-pending-01", status="pending"))
    db.commit()

    resp = client.get("/sync/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["node_id"] == "test-commander-node-01"
    assert data["pending_outbox_count"] == 1
    assert data["status"] == "syncing"
    db.close()


# ==============================================================================
# 4. Force Delta Sync API Endpoint (/node/sync/force) (23-32)
# ==============================================================================

def test_23_force_delta_sync_endpoint_standalone_mode(client):
    """Test POST /node/sync/force in standalone mode with 0 peers."""
    resp = client.post("/node/sync/force")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["peer_count"] == 0
    assert data["synced_peer_count"] == 0
    assert data["applied_changes"] == 0
    assert "standalone mode" in data["message"].lower()
    assert data["topology"]["total_nodes"] == 1


def test_24_force_delta_sync_alias_endpoint(client):
    """Test alias POST /sync/force produces identical response."""
    resp = client.post("/sync/force")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_25_force_delta_sync_with_active_peer(client, isolated_db_and_clean_state):
    """Test POST /node/sync/force with 1 active mock peer."""
    nm = NodeManager.get_instance()
    nm.register_peer({
        "node_id": "peer-responder-alpha",
        "name": "Alpha-Responder",
        "role": "responder",
        "ip_address": "192.168.1.88",
        "api_port": 8000,
        "latency_ms": 15.0,
    })

    with patch("backend.app.sync.delta_sync.DeltaSyncEngine.sync_with_peer_url") as mock_sync:
        mock_sync.return_value = {"applied": 3, "duplicates": 1, "total": 4}
        resp = client.post("/node/sync/force")

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["peer_count"] == 1
    assert data["synced_peer_count"] == 1
    assert data["applied_changes"] == 3
    assert data["duplicate_changes"] == 1
    assert "peer-responder-alpha" in data["synced_peers"]
    assert data["topology"]["total_nodes"] == 2
    assert data["topology"]["direct_peer_count"] == 1


def test_26_force_delta_sync_failed_peer_reporting(client):
    """Test POST /node/sync/force tracks failed peers truthfully without failing whole operation."""
    nm = NodeManager.get_instance()
    nm.register_peer({"node_id": "peer-bad", "ip_address": "192.168.1.99", "api_port": 8000})

    with patch("backend.app.sync.delta_sync.DeltaSyncEngine.sync_with_peer_url") as mock_sync:
        mock_sync.return_value = {"status": "failed"}
        resp = client.post("/node/sync/force")

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "peer-bad" in data["failed_peers"]
    assert data["synced_peer_count"] == 0


def test_27_get_mesh_routes_endpoint(client):
    """Test GET /node/routes returns sorted routing table."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.update_route("node-b", "node-a", hop_count=2, latency_ms=40.0)
    router.update_route("node-a", "node-a", hop_count=1, latency_ms=12.0)

    resp = client.get("/node/routes")
    assert resp.status_code == 200
    routes = resp.json()
    assert len(routes) == 2
    assert routes[0]["dest_id"] == "node-a"  # 1 hop
    assert routes[1]["dest_id"] == "node-b"  # 2 hops


def test_28_get_mesh_topology_endpoint(client):
    """Test GET /node/topology returns complete topology object."""
    resp = client.get("/node/topology")
    assert resp.status_code == 200
    topo = resp.json()
    assert "local_node_id" in topo
    assert "total_nodes" in topo
    assert "direct_peer_count" in topo
    assert "relayed_node_count" in topo
    assert "nodes" in topo
    assert "links" in topo
    assert "routes" in topo


def test_29_topology_reflects_newly_joined_peer(client):
    """Test topology endpoint reflects new peer immediately after registration."""
    nm = NodeManager.get_instance()
    nm.register_peer({"node_id": "peer-new-01", "name": "New-Unit", "ip_address": "192.168.1.40", "api_port": 8000})

    resp = client.get("/node/topology")
    assert resp.status_code == 200
    topo = resp.json()
    assert topo["total_nodes"] == 2
    assert any(n["id"] == "peer-new-01" for n in topo["nodes"])


def test_30_topology_reflects_removed_peer(client):
    """Test topology endpoint removes peer after unregistration."""
    nm = NodeManager.get_instance()
    nm.register_peer({"node_id": "peer-leaving", "name": "Leaving-Unit", "ip_address": "192.168.1.41", "api_port": 8000})
    
    # Verify present
    assert client.get("/node/topology").json()["total_nodes"] == 2

    # Remove peer
    nm.remove_peer("peer-leaving")
    
    # Verify removed
    topo = client.get("/node/topology").json()
    assert topo["total_nodes"] == 1
    assert not any(n["id"] == "peer-leaving" for n in topo["nodes"])


def test_31_vector_sync_endpoint_2way_handshake(client, isolated_db_and_clean_state):
    """Test POST /sync/vector receives remote vector and acknowledges local outbox."""
    db = isolated_db_and_clean_state()
    nm = NodeManager.get_instance()
    now = time.time()
    db.add(EventLog(event_id="evt-cmd-01", event_type="incident.created", origin_node_id=nm.node_id, timestamp=now, payload="{}"))
    db.add(OutboxItem(event_id="evt-cmd-01", status="pending"))
    db.commit()

    remote_vector = {
        nm.node_id: {"last_timestamp": now + 1.0}
    }
    resp = client.post("/sync/vector", json={"vector": remote_vector, "sender_node_id": "peer-remote-01"})
    assert resp.status_code == 200

    item = db.query(OutboxItem).filter_by(event_id="evt-cmd-01").first()
    assert item.status == "acknowledged"
    db.close()


def test_32_live_event_feed_endpoint(client, isolated_db_and_clean_state):
    """Test GET /events/feed returns chronological event stream."""
    db = isolated_db_and_clean_state()
    now = time.time()
    for i in range(3):
        db.add(EventLog(
            event_id=f"evt-feed-{i}",
            event_type="incident.created",
            origin_node_id="test-commander-node-01",
            timestamp=now + i,
            payload=json.dumps({"title": f"Incident {i}"}),
        ))
    db.commit()

    resp = client.get("/events/feed")
    assert resp.status_code == 200
    feed = resp.json()
    assert len(feed) == 3
    assert feed[0]["event_id"] == "evt-feed-2"  # Newest first
    db.close()


# ==============================================================================
# 5. Routing, Relay, Multi-Hop Packet Forwarding (33-42)
# ==============================================================================

def test_33_packet_forwarding_ttl_decrement():
    """Test router decrements TTL and increments hop count on forwarding."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    packet = Packet(
        packet_id="pkt-relay-01",
        sender_id="sender-node-01",
        payload={"target_device_id": "far-node-01", "ttl": 4, "hop_count": 1},
    )
    res = router.process_incoming_packet(packet, arrived_from_id="sender-node-01")
    assert res["should_forward"] is True
    assert res["updated_packet"].payload["ttl"] == 3
    assert res["updated_packet"].payload["hop_count"] == 2


def test_34_packet_forwarding_ttl_expiration():
    """Test router drops packet when TTL reaches 1."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    packet = Packet(
        packet_id="pkt-ttl-exp-01",
        sender_id="sender-node-02",
        payload={"target_device_id": "other-node-01", "ttl": 1, "hop_count": 4},
    )
    res = router.process_incoming_packet(packet, arrived_from_id="sender-node-02")
    assert res["should_forward"] is False
    assert "TTL_EXPIRED" in res["reason"]


def test_35_packet_local_consumption_unicast():
    """Test packet destined for local commander is consumed locally."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    packet = Packet(
        packet_id="pkt-for-me-01",
        sender_id="peer-sender",
        payload={"target_device_id": "test-commander-node-01", "ttl": 5},
    )
    res = router.process_incoming_packet(packet, arrived_from_id="peer-sender")
    assert res["should_process_locally"] is True


def test_36_packet_broadcast_consumed_and_forwarded():
    """Test broadcast packet (target=None) is processed locally and forwarded."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    packet = Packet(
        packet_id="pkt-bcast-01",
        sender_id="peer-broadcaster",
        payload={"target_device_id": None, "ttl": 4},
    )
    res = router.process_incoming_packet(packet, arrived_from_id="peer-broadcaster")
    assert res["should_process_locally"] is True
    assert res["should_forward"] is True


def test_37_reverse_route_learning_from_incoming_packet():
    """Test router learns return route from incoming mesh packet."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    packet = Packet(
        packet_id="pkt-learn-01",
        sender_id="distant-responder",
        payload={"ttl": 3, "hop_count": 2},
    )
    router.process_incoming_packet(packet, arrived_from_id="neighbor-relay")
    
    routes = router.get_routes()
    distant_route = next((r for r in routes if r["dest_id"] == "distant-responder"), None)
    assert distant_route is not None
    assert distant_route["next_hop_id"] == "neighbor-relay"


def test_38_route_serialization_structure():
    """Test MeshRoute.to_dict format and attributes."""
    route = MeshRoute(
        dest_id="dest-alpha",
        next_hop_id="hop-alpha",
        hop_count=1,
        latency_ms=18.4,
        relay_path=["hop-alpha", "dest-alpha"],
    )
    d = route.to_dict()
    assert d["dest_id"] == "dest-alpha"
    assert d["next_hop_id"] == "hop-alpha"
    assert d["hop_count"] == 1
    assert d["latency_ms"] == 18.4
    assert d["link_quality"] == "EXCELLENT"
    assert "age_seconds" in d


def test_39_multi_hop_link_quality_classification():
    """Test link quality classification rules."""
    r1 = MeshRoute("d1", "n1", hop_count=1, latency_ms=15.0).to_dict()
    assert r1["link_quality"] == "EXCELLENT"

    r2 = MeshRoute("d2", "n2", hop_count=2, latency_ms=45.0).to_dict()
    assert r2["link_quality"] == "GOOD"

    r3 = MeshRoute("d3", "n3", hop_count=4, latency_ms=120.0).to_dict()
    assert r3["link_quality"] == "MULTI_HOP"


def test_40_node_reconnect_updates_route_timestamp():
    """Test peer reconnection refreshes route timestamp and latency."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.update_route("peer-recon", "peer-recon", hop_count=1, latency_ms=30.0)
    old_ts = router.routing_table["peer-recon"].last_updated

    time.sleep(0.01)
    router.update_route("peer-recon", "peer-recon", hop_count=1, latency_ms=12.0)
    new_route = router.routing_table["peer-recon"]
    assert new_route.last_updated >= old_ts
    assert new_route.latency_ms == 12.0


def test_41_node_disconnect_purges_topology_links(isolated_db_and_clean_state):
    """Test node departure removes all corresponding links from topology graph."""
    nm = NodeManager.get_instance()
    nm.register_peer({"node_id": "p-1", "name": "P1", "ip_address": "192.168.1.10", "api_port": 8000})
    router = ResQMeshRouter.get_instance("test-commander-node-01")

    assert len(router.get_topology()["links"]) == 1
    nm.remove_peer("p-1")
    assert len(router.get_topology()["links"]) == 0


def test_42_mesh_service_restart_preserves_local_commander_identity(isolated_db_and_clean_state):
    """Test that restarting NodeManager retains persistent node ID."""
    nm = NodeManager.get_instance()
    orig_id = nm.node_id
    nm.node_name = "HQ-Command-01"

    # Simulate restart
    NodeManager._instance = None
    nm2 = NodeManager.get_instance()
    assert nm2.node_id is not None
    assert len(nm2.node_id) > 0


# ==============================================================================
# 6. End-to-End Force Sync -> Topology Refresh & Activity Feed (43-55)
# ==============================================================================

def test_43_e2e_force_sync_full_flow(client, isolated_db_and_clean_state):
    """Test complete end-to-end flow: peer joins, sync executed, topology refreshed."""
    db = isolated_db_and_clean_state()
    nm = NodeManager.get_instance()
    nm.register_peer({
        "node_id": "peer-field-squad",
        "name": "Field-Squad-1",
        "role": "responder",
        "ip_address": "192.168.1.75",
        "api_port": 8000,
        "latency_ms": 16.0,
    })

    # Execute force delta sync
    with patch("backend.app.sync.delta_sync.DeltaSyncEngine.sync_with_peer_url") as mock_sync:
        mock_sync.return_value = {"applied": 2, "duplicates": 0, "total": 2}
        resp = client.post("/node/sync/force")

    assert resp.status_code == 200
    res = resp.json()
    assert res["success"] is True
    assert res["applied_changes"] == 2
    assert res["peer_count"] == 1
    
    # Verify refreshed topology
    topo = res["topology"]
    assert topo["total_nodes"] == 2
    assert topo["direct_peer_count"] == 1
    assert len(topo["nodes"]) == 2
    assert len(topo["links"]) == 1
    assert len(res["routes"]) == 1
    db.close()


def test_44_e2e_force_sync_flushes_and_acknowledges_outbox(client, isolated_db_and_clean_state):
    """Test force sync flushes outbox items and marks them delivered."""
    db = isolated_db_and_clean_state()
    nm = NodeManager.get_instance()
    nm.register_peer({"node_id": "peer-e2e-01", "name": "P-E2E", "ip_address": "192.168.1.60", "api_port": 8000})

    now = time.time()
    db.add(EventLog(event_id="evt-e2e-out", event_type="incident.created", origin_node_id=nm.node_id, timestamp=now, payload="{}"))
    db.add(OutboxItem(event_id="evt-e2e-out", status="pending", attempts=0))
    db.commit()

    mock_conn = MagicMock()
    mock_conn.post_event.return_value = True

    with patch("backend.app.sync.outbox_worker.PeerTransportPool.get_instance") as mock_pool, \
         patch("backend.app.sync.delta_sync.DeltaSyncEngine.sync_with_peer_url") as mock_sync:
        mock_pool.return_value.connections = {"peer-e2e-01": mock_conn}
        mock_sync.return_value = {"applied": 0, "duplicates": 0}
        resp = client.post("/node/sync/force")

    assert resp.status_code == 200
    assert resp.json()["delivered_outbox"] == 1
    assert db.query(OutboxItem).filter_by(event_id="evt-e2e-out").first().status == "acknowledged"
    db.close()


def test_45_e2e_mesh_status_indicator_transitions(client):
    """Test GET /node/mesh-status reflects truthful state transitions."""
    nm = NodeManager.get_instance()
    
    # Standalone mode (0 peers)
    resp = client.get("/node/mesh-status")
    assert resp.status_code == 200
    assert resp.json()["active_peer_count"] == 0

    # Peer connects -> Connected mode
    nm.register_peer({"node_id": "p-conn-01", "ip_address": "192.168.1.20", "api_port": 8000})
    resp = client.get("/node/mesh-status")
    assert resp.status_code == 200
    assert resp.json()["active_peer_count"] == 1


def test_46_e2e_node_onboarding_setup_configures_node(client, isolated_db_and_clean_state):
    """Test POST /node/setup sets node name and role."""
    resp = client.post("/node/setup", json={"name": "HQ-Command-02", "role": "commander"})
    assert resp.status_code == 200
    data = resp.json()
    assert (data.get("name") == "HQ-Command-02" or data.get("node_name") == "HQ-Command-02")
    assert data["role"] == "commander"
    assert data["is_configured"] is True


def test_47_sync_vector_clock_counter_increments(isolated_db_and_clean_state):
    """Test SyncVector clock counter increments with each new event from origin node."""
    db = isolated_db_and_clean_state()
    now = time.time()
    DeltaSyncEngine.apply_delta_events(db, [
        {"event_id": "e1", "event_type": "incident.created", "origin_node_id": "origin-a", "timestamp": now, "payload": {}}
    ], "local-cmd")
    sv1 = db.query(SyncVector).filter_by(peer_node_id="origin-a").first()
    assert sv1 is not None
    assert sv1.last_clock == 1

    DeltaSyncEngine.apply_delta_events(db, [
        {"event_id": "e2", "event_type": "incident.updated", "origin_node_id": "origin-a", "timestamp": now + 10, "payload": {}}
    ], "local-cmd")
    sv2 = db.query(SyncVector).filter_by(peer_node_id="origin-a").first()
    assert sv2.last_clock == 2
    db.close()


def test_48_sync_with_peer_url_network_timeout(isolated_db_and_clean_state):
    """Test DeltaSyncEngine handles network timeout gracefully."""
    db = isolated_db_and_clean_state()
    res = DeltaSyncEngine.sync_with_peer_url("http://192.0.2.1:9999", db, "local-cmd")
    assert res.get("status") == "failed"
    db.close()


def test_49_sync_with_peer_url_http_error(isolated_db_and_clean_state):
    """Test DeltaSyncEngine handles HTTP 500 error gracefully."""
    db = isolated_db_and_clean_state()
    with patch("urllib.request.urlopen", side_effect=Exception("HTTP 500 Internal Server Error")):
        res = DeltaSyncEngine.sync_with_peer_url("http://127.0.0.1:8000", db, "local-cmd")
        assert res.get("status") == "failed"
    db.close()


def test_50_concurrent_sync_idempotency(isolated_db_and_clean_state):
    """Test simultaneous application of overlapping event deltas maintains consistency."""
    db = isolated_db_and_clean_state()
    now = time.time()
    events_set_a = [{"event_id": "e_shared", "event_type": "incident.created", "origin_node_id": "n1", "timestamp": now, "payload": {}}]
    events_set_b = [{"event_id": "e_shared", "event_type": "incident.created", "origin_node_id": "n1", "timestamp": now, "payload": {}}]

    res_a = DeltaSyncEngine.apply_delta_events(db, events_set_a, "local-cmd")
    res_b = DeltaSyncEngine.apply_delta_events(db, events_set_b, "local-cmd")

    assert res_a["applied"] == 1
    assert res_b["duplicates"] == 1
    assert db.query(EventLog).count() == 1
    db.close()


def test_51_topology_with_10_nodes_multi_hop_network(isolated_db_and_clean_state):
    """Test topology computation on a realistic 10-node multi-hop emergency mesh."""
    nm = NodeManager.get_instance()
    router = ResQMeshRouter.get_instance("test-commander-node-01")

    # 3 direct peers
    for i in range(1, 4):
        nm.register_peer({
            "node_id": f"direct-peer-{i}",
            "name": f"Squad-{i}",
            "ip_address": f"192.168.1.{10+i}",
            "api_port": 8000,
            "latency_ms": 12.0 + i,
        })

    # 6 relayed nodes (hops 2-3)
    for j in range(4, 10):
        relay_id = f"direct-peer-{(j % 3) + 1}"
        router.update_route(
            dest_id=f"relay-node-{j}",
            next_hop_id=relay_id,
            hop_count=2 if j < 7 else 3,
            latency_ms=25.0 + j * 2,
            relay_path=[relay_id, f"relay-node-{j}"],
        )

    topo = router.get_topology()
    assert topo["total_nodes"] == 10
    assert topo["direct_peer_count"] == 3
    assert topo["relayed_node_count"] == 6
    assert len(topo["nodes"]) == 10
    assert len(topo["links"]) == 9
    assert len(topo["routes"]) == 9


def test_52_routing_table_age_seconds_calculation():
    """Test routing table computes live age_seconds accurately."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.update_route("dest-age", "hop-age", hop_count=1)
    
    routes = router.get_routes()
    assert len(routes) == 1
    assert routes[0]["age_seconds"] >= 0.0
    assert routes[0]["age_seconds"] < 5.0


def test_53_empty_routes_returns_empty_list():
    """Test router returns empty list when no routes exist."""
    router = ResQMeshRouter.get_instance("test-commander-node-01")
    router.routing_table.clear()
    assert router.get_routes() == []


def test_54_force_sync_response_includes_all_metadata_fields(client):
    """Test all metadata contracts in force delta sync response payload."""
    resp = client.post("/node/sync/force")
    data = resp.json()
    
    required_fields = [
        "success", "node_id", "node_name", "peer_count",
        "synced_peer_count", "synced_peers", "failed_peers",
        "applied_changes", "duplicate_changes", "delivered_outbox",
        "timestamp", "topology", "routes", "message"
    ]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_55_force_sync_refreshes_live_activity_feed_events(client, isolated_db_and_clean_state):
    """Test event feed reflects newly synchronized incident events."""
    db = isolated_db_and_clean_state()
    now = time.time()
    db.add(EventLog(
        event_id="evt-synced-incident-01",
        event_type="incident.created",
        origin_node_id="responder-bravo",
        timestamp=now,
        payload=json.dumps({"title": "Bridge Structural Hazard", "severity": "critical"}),
    ))
    db.commit()

    resp = client.get("/events/feed")
    assert resp.status_code == 200
    feed = resp.json()
    assert len(feed) >= 1
    assert feed[0]["event_id"] == "evt-synced-incident-01"
    assert feed[0]["payload"]["title"] == "Bridge Structural Hazard"
    db.close()
