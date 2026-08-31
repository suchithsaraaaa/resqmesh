import pytest
from tests.simulation.mesh_simulator import MeshNetworkSimulator


def test_linear_multihop_mesh_broadcast():
    """
    Test linear 4-node topology:
    Node-A <---> Node-B <---> Node-C <---> Node-D
    A sends report, verifies it reaches Node-D across 3 hops.
    """
    sim = MeshNetworkSimulator()
    sim.add_node("node-a")
    sim.add_node("node-b")
    sim.add_node("node-c")
    sim.add_node("node-d")

    sim.connect("node-a", "node-b")
    sim.connect("node-b", "node-c")
    sim.connect("node-c", "node-d")

    # Node A creates report
    pkt = sim.nodes["node-a"].create_report(
        report_id="rep-alpha-001",
        category="fire",
        description="Transformer fire near north bridge",
        lat=12.9716,
        lon=77.5946,
    )
    sim.broadcast_from_node("node-a", pkt)

    # Run simulation to quiescence
    sim.run_until_quiescence(max_ticks=10)

    # Verify all 4 nodes have the report in their database
    for node_id in ["node-a", "node-b", "node-c", "node-d"]:
        assert "rep-alpha-001" in sim.nodes[node_id].local_database
        rep = sim.nodes[node_id].local_database["rep-alpha-001"]
        assert rep["category"] == "fire"


def test_mesh_network_partition_and_reconnection():
    """
    Test network partition:
    Subnet 1: Node-A <-> Node-B
    Subnet 2: Node-C <-> Node-D
    1. During partition, Node-A creates Report-1 (reaches B, but not C or D).
    2. Node-D creates Report-2 (reaches C, but not A or B).
    3. Reconnect B <-> C (bridge link restored).
    4. Verify both subnets synchronize and converge on all reports.
    """
    sim = MeshNetworkSimulator()
    sim.add_node("node-a")
    sim.add_node("node-b")
    sim.add_node("node-c")
    sim.add_node("node-d")

    # Connect partitioned subnets
    sim.connect("node-a", "node-b")
    sim.connect("node-c", "node-d")

    # Subnet 1 creates Report 1
    pkt1 = sim.nodes["node-a"].create_report(
        report_id="rep-1", category="flood", description="Water rising", lat=12.97, lon=77.59
    )
    sim.broadcast_from_node("node-a", pkt1)

    # Subnet 2 creates Report 2
    pkt2 = sim.nodes["node-d"].create_report(
        report_id="rep-2", category="medical", description="Medical triage needed", lat=12.98, lon=77.60
    )
    sim.broadcast_from_node("node-d", pkt2)

    sim.run_until_quiescence(max_ticks=5)

    # Verify Subnet 1 has rep-1 only, Subnet 2 has rep-2 only
    assert "rep-1" in sim.nodes["node-b"].local_database
    assert "rep-2" not in sim.nodes["node-b"].local_database
    assert "rep-2" in sim.nodes["node-c"].local_database
    assert "rep-1" not in sim.nodes["node-c"].local_database

    # Restore bridge connection B <-> C
    sim.connect("node-b", "node-c")

    # Trigger bidirectional delta sync across newly restored link
    sim.trigger_delta_sync("node-b")
    sim.trigger_delta_sync("node-c")

    sim.run_until_quiescence(max_ticks=10)

    # Verify complete convergence across all nodes
    for node_id in ["node-a", "node-b", "node-c", "node-d"]:
        assert "rep-1" in sim.nodes[node_id].local_database
        assert "rep-2" in sim.nodes[node_id].local_database


def test_mesh_dense_grid_duplicate_suppression():
    """
    Test dense triangular/mesh grid:
    Node-A connects to Node-B, Node-C, Node-D.
    Node-B connects to Node-C and Node-D.
    Verify packets do not loop infinitely and duplicate suppression halts packet storms.
    """
    sim = MeshNetworkSimulator()
    sim.add_node("node-1")
    sim.add_node("node-2")
    sim.add_node("node-3")
    sim.add_node("node-4")

    # Complete graph K4
    nodes = ["node-1", "node-2", "node-3", "node-4"]
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            sim.connect(nodes[i], nodes[j])

    pkt = sim.nodes["node-1"].create_report(
        report_id="rep-grid-01", category="structural", description="Wall collapse", lat=12.9, lon=77.5
    )
    sim.broadcast_from_node("node-1", pkt)

    total_transmissions = sim.run_until_quiescence(max_ticks=10)

    # Transmissions should be strictly bounded and terminate within a few ticks
    assert total_transmissions < 25
    for node_id in nodes:
        assert "rep-grid-01" in sim.nodes[node_id].local_database
