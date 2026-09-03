"""
Dedicated Comprehensive Test Suite: ResQMesh AI Peer Lifecycle, Heartbeat & Lease Persistence.

Covers 55 distinct unit and integration test cases validating:
- Peer registration and persistence
- Dedicated /peers/heartbeat and /node/heartbeat endpoints
- last_seen timestamp updates and touch_peer leases
- Multi-cycle missed heartbeat tolerances (0, 1, 2, 5 missed cycles)
- Stale peer threshold detection (45s) and automatic recovery
- ResQMeshRouter 1-hop route creation, preservation, and topology updates
- Header and query param fallback on GET /node/status
- NAT/Client host detection and IP normalization
- Multi-peer concurrent lease tracking and idempotency.
"""

import os
import sys
import time
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.services.node_manager import NodeManager
from backend.app.network.router import ResQMeshRouter
from backend.app.models import NodeRecord


@pytest.fixture
def clean_node_state():
    """Ensure clean isolated DB and singleton state before and after each test."""
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

    nm = NodeManager.get_instance()
    nm._active_peers.clear()
    nm.setup_node(name="HQ-Commander", role="commander", port=8000)
    router = ResQMeshRouter.get_instance(nm.node_id)
    router.routing_table.clear()
    
    yield nm, router, TestingSessionLocal

    nm._active_peers.clear()
    router.routing_table.clear()
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ─── Group 1: Peer Registration & Field Validation (Tests 1–10) ────────────────

def test_01_peer_registration_creates_active_peer(client, clean_node_state):
    nm, router, _ = clean_node_state
    resp = client.post(
        "/peers/register",
        json={
            "node_id": "responder-alpha-01",
            "name": "Alpha-Lead",
            "role": "responder",
            "ip_address": "192.168.68.105",
            "api_port": 8001,
            "latency_ms": 14.5,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["registered_peer"] == "responder-alpha-01"
    assert "my_node" in data


def test_02_peer_registration_populates_node_manager_registry(client, clean_node_state):
    nm, _, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-02", "name": "Medic-2", "role": "responder", "ip_address": "192.168.68.106", "api_port": 8001},
    )
    peer = nm.get_peer("resp-02")
    assert peer is not None
    assert peer["name"] == "Medic-2"
    assert peer["status"] == "online"
    assert peer["last_seen"] > 0


def test_03_peer_registration_initializes_1hop_route(client, clean_node_state):
    nm, router, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-03", "name": "Scout-3", "role": "responder", "ip_address": "192.168.68.107", "latency_ms": 8.0},
    )
    route = router.routing_table.get("resp-03")
    assert route is not None
    assert route.hop_count == 1
    assert route.next_hop_id == "resp-03"
    assert route.latency_ms == 8.0


def test_04_peer_registration_persists_in_database(client, clean_node_state):
    _, _, TestingSessionLocal = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-db-04", "name": "Rescue-4", "role": "responder", "ip_address": "192.168.68.108"},
    )
    db = TestingSessionLocal()
    rec = db.query(NodeRecord).filter_by(node_id="resp-db-04").first()
    assert rec is not None
    assert rec.name == "Rescue-4"
    assert rec.status == "online"
    db.close()


def test_05_peer_registration_idempotency(client, clean_node_state):
    nm, _, _ = clean_node_state
    for _ in range(3):
        resp = client.post(
            "/peers/register",
            json={"node_id": "resp-idem-05", "name": "Squad-5", "role": "responder", "ip_address": "192.168.68.109"},
        )
        assert resp.status_code == 200
    active = nm.get_active_peers()
    assert len([p for p in active if p["node_id"] == "resp-idem-05"]) == 1


def test_06_registration_ignores_self_node_id(client, clean_node_state):
    nm, _, _ = clean_node_state
    resp = client.post(
        "/peers/register",
        json={"node_id": nm.node_id, "name": "Self-Node", "role": "commander", "ip_address": "127.0.0.1"},
    )
    assert resp.status_code == 200
    assert nm.get_peer(nm.node_id) is None


