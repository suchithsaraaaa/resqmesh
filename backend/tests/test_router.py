import pytest
from backend.app.network.router import ResQMeshRouter, SeenPacketCache
from backend.app.network.protocol import Packet


def test_seen_packet_cache():
    cache = SeenPacketCache(expiry_seconds=0.1)
    assert cache.is_seen("pkt-1") is False

    cache.mark_seen("pkt-1")
    assert cache.is_seen("pkt-1") is True

    import time
    time.sleep(0.15)
    assert cache.is_seen("pkt-1") is False


def test_mesh_router_duplicate_suppression():
    router = ResQMeshRouter(local_device_id="node-b")

    pkt = Packet(
        packet_id="pkt-broadcast-001",
        sender_id="node-a",
        payload={"message": "Emergency alert", "ttl": 5, "hop_count": 0},
    )

    # First time seeing packet -> OK to process & forward
    res1 = router.process_incoming_packet(pkt, arrived_from_id="node-a")
    assert res1["should_process_locally"] is True
    assert res1["should_forward"] is True
    assert res1["reason"] == "OK_FORWARD"
    assert res1["updated_packet"].payload["ttl"] == 4
    assert res1["updated_packet"].payload["hop_count"] == 1

    # Second time seeing duplicate packet -> Suppress forwarding & processing
    res2 = router.process_incoming_packet(pkt, arrived_from_id="node-c")
    assert res2["should_process_locally"] is False
    assert res2["should_forward"] is False
    assert res2["reason"] == "DUPLICATE_PACKET"


def test_mesh_router_ttl_expiration():
    router = ResQMeshRouter(local_device_id="node-c")

    pkt = Packet(
        packet_id="pkt-ttl-1",
        sender_id="node-a",
        payload={"message": "Near end of life", "ttl": 1, "hop_count": 4},
    )

    res = router.process_incoming_packet(pkt, arrived_from_id="node-b")
    assert res["should_process_locally"] is True
    assert res["should_forward"] is False
    assert res["reason"] == "PROCESSED_LOCALLY_TTL_EXPIRED"


def test_mesh_router_unicast_routing():
    router = ResQMeshRouter(local_device_id="node-relay")

    # Packet targeted for node-final (not node-relay)
    pkt = Packet(
        packet_id="pkt-unicast-100",
        sender_id="node-commander",
        payload={"target_device_id": "node-final", "ttl": 5, "hop_count": 0},
    )

    res = router.process_incoming_packet(pkt, arrived_from_id="node-commander")
    assert res["should_process_locally"] is False
    assert res["should_forward"] is True
    assert res["updated_packet"].payload["ttl"] == 4
    assert "node-commander" in router.routing_table


def test_mesh_router_topology_and_routes():
    router = ResQMeshRouter(local_device_id="node-local")

    # Direct 1-hop neighbor
    router.update_route(
        dest_id="node-neighbor",
        next_hop_id="node-neighbor",
        hop_count=1,
        latency_ms=14.5,
        relay_path=["node-neighbor"],
    )

    # Multi-hop node reached via node-neighbor (2 hops)
    router.update_route(
        dest_id="node-remote",
        next_hop_id="node-neighbor",
        hop_count=2,
        latency_ms=48.2,
        relay_path=["node-neighbor", "node-remote"],
    )

    routes = router.get_routes()
    assert len(routes) == 2
    assert routes[0]["dest_id"] == "node-neighbor"
    assert routes[0]["hop_count"] == 1
    assert routes[0]["link_quality"] == "EXCELLENT"

    assert routes[1]["dest_id"] == "node-remote"
    assert routes[1]["hop_count"] == 2
    assert routes[1]["link_quality"] == "GOOD"

    topology = router.get_topology()
    assert topology["total_nodes"] >= 3
    assert len(topology["links"]) >= 2