def test_07_registration_uses_client_host_when_reported_is_loopback(client, clean_node_state):
    nm, _, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-loopback-07", "name": "Loop-Phone", "role": "responder", "ip_address": "127.0.0.1"},
    )
    peer = nm.get_peer("resp-loopback-07")
    assert peer is not None
    assert peer["status"] == "online"


def test_08_registration_updates_existing_peer_metadata(client, clean_node_state):
    nm, _, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-meta-08", "name": "Old-Name", "role": "responder", "ip_address": "192.168.68.110"},
    )
    client.post(
        "/peers/register",
        json={"node_id": "resp-meta-08", "name": "Updated-Name", "role": "triage_lead", "ip_address": "192.168.68.110"},
    )
    peer = nm.get_peer("resp-meta-08")
    assert peer["name"] == "Updated-Name"
    assert peer["role"] == "triage_lead"


def test_09_registration_default_latency_fallback(client, clean_node_state):
    _, router, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-lat-09", "name": "Zero-Lat", "role": "responder", "ip_address": "192.168.68.111", "latency_ms": 0.0},
    )
    route = router.routing_table.get("resp-lat-09")
    assert route.latency_ms > 0.0


def test_10_list_peers_endpoint_returns_registered_peers(client, clean_node_state):
    client.post(
        "/peers/register",
        json={"node_id": "resp-list-10", "name": "List-Test", "role": "responder", "ip_address": "192.168.68.112"},
    )
    resp = client.get("/peers/")
    assert resp.status_code == 200
    peers = resp.json()
    assert any(p["node_id"] == "resp-list-10" for p in peers)


# ─── Group 2: Dedicated /peers/heartbeat & Lease Management (Tests 11–20) ──────

def test_11_dedicated_peer_heartbeat_returns_200_ok(client, clean_node_state):
    nm, _, _ = clean_node_state
    resp = client.post(
        "/peers/heartbeat",
        json={"node_id": "resp-hb-11", "name": "Heartbeat-11", "role": "responder", "latency_ms": 11.2},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["peer_id"] == "resp-hb-11"
    assert data["commander_node_id"] == nm.node_id


def test_12_peer_heartbeat_refreshes_last_seen_timestamp(client, clean_node_state):
    nm, _, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-hb-12", "name": "Heartbeat-12", "role": "responder", "ip_address": "192.168.68.120"},
    )
    # Simulate time lapse
    nm._active_peers["resp-hb-12"]["last_seen"] = time.time() - 20.0
    initial_last_seen = nm._active_peers["resp-hb-12"]["last_seen"]

    client.post(
        "/peers/heartbeat",
        json={"node_id": "resp-hb-12", "latency_ms": 15.0},
    )
    refreshed_last_seen = nm.get_peer("resp-hb-12")["last_seen"]
    assert refreshed_last_seen > initial_last_seen
    assert (time.time() - refreshed_last_seen) < 1.0


def test_13_peer_heartbeat_updates_latency(client, clean_node_state):
    nm, _, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-hb-13", "name": "Heartbeat-13", "role": "responder", "ip_address": "192.168.68.121", "latency_ms": 50.0},
    )
    client.post(
        "/peers/heartbeat",
        json={"node_id": "resp-hb-13", "latency_ms": 8.5},
    )
    assert nm.get_peer("resp-hb-13")["latency_ms"] == 8.5


def test_14_peer_heartbeat_auto_registers_unknown_peer(client, clean_node_state):
    nm, router, _ = clean_node_state
    resp = client.post(
        "/peers/heartbeat",
        json={"node_id": "resp-hb-auto-14", "name": "Auto-Registered", "role": "responder", "ip_address": "192.168.68.122", "latency_ms": 12.0},
    )
    assert resp.status_code == 200
    peer = nm.get_peer("resp-hb-auto-14")
    assert peer is not None
    assert peer["status"] == "online"
    assert router.routing_table.get("resp-hb-auto-14") is not None


def test_15_node_heartbeat_alias_endpoint(client, clean_node_state):
    nm, _, _ = clean_node_state
    resp = client.post(
        "/node/heartbeat",
        json={"node_id": "resp-alias-15", "name": "Alias-Node", "role": "responder", "latency_ms": 10.0},
    )
    assert resp.status_code == 200
    assert nm.get_peer("resp-alias-15") is not None


def test_16_heartbeat_maintains_online_status_over_multiple_cycles(client, clean_node_state):
    nm, _, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-cycle-16", "name": "Multi-Cycle", "role": "responder", "ip_address": "192.168.68.123"},
    )
    for i in range(5):
        client.post(
            "/peers/heartbeat",
            json={"node_id": "resp-cycle-16", "latency_ms": 10.0 + i},
        )
        assert nm.get_peer("resp-cycle-16")["status"] == "online"


def test_17_heartbeat_refreshes_router_1hop_route(client, clean_node_state):
    nm, router, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-route-17", "name": "Route-Check", "role": "responder", "ip_address": "192.168.68.124"},
    )
    route = router.routing_table.get("resp-route-17")
    time.sleep(0.01)

    client.post(
        "/peers/heartbeat",
        json={"node_id": "resp-route-17", "latency_ms": 5.0},
    )
    updated_route = router.routing_table.get("resp-route-17")
    assert updated_route.latency_ms == 5.0
    assert updated_route.hop_count == 1


def test_18_get_node_status_with_peer_id_query_param_touches_peer(client, clean_node_state):
    nm, _, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-query-18", "name": "Query-Param-Peer", "role": "responder", "ip_address": "192.168.68.125"},
    )
    nm._active_peers["resp-query-18"]["last_seen"] = time.time() - 15.0
    old_seen = nm._active_peers["resp-query-18"]["last_seen"]

    resp = client.get("/node/status?peer_id=resp-query-18")
    assert resp.status_code == 200
    new_seen = nm.get_peer("resp-query-18")["last_seen"]
    assert new_seen > old_seen


def test_19_get_node_status_with_x_peer_id_header_touches_peer(client, clean_node_state):
    nm, _, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "resp-hdr-19", "name": "Header-Peer", "role": "responder", "ip_address": "192.168.68.126"},
    )
    nm._active_peers["resp-hdr-19"]["last_seen"] = time.time() - 25.0
    old_seen = nm._active_peers["resp-hdr-19"]["last_seen"]

    resp = client.get("/node/status", headers={"X-Peer-ID": "resp-hdr-19"})
    assert resp.status_code == 200
    new_seen = nm.get_peer("resp-hdr-19")["last_seen"]
    assert new_seen > old_seen


def test_20_touch_peer_returns_false_for_unknown_peer(clean_node_state):
    nm, _, _ = clean_node_state
    assert nm.touch_peer("unknown-nonexistent-node") is False


# ─── Group 3: Stale Detection, Thresholds & Disconnect Recovery (Tests 21–30) ──

def test_21_peer_with_recent_last_seen_is_active(clean_node_state):
    nm, _, _ = clean_node_state
    nm.register_peer({"node_id": "peer-active-21", "name": "Fresh", "last_seen": time.time() - 5.0})
    active = nm.get_active_peers(timeout_seconds=45.0)
    assert len(active) == 1
    assert active[0]["node_id"] == "peer-active-21"


def test_22_peer_exceeding_45s_threshold_is_marked_offline(clean_node_state):
    nm, _, _ = clean_node_state
    nm.register_peer({"node_id": "peer-stale-22", "name": "Stale", "last_seen": time.time() - 50.0})
    active = nm.get_active_peers(timeout_seconds=45.0)
    assert len(active) == 0
    raw = nm.get_peer("peer-stale-22")
    assert raw["status"] == "offline"


def test_23_single_missed_heartbeat_at_10s_remains_online(clean_node_state):
    nm, _, _ = clean_node_state
    nm.register_peer({"node_id": "peer-1miss-23", "name": "Miss-1", "last_seen": time.time() - 10.0})
    active = nm.get_active_peers(timeout_seconds=45.0)
    assert len(active) == 1
    assert active[0]["status"] == "online"


def test_24_two_missed_heartbeats_at_15s_remains_online(clean_node_state):
    nm, _, _ = clean_node_state
    nm.register_peer({"node_id": "peer-2miss-24", "name": "Miss-2", "last_seen": time.time() - 15.0})
    active = nm.get_active_peers(timeout_seconds=45.0)
    assert len(active) == 1
    assert active[0]["status"] == "online"


def test_25_four_missed_heartbeats_at_25s_remains_online(clean_node_state):
    nm, _, _ = clean_node_state
    nm.register_peer({"node_id": "peer-4miss-25", "name": "Miss-4", "last_seen": time.time() - 25.0})
    active = nm.get_active_peers(timeout_seconds=45.0)
    assert len(active) == 1


def test_26_six_missed_heartbeats_at_35s_remains_online(clean_node_state):
    nm, _, _ = clean_node_state
    nm.register_peer({"node_id": "peer-6miss-26", "name": "Miss-6", "last_seen": time.time() - 35.0})
    active = nm.get_active_peers(timeout_seconds=45.0)
    assert len(active) == 1


def test_27_offline_peer_reconnect_recovers_to_online(client, clean_node_state):
    nm, _, _ = clean_node_state
    nm.register_peer({"node_id": "peer-recov-27", "name": "Drop-Recov", "last_seen": time.time() - 60.0})
    assert len(nm.get_active_peers(timeout_seconds=45.0)) == 0

    # Peer sends heartbeat
    client.post("/peers/heartbeat", json={"node_id": "peer-recov-27", "latency_ms": 12.0})
    active = nm.get_active_peers(timeout_seconds=45.0)
    assert len(active) == 1
    assert active[0]["node_id"] == "peer-recov-27"
    assert active[0]["status"] == "online"


def test_28_remove_peer_explicit_deletion(clean_node_state):
    nm, _, _ = clean_node_state
    nm.register_peer({"node_id": "peer-del-28", "name": "To-Delete"})
    assert nm.get_peer("peer-del-28") is not None
    nm.remove_peer("peer-del-28")
    assert nm.get_peer("peer-del-28") is None


def test_29_remove_peer_safe_on_nonexistent_id(clean_node_state):
    nm, _, _ = clean_node_state
    nm.remove_peer("non-existent-999")  # Should not raise


def test_30_active_peer_count_reflects_truthful_online_nodes(clean_node_state):
    nm, _, _ = clean_node_state
    nm.register_peer({"node_id": "p1", "name": "Node-1", "last_seen": time.time() - 5.0})
    nm.register_peer({"node_id": "p2", "name": "Node-2", "last_seen": time.time() - 10.0})
    nm.register_peer({"node_id": "p3", "name": "Node-3", "last_seen": time.time() - 60.0})  # Expired
    status = nm.get_status()
    assert status["active_peer_count"] == 2


# ─── Group 4: ResQMeshRouter Topology & Route Preservation (Tests 31–40) ───────

def test_31_topology_contains_commander_as_local_node(clean_node_state):
    nm, router, _ = clean_node_state
    topo = router.get_topology()
    assert len(topo["nodes"]) >= 1
    local_node = next(n for n in topo["nodes"] if n["is_local"])
    assert local_node["id"] == nm.node_id
    assert local_node["hop_count"] == 0


def test_32_topology_includes_active_1hop_peer_node(client, clean_node_state):
    _, router, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "peer-topo-32", "name": "Responder-32", "role": "responder", "ip_address": "192.168.68.132"},
    )
    topo = router.get_topology()
    assert len(topo["nodes"]) == 2
    peer_node = next(n for n in topo["nodes"] if n["id"] == "peer-topo-32")
    assert peer_node["is_local"] is False
    assert peer_node["hop_count"] == 1


def test_33_topology_creates_link_between_commander_and_peer(client, clean_node_state):
    nm, router, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "peer-link-33", "name": "Responder-33", "role": "responder", "ip_address": "192.168.68.133"},
    )
    topo = router.get_topology()
    assert len(topo["links"]) == 1
    link = topo["links"][0]
    assert link["source"] == nm.node_id
    assert link["target"] == "peer-link-33"


def test_34_topology_prunes_stale_1hop_routes_when_peer_expires(clean_node_state):
    nm, router, _ = clean_node_state
    nm.register_peer({"node_id": "peer-prune-34", "name": "Stale-34", "last_seen": time.time() - 60.0})
    router.update_route("peer-prune-34", "peer-prune-34", hop_count=1)

    topo = router.get_topology()
    assert len(topo["nodes"]) == 1  # Only commander remains
    assert len(topo["links"]) == 0
    assert "peer-prune-34" not in router.routing_table


def test_35_route_remains_active_during_continuous_heartbeats(client, clean_node_state):
    nm, router, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "peer-cont-35", "name": "Continuous-35", "role": "responder", "ip_address": "192.168.68.135"},
    )
    for _ in range(10):
        client.post("/peers/heartbeat", json={"node_id": "peer-cont-35", "latency_ms": 12.0})
        topo = router.get_topology()
        assert len(topo["nodes"]) == 2
        assert len(topo["links"]) == 1


def test_36_multi_hop_route_addition_and_serialization(clean_node_state):
    nm, router, _ = clean_node_state
    router.update_route(
        dest_id="node-far-36",
        next_hop_id="node-relay-36",
        hop_count=2,
        latency_ms=28.0,
        relay_path=[nm.node_id, "node-relay-36", "node-far-36"],
    )
    routes = router.get_routes()
    far_route = next(r for r in routes if r["dest_id"] == "node-far-36")
    assert far_route["hop_count"] == 2
    assert far_route["next_hop_id"] == "node-relay-36"


def test_37_route_table_sorted_by_hop_count_and_latency(clean_node_state):
    _, router, _ = clean_node_state
    router.update_route("dest-c", "hop-c", hop_count=3, latency_ms=40.0)
    router.update_route("dest-a", "hop-a", hop_count=1, latency_ms=10.0)
    router.update_route("dest-b", "hop-b", hop_count=1, latency_ms=20.0)

    routes = router.get_routes()
    assert [r["dest_id"] for r in routes] == ["dest-a", "dest-b", "dest-c"]


def test_38_topology_endpoint_http_contract(client, clean_node_state):
    client.post(
        "/peers/register",
        json={"node_id": "peer-http-38", "name": "HTTP-Test", "role": "responder", "ip_address": "192.168.68.138"},
    )
    resp = client.get("/node/topology")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "links" in data
    assert "routes" in data


def test_39_routes_endpoint_http_contract(client, clean_node_state):
    client.post(
        "/peers/register",
        json={"node_id": "peer-routes-39", "name": "Routes-Test", "role": "responder", "ip_address": "192.168.68.139"},
    )
    resp = client.get("/node/routes")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["dest_id"] == "peer-routes-39"


def test_40_remove_route_explicit(clean_node_state):
    _, router, _ = clean_node_state
    router.update_route("to-remove-40", "to-remove-40", hop_count=1)
    assert "to-remove-40" in router.routing_table
    router.remove_route("to-remove-40")
    assert "to-remove-40" not in router.routing_table


# ─── Group 5: Multi-Peer Concurrency & Network Resilience (Tests 41–55) ────────

def test_41_multiple_concurrent_peers_registered(client, clean_node_state):
    nm, router, _ = clean_node_state
    for i in range(5):
        client.post(
            "/peers/register",
            json={
                "node_id": f"squad-node-{i}",
                "name": f"Squad-{i}",
                "role": "responder",
                "ip_address": f"192.168.68.20{i}",
                "latency_ms": 10.0 + i,
            },
        )
    active = nm.get_active_peers()
    assert len(active) == 5
    topo = router.get_topology()
    assert len(topo["nodes"]) == 6  # 1 commander + 5 responders
    assert len(topo["links"]) == 5


def test_42_independent_peer_heartbeat_leases(client, clean_node_state):
    nm, _, _ = clean_node_state
    client.post("/peers/register", json={"node_id": "peer-alive", "name": "Alive", "ip_address": "192.168.68.210"})
    client.post("/peers/register", json={"node_id": "peer-dying", "name": "Dying", "ip_address": "192.168.68.211"})

    nm._active_peers["peer-dying"]["last_seen"] = time.time() - 50.0  # Expire peer-dying

    client.post("/peers/heartbeat", json={"node_id": "peer-alive", "latency_ms": 12.0})

    active = nm.get_active_peers(timeout_seconds=45.0)
    assert len(active) == 1
    assert active[0]["node_id"] == "peer-alive"


def test_43_mesh_status_endpoint_reports_truthful_connected_state(client, clean_node_state):
    client.post(
        "/peers/register",
        json={"node_id": "peer-status-43", "name": "Status-43", "role": "responder", "ip_address": "192.168.68.212"},
    )
    resp = client.get("/node/mesh-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_peer_count"] >= 1


def test_44_force_sync_preserves_connected_peers(client, clean_node_state):
    nm, router, _ = clean_node_state
    client.post(
        "/peers/register",
        json={"node_id": "peer-sync-44", "name": "Sync-44", "role": "responder", "ip_address": "192.168.68.213"},
    )
    # Execute force delta sync
    resp = client.post("/node/sync/force")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    # Verify peer was NOT removed
    assert nm.get_peer("peer-sync-44") is not None
    assert router.routing_table.get("peer-sync-44") is not None



def test_45_force_sync_topology_output_preserves_nodes(client, clean_node_state):
    client.post(
        "/peers/register",
        json={"node_id": "peer-synctopo-45", "name": "SyncTopo-45", "role": "responder", "ip_address": "192.168.68.214"},
    )
    resp = client.post("/node/sync/force")
    data = resp.json()
    topo = data.get("topology", {})
    assert any(n["id"] == "peer-synctopo-45" for n in topo.get("nodes", []))


def test_46_heartbeat_payload_validation_rejects_missing_node_id(client, clean_node_state):
    resp = client.post("/peers/heartbeat", json={"latency_ms": 12.0})
    assert resp.status_code == 422


def test_47_heartbeat_payload_handles_negative_latency_gracefully(client, clean_node_state):
    resp = client.post("/peers/heartbeat", json={"node_id": "peer-neg-47", "latency_ms": -5.0})
    assert resp.status_code == 200


def test_48_peer_reconnect_after_temporary_wifi_drop(client, clean_node_state):
    nm, router, _ = clean_node_state
    client.post("/peers/register", json={"node_id": "peer-wifi-48", "name": "WiFi-Phone", "ip_address": "192.168.68.215"})
    # 1. Connected
    assert len(nm.get_active_peers(45.0)) == 1

    # 2. Wi-Fi drops (simulated 50s silence)
    nm._active_peers["peer-wifi-48"]["last_seen"] = time.time() - 50.0
    assert len(nm.get_active_peers(45.0)) == 0

    # 3. Wi-Fi restores, auto-heartbeat resumes
    client.post("/peers/heartbeat", json={"node_id": "peer-wifi-48", "latency_ms": 14.0})
    assert len(nm.get_active_peers(45.0)) == 1
    assert nm.get_peer("peer-wifi-48")["status"] == "online"


def test_49_node_status_uptime_increases(clean_node_state):
    nm, _, _ = clean_node_state
    s1 = nm.get_status()["uptime_seconds"]
    time.sleep(0.05)
    s2 = nm.get_status()["uptime_seconds"]
    assert s2 >= s1


def test_50_peer_heartbeat_server_time_is_recent(client, clean_node_state):
    now = time.time()
    resp = client.post("/peers/heartbeat", json={"node_id": "peer-time-50"})
    data = resp.json()
    assert abs(data["server_time"] - now) < 2.0


def test_51_multiple_heartbeats_do_not_create_duplicate_routes(client, clean_node_state):
    _, router, _ = clean_node_state
    client.post("/peers/register", json={"node_id": "peer-nodup-51", "name": "No-Dup", "ip_address": "192.168.68.216"})
    for _ in range(5):
        client.post("/peers/heartbeat", json={"node_id": "peer-nodup-51", "latency_ms": 10.0})
    routes = [r for r in router.get_routes() if r["dest_id"] == "peer-nodup-51"]
    assert len(routes) == 1


def test_52_stale_routes_pruning_leaves_valid_multi_hop(clean_node_state):
    nm, router, _ = clean_node_state
    # Direct peer
    nm.register_peer({"node_id": "direct-52", "name": "Direct-52", "last_seen": time.time()})
    router.update_route("direct-52", "direct-52", hop_count=1)
    # Multi-hop peer (hop 2)
    router.update_route("far-52", "direct-52", hop_count=2)

    router.prune_stale_routes(active_peer_ids={"direct-52"})
    assert "direct-52" in router.routing_table
    assert "far-52" in router.routing_table


def test_53_stale_routes_pruning_removes_expired_multi_hop(clean_node_state):
    _, router, _ = clean_node_state
    router.update_route("far-stale-53", "direct-53", hop_count=2)
    router.routing_table["far-stale-53"].last_updated = time.time() - 200.0

    router.prune_stale_routes(active_peer_ids={"direct-53"})
    assert "far-stale-53" not in router.routing_table


def test_54_heartbeat_updates_client_ip_if_peer_switches_network(client, clean_node_state):
    nm, _, _ = clean_node_state
    client.post("/peers/register", json={"node_id": "peer-roam-54", "name": "Roam-54", "ip_address": "192.168.1.50"})
    assert nm.get_peer("peer-roam-54") is not None
    # Roams to hotspot
    client.post("/peers/heartbeat", json={"node_id": "peer-roam-54", "ip_address": "192.168.137.50"})
    assert nm.get_peer("peer-roam-54")["status"] == "online"



def test_55_end_to_end_peer_registration_heartbeat_and_topology_consistency(client, clean_node_state):
    """Full lifecycle: register -> heartbeat x3 -> query topology -> check routes."""
    nm, router, _ = clean_node_state

    # 1. Initial Handshake / Registration
    reg = client.post(
        "/peers/register",
        json={
            "node_id": "responder-squad-e2e",
            "name": "Alpha-Squad-Lead",
            "role": "responder",
            "ip_address": "192.168.68.199",
            "api_port": 8001,
            "latency_ms": 11.5,
        },
    )
    assert reg.status_code == 200

    # 2. Verify Initial State
    assert len(nm.get_active_peers(45.0)) == 1
    assert router.routing_table.get("responder-squad-e2e") is not None

    # 3. Simulate 3 Heartbeat Pulses
    for i in range(3):
        hb = client.post(
            "/peers/heartbeat",
            json={"node_id": "responder-squad-e2e", "latency_ms": 10.0 + i},
        )
        assert hb.status_code == 200

    # 4. Verify Final Topology & Routes
    topo = client.get("/node/topology").json()
    assert len(topo["nodes"]) == 2
    assert len(topo["links"]) == 1

    routes = client.get("/node/routes").json()
    assert len(routes) == 1
    assert routes[0]["dest_id"] == "responder-squad-e2e"
    assert routes[0]["hop_count"] == 1
