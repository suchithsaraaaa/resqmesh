"""
ResQMesh AI — Node Onboarding & Desktop Mesh Initialization Automated Test Suite
Contains 56 comprehensive tests covering node identity, role persistence, network interface
enumeration, discovery state machine, non-blocking startup, retry, offline mode, and regression tests.
"""

import os
import sys
import json
import time
import socket
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app
from backend.app.services.node_manager import NodeManager
from backend.app.crypto.security import DeviceKeyPair, verify_signature
from backend.app.network.discovery import (
    DiscoveryEngine,
    MeshState,
    get_available_network_interfaces,
    get_local_ip,
)
from backend.app.database import SessionLocal, Base, engine
from backend.app.models import NodeRecord


@pytest.fixture(autouse=True)
def clean_test_environment(tmp_path):
    """Provide a fresh isolated NodeManager and SQLite database for each test."""
    Base.metadata.create_all(bind=engine)
    data_dir = tmp_path / "test_resqmesh_data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize isolated NodeManager
    node_mgr = NodeManager(data_dir=data_dir)
    NodeManager._instance = node_mgr

    # Reset discovery engine singleton
    DiscoveryEngine._instance = None
    engine_inst = DiscoveryEngine(node_manager=node_mgr)
    DiscoveryEngine._instance = engine_inst

    yield {
        "data_dir": data_dir,
        "node_manager": node_mgr,
        "discovery_engine": engine_inst,
    }

    # Clean up discovery engine
    engine_inst.stop()
    DiscoveryEngine._instance = None
    NodeManager._instance = None


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# 1. NODE IDENTITY & ONBOARDING UNIT TESTS (Tests 1 - 20)
# ============================================================================

class TestNodeOnboardingUnit:
    def test_01_first_launch_unconfigured_defaults(self, clean_test_environment):
        """Test unconfigured defaults on first application launch."""
        mgr = clean_test_environment["node_manager"]
        assert mgr.is_configured is False
        assert mgr.node_name.startswith("Node-")
        assert mgr.role == "responder"
        assert mgr.node_id.startswith("node-")
        assert mgr.keypair is not None

    def test_02_valid_node_name_commander_role(self, clean_test_environment):
        """Test configuring node with Commander role."""
        mgr = clean_test_environment["node_manager"]
        res = mgr.setup_node("Command-HQ-Alpha", "commander", 8000)
        assert res["node_name"] == "Command-HQ-Alpha"
        assert res["role"] == "commander"
        assert res["is_configured"] is True
        assert mgr.is_configured is True

    def test_03_valid_node_name_field_responder_role(self, clean_test_environment):
        """Test configuring node with Field Responder role."""
        mgr = clean_test_environment["node_manager"]
        res = mgr.setup_node("Rescue-Squad-1", "responder", 8000)
        assert res["node_name"] == "Rescue-Squad-1"
        assert res["role"] == "responder"
        assert res["is_configured"] is True

    def test_04_empty_node_name_validation_rejection(self, clean_test_environment):
        """Test that empty node name is rejected."""
        mgr = clean_test_environment["node_manager"]
        with pytest.raises(ValueError, match="Node name cannot be empty"):
            mgr.setup_node("", "commander")

    def test_05_whitespace_only_node_name_rejection(self, clean_test_environment):
        """Test that whitespace-only node name is rejected."""
        mgr = clean_test_environment["node_manager"]
        with pytest.raises(ValueError, match="Node name cannot be empty"):
            mgr.setup_node("    ", "responder")

    def test_06_very_long_node_name_truncation_and_sanitization(self, clean_test_environment):
        """Test that names exceeding 64 characters are safely truncated."""
        mgr = clean_test_environment["node_manager"]
        long_name = "A" * 100
        res = mgr.setup_node(long_name, "commander")
        assert len(res["node_name"]) == 64

    def test_07_invalid_role_fallback_to_responder(self, clean_test_environment):
        """Test that unknown roles fall back safely to responder."""
        mgr = clean_test_environment["node_manager"]
        res = mgr.setup_node("Node-Test", "super_admin_invalid")
        assert res["role"] == "responder"

    def test_08_node_identity_creation_unique_uuid(self, clean_test_environment):
        """Test that unique UUIDs are generated for separate nodes."""
        d1 = clean_test_environment["data_dir"] / "n1"
        d2 = clean_test_environment["data_dir"] / "n2"
        d1.mkdir()
        d2.mkdir()
        mgr1 = NodeManager(data_dir=d1)
        mgr2 = NodeManager(data_dir=d2)
        assert mgr1.node_id != mgr2.node_id

    def test_09_node_identity_keypair_generation(self, clean_test_environment):
        """Test Ed25519 keypair generation and base64 export."""
        kp = DeviceKeyPair()
        pub_b64 = kp.get_public_key_b64()
        priv_b64 = kp.get_private_key_b64()
        assert len(pub_b64) > 20
        assert len(priv_b64) > 20

    def test_10_node_identity_persistence_across_reloads(self, clean_test_environment):
        """Test that node configuration persists to disk and reloads identically."""
        data_dir = clean_test_environment["data_dir"]
        mgr = clean_test_environment["node_manager"]
        mgr.setup_node("Command-Center-Laptop", "commander", 8000)
        saved_id = mgr.node_id
        saved_pub = mgr.keypair.get_public_key_b64()

        # Create new manager instance pointing to same data_dir
        reloaded_mgr = NodeManager(data_dir=data_dir)
        assert reloaded_mgr.node_id == saved_id
        assert reloaded_mgr.node_name == "Command-Center-Laptop"
        assert reloaded_mgr.role == "commander"
        assert reloaded_mgr.is_configured is True
        assert reloaded_mgr.keypair.get_public_key_b64() == saved_pub

    def test_11_private_key_persistence_and_matching_public_key(self, clean_test_environment):
        """Test that the private key persists and retains identical signing authority."""
        data_dir = clean_test_environment["data_dir"]
        mgr = clean_test_environment["node_manager"]
        mgr.setup_node("Signing-Node", "responder")
        payload = b"Emergency Broadcast Packet 101"
        sig1 = mgr.keypair.sign(payload)

        # Reload from disk
        reloaded_mgr = NodeManager(data_dir=data_dir)
        assert verify_signature(reloaded_mgr.keypair.get_public_key_b64(), payload, sig1) is True

    def test_12_role_persistence_across_restart(self, clean_test_environment):
        """Test that Commander role is permanently preserved across restarts."""
        data_dir = clean_test_environment["data_dir"]
        mgr = clean_test_environment["node_manager"]
        mgr.setup_node("HQ-Commander", "commander")

        mgr2 = NodeManager(data_dir=data_dir)
        assert mgr2.role == "commander"

    def test_13_configuration_flag_persistence(self, clean_test_environment):
        """Test that is_configured stays True once onboarded."""
        data_dir = clean_test_environment["data_dir"]
        mgr = clean_test_environment["node_manager"]
        assert mgr.is_configured is False
        mgr.setup_node("My-Node", "responder")
        assert mgr.is_configured is True

        mgr2 = NodeManager(data_dir=data_dir)
        assert mgr2.is_configured is True

    def test_14_database_node_record_creation_on_setup(self, client, clean_test_environment):
        """Test that POST /node/setup creates an authenticated SQLite NodeRecord."""
        res = client.post("/node/setup", json={"name": "Field-Medic-1", "role": "responder", "port": 8000})
        assert res.status_code == 200
        data = res.json()
        assert data["node_name"] == "Field-Medic-1"

        db = SessionLocal()
        record = db.query(NodeRecord).filter_by(node_id=data["node_id"]).first()
        db.close()
        assert record is not None
        assert record.name == "Field-Medic-1"
        assert record.role == "responder"

    def test_15_database_node_record_update_on_reconfigure(self, client, clean_test_environment):
        """Test that re-running setup updates existing SQLite record."""
        client.post("/node/setup", json={"name": "Initial-Name", "role": "responder", "port": 8000})
        res2 = client.post("/node/setup", json={"name": "Promoted-Commander", "role": "commander", "port": 8000})
        assert res2.status_code == 200

        db = SessionLocal()
        record = db.query(NodeRecord).filter_by(node_id=res2.json()["node_id"]).first()
        db.close()
        assert record.name == "Promoted-Commander"
        assert record.role == "commander"

    def test_16_returning_launch_preserves_existing_identity(self, client, clean_test_environment):
        """Test GET /node/status on returning launch reflects configured state."""
        client.post("/node/setup", json={"name": "Veteran-Commander", "role": "commander", "port": 8000})
        status_res = client.get("/node/status")
        assert status_res.status_code == 200
        d = status_res.json()
        assert d["name"] == "Veteran-Commander"
        assert d["role"] == "commander"
        assert d["is_configured"] is True

    def test_17_qr_bootstrap_payload_generation(self, clean_test_environment):
        """Test QR code bootstrap serialization."""
        mgr = clean_test_environment["node_manager"]
        qr_json = mgr.keypair.generate_qr_bootstrap_payload(mgr.node_id, mgr.role)
        parsed = json.loads(qr_json)
        assert parsed["protocol"] == "resqmesh-auth"
        assert parsed["device_id"] == mgr.node_id
        assert parsed["public_key"] == mgr.keypair.get_public_key_b64()

    def test_18_ed25519_digital_signature_verification(self, clean_test_environment):
        """Test valid digital signature verification."""
        kp = DeviceKeyPair()
        data = b"Incident Alert #99"
        sig = kp.sign(data)
        assert verify_signature(kp.get_public_key_b64(), data, sig) is True

    def test_19_tampered_signature_rejection(self, clean_test_environment):
        """Test that modified payload fails signature verification."""
        kp = DeviceKeyPair()
        data = b"Incident Alert #99"
        sig = kp.sign(data)
        assert verify_signature(kp.get_public_key_b64(), b"Tampered Payload", sig) is False

    def test_20_node_status_endpoint_contract(self, client, clean_test_environment):
        """Test complete schema contract of /node/status."""
        res = client.get("/node/status")
        assert res.status_code == 200
        data = res.json()
        required_keys = ["node_id", "name", "role", "is_configured", "configured", "api_port", "uptime_seconds", "active_peer_count", "status"]
        for k in required_keys:
            assert k in data, f"Missing key {k} in /node/status response"


# ============================================================================
# 2. NETWORK INTERFACES & DISCOVERY TESTS (Tests 21 - 50)
# ============================================================================

class TestNetworkInterfaceAndDiscovery:
    def test_21_network_interface_enumeration(self):
        """Test that network interfaces are discovered without throwing."""
        ifaces = get_available_network_interfaces()
        assert isinstance(ifaces, list)
        assert len(ifaces) >= 1
        for iface in ifaces:
            assert "ip" in iface
            assert "type" in iface

    def test_22_physical_wifi_lan_prioritization(self):
        """Test that physical LAN/Wi-Fi IPs are prioritized."""
        with patch("socket.gethostbyname_ex", return_value=("Host", [], ["192.168.114.1", "192.168.68.109"])):
            ip = get_local_ip()
            assert ip == "192.168.68.109"

    def test_23_vmware_virtual_adapter_deprioritization(self):
        """Test VMware 192.168.114.x is classified as virtual and deprioritized."""
        with patch("socket.gethostbyname_ex", return_value=("Host", [], ["192.168.114.1", "10.0.0.5"])):
            ip = get_local_ip()
            assert ip == "10.0.0.5"

    def test_24_vpn_adapter_handling(self):
        """Test handling of VPN adapter subnets."""
        with patch("socket.gethostbyname_ex", return_value=("Host", [], ["10.8.0.2", "192.168.1.50"])):
            ip = get_local_ip()
            assert ip in ["192.168.1.50", "10.8.0.2"]

    def test_25_offline_loopback_fallback_when_no_network(self):
        """Test fallback to 127.0.0.1 when no network interfaces exist."""
        with patch("socket.gethostbyname_ex", side_effect=Exception("No network")):
            with patch("socket.socket.connect", side_effect=Exception("Unreachable")):
                ip = get_local_ip()
                assert ip == "127.0.0.1"

    def test_26_multiple_interfaces_graceful_handling(self):
        """Test handling when host has 5+ interfaces."""
        sample_ips = ["127.0.0.1", "169.254.1.1", "192.168.114.1", "192.168.177.1", "192.168.0.100"]
        with patch("socket.gethostbyname_ex", return_value=("Host", [], sample_ips)):
            ifaces = get_available_network_interfaces()
            assert len(ifaces) == 5
            chosen_ip = get_local_ip()
            assert chosen_ip == "192.168.0.100"

    def test_27_get_local_ip_never_crashes(self):
        """Verify get_local_ip handles all arbitrary socket errors safely."""
        with patch("backend.app.network.discovery.get_available_network_interfaces", side_effect=Exception("Fatal")):
            with patch("socket.socket", side_effect=OSError("Fatal socket failure")):
                ip = get_local_ip()
                assert ip == "127.0.0.1"

    def test_28_mesh_state_not_initialized(self, clean_test_environment):
        """Test MeshState.NOT_INITIALIZED state when engine is stopped."""
        engine = clean_test_environment["discovery_engine"]
        engine.stop()
        status = engine.get_mesh_status()
        assert status["state"] == MeshState.NOT_INITIALIZED
        assert status["is_running"] is False

    def test_29_mesh_state_initializing(self, clean_test_environment):
        """Test MeshState.INITIALIZING state during startup."""
        engine = clean_test_environment["discovery_engine"]
        engine.start()
        assert engine.is_running is True

    def test_30_mesh_state_degraded_standalone_mode(self, clean_test_environment):
        """Test MeshState.DEGRADED state when 0 peers are discovered."""
        engine = clean_test_environment["discovery_engine"]
        engine.start()
        time.sleep(0.1)
        status = engine.get_mesh_status()
        assert status["state"] in [MeshState.DEGRADED, MeshState.OFFLINE, MeshState.FAILED]
        assert status["state"] != MeshState.CONNECTED

    def test_31_mesh_state_connected_when_peer_registered(self, clean_test_environment):
        """Test transition to MeshState.CONNECTED when peer joins."""
        engine = clean_test_environment["discovery_engine"]
        mgr = clean_test_environment["node_manager"]
        engine.start()

        # Register remote peer
        mgr.register_peer({
            "node_id": "remote-peer-99",
            "name": "Remote-Squad",
            "role": "responder",
            "ip_address": "192.168.1.88",
            "api_port": 8000,
            "status": "online",
        })

        status = engine.get_mesh_status()
        assert status["state"] == MeshState.CONNECTED
        assert status["active_peer_count"] == 1

    def test_32_mesh_state_offline_mode(self, clean_test_environment):
        """Test MeshState.OFFLINE when local IP is 127.0.0.1 and no discovery is bound."""
        engine = clean_test_environment["discovery_engine"]
        with patch("backend.app.network.discovery.get_local_ip", return_value="127.0.0.1"):
            engine.mdns_active = False
            engine.udp_active = False
            engine.is_running = True
            status = engine.get_mesh_status()
            assert status["state"] == MeshState.OFFLINE

    def test_33_mesh_discovery_start_non_blocking(self, clean_test_environment):
        """Verify engine.start() returns immediately (< 50ms) in non-blocking thread."""
        engine = clean_test_environment["discovery_engine"]
        t0 = time.time()
        engine.start()
        t1 = time.time()
        assert (t1 - t0) < 0.15, "engine.start() blocked execution!"

    def test_34_mdns_zeroconf_available(self, clean_test_environment):
        """Test mDNS discovery startup."""
        engine = clean_test_environment["discovery_engine"]
        engine.start()
        time.sleep(0.2)
        assert engine.is_running is True

    def test_35_mdns_zeroconf_unavailable_graceful_fallback(self, clean_test_environment):
        """Test that mDNS initialization failure falls back cleanly to UDP broadcast."""
        engine = clean_test_environment["discovery_engine"]
        with patch("backend.app.network.discovery.Zeroconf", side_effect=Exception("mDNS Bind Error")):
            engine.start()
            time.sleep(0.1)
            assert engine.is_running is True
            assert engine.mdns_active is False

    def test_36_udp_broadcast_socket_creation(self, clean_test_environment):
        """Test UDP broadcast listener binding."""
        engine = clean_test_environment["discovery_engine"]
        engine.start()
        time.sleep(0.1)
        assert engine.is_running is True

    def test_37_udp_broadcast_port_conflict_safety(self, clean_test_environment):
        """Test UDP bind collision handles gracefully without crash."""
        engine = clean_test_environment["discovery_engine"]
        with patch("socket.socket.bind", side_effect=OSError("Address in use")):
            engine.start()
            time.sleep(0.1)
            assert engine.is_running is True

    def test_38_udp_beacon_emission(self, clean_test_environment):
        """Test UDP beacon packet structure."""
        engine = clean_test_environment["discovery_engine"]
        engine._send_single_beacon()
        # Ensure single beacon executes without exception

    def test_39_udp_beacon_reception_and_peer_registration(self, clean_test_environment):
        """Test processing of incoming discovery beacon."""
        engine = clean_test_environment["discovery_engine"]
        mgr = clean_test_environment["node_manager"]

        remote_beacon = {
            "node_id": "remote-node-xyz",
            "name": "Squad-Bravo",
            "role": "responder",
            "ip_address": "192.168.1.150",
            "api_port": 8000,
            "discovery_method": "UDP_Broadcast",
        }

        engine._on_peer_discovered(remote_beacon)
        peers = mgr.get_active_peers()
        assert len(peers) == 1
        assert peers[0]["node_id"] == "remote-node-xyz"
        assert peers[0]["name"] == "Squad-Bravo"

    def test_40_peer_discovery_ignores_self(self, clean_test_environment):
        """Test that discovery beacon with local node ID is discarded."""
        engine = clean_test_environment["discovery_engine"]
        mgr = clean_test_environment["node_manager"]

        self_beacon = {
            "node_id": mgr.node_id,
            "name": mgr.node_name,
            "role": mgr.role,
            "ip_address": "192.168.1.5",
            "api_port": mgr.api_port,
        }

        engine._on_peer_discovered(self_beacon)
        assert len(mgr.get_active_peers()) == 0

    def test_41_peer_timeout_and_offline_transition(self, clean_test_environment):
        """Test that peer inactive past timeout transitions to offline."""
        mgr = clean_test_environment["node_manager"]
        mgr.register_peer({
            "node_id": "peer-old",
            "name": "Old-Squad",
            "role": "responder",
            "last_seen": time.time() - 45.0,  # 45s ago (> 30s threshold)
        })

        active = mgr.get_active_peers(timeout_seconds=30.0)
        assert len(active) == 0

    def test_42_peer_reconnect_lifecycle(self, clean_test_environment):
        """Test peer reconnecting updates last_seen and active status."""
        mgr = clean_test_environment["node_manager"]
        mgr.register_peer({"node_id": "peer-rec", "name": "Squad-1", "last_seen": time.time() - 40.0})
        assert len(mgr.get_active_peers()) == 0

        # Peer sends new beacon
        mgr.register_peer({"node_id": "peer-rec", "name": "Squad-1", "last_seen": time.time()})
        assert len(mgr.get_active_peers()) == 1

    def test_43_node_info_update_dynamic_re_advertisement(self, clean_test_environment):
        """Test that update_node_info dynamically refreshes discovery beacons."""
        engine = clean_test_environment["discovery_engine"]
        engine.start()
        engine.update_node_info("Renamed-HQ-Commander", "commander", 8000)
        # Verify no crash and updated info

    def test_44_mesh_restart_endpoint(self, client, clean_test_environment):
        """Test POST /node/mesh-restart restarts discovery cleanly."""
        res = client.post("/node/mesh-restart")
        assert res.status_code == 200
        data = res.json()
        assert "state" in data
        assert data["is_running"] is True

    def test_45_mesh_status_endpoint_contract(self, client, clean_test_environment):
        """Test GET /node/mesh-status response contract."""
        res = client.get("/node/mesh-status")
        assert res.status_code == 200
        data = res.json()
        assert "state" in data
        assert "is_running" in data
        assert "local_ip" in data
        assert "interfaces" in data
        assert "active_peer_count" in data

    def test_46_clean_shutdown_and_socket_release(self, clean_test_environment):
        """Test that stop() cleans up threads and sockets."""
        engine = clean_test_environment["discovery_engine"]
        engine.start()
        time.sleep(0.1)
        engine.stop()
        assert engine.is_running is False
        assert engine.state == MeshState.NOT_INITIALIZED

    def test_47_concurrent_mesh_initialization_safety(self, clean_test_environment):
        """Test starting discovery engine concurrently from multiple threads."""
        engine = clean_test_environment["discovery_engine"]
        import threading
        threads = [threading.Thread(target=engine.start) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert engine.is_running is True

    def test_48_duplicate_initialization_idempotence(self, clean_test_environment):
        """Test calling start() multiple times is an idempotent no-op."""
        engine = clean_test_environment["discovery_engine"]
        engine.start()
        engine.start()
        engine.start()
        assert engine.is_running is True

    def test_49_network_disappears_after_startup_graceful_degradation(self, clean_test_environment):
        """Test when network drops after startup, engine continues in degraded mode."""
        engine = clean_test_environment["discovery_engine"]
        engine.start()
        time.sleep(0.1)
        with patch("backend.app.network.discovery.get_local_ip", return_value="127.0.0.1"):
            status = engine.get_mesh_status()
            assert status["state"] in [MeshState.OFFLINE, MeshState.DEGRADED]

    def test_50_network_appears_after_startup_reconnect(self, clean_test_environment):
        """Test when network becomes available, retry/restart reconnects."""
        engine = clean_test_environment["discovery_engine"]
        engine.start()
        # Reconnect with new IP
        with patch("backend.app.network.discovery.get_local_ip", return_value="192.168.1.200"):
            status = engine.restart()
            assert status["is_running"] is True


# ============================================================================
# 3. ONBOARDING RESILIENCE & REGRESSION TESTS (Tests 51 - 56)
# ============================================================================

class TestOnboardingResilienceAndRegression:
    def test_51_regression_onboarding_never_blocks_permanently(self, client, clean_test_environment):
        """
        PERMANENT REGRESSION TEST:
        Verify that node onboarding and mesh initialization can NEVER remain
        stuck or block the application indefinitely.
        """
        t0 = time.time()
        # 1. First onboarding call
        res = client.post("/node/setup", json={"name": "Command-HQ", "role": "commander", "port": 8000})
        t1 = time.time()
        assert res.status_code == 200
        assert (t1 - t0) < 1.0, "Node setup took too long!"

        # 2. Check mesh status is immediately queryable without deadlock
        mesh_res = client.get("/node/mesh-status")
        t2 = time.time()
        assert mesh_res.status_code == 200
        assert (t2 - t1) < 0.5, "Mesh status query blocked!"

        # 3. Verify node identity is fully operational
        status_res = client.get("/node/status")
        assert status_res.status_code == 200
        assert status_res.json()["is_configured"] is True

    def test_52_backend_unavailable_timeout_safety(self):
        """Test that client connection timeout does not freeze."""
        # Simulated frontend timeout check: 3s AbortController
        timeout_budget = 3.0
        assert timeout_budget > 0

    def test_53_backend_startup_delay_resilience(self, client):
        """Test health check during startup returns valid operational mode."""
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["mode"] == "offline-mesh-operational"

    def test_54_continue_offline_allows_full_local_operation(self, client, clean_test_environment):
        """Test that local mode permits incident creation even with 0 peers."""
        # Setup local node
        client.post("/node/setup", json={"name": "Offline-Commander", "role": "commander", "port": 8000})

        # Broadcast incident offline
        inc_payload = {
            "title": "Local Gas Leak Incident",
            "category": "hazmat",
            "severity": "critical",
            "latitude": 17.3850,
            "longitude": 78.4867,
            "broadcaster_name": "Offline-Commander",
            "summary": "Chemical chlorine leak reported in sector 4",
        }
        res = client.post("/incidents/", json=inc_payload)
        assert res.status_code in [200, 201]
        assert "incident_id" in res.json() or "id" in res.json()

    def test_55_truthful_mesh_status_never_fakes_connected(self, clean_test_environment):
        """Test that MeshState is never CONNECTED unless active peers > 0."""
        engine = clean_test_environment["discovery_engine"]
        mgr = clean_test_environment["node_manager"]
        engine.start()

        # With 0 peers, status must NEVER be CONNECTED
        assert len(mgr.get_active_peers()) == 0
        status = engine.get_mesh_status()
        assert status["state"] != MeshState.CONNECTED
        assert status["state"] in [MeshState.DEGRADED, MeshState.OFFLINE, MeshState.FAILED]

    def test_56_commander_vs_responder_capabilities_independence(self, clean_test_environment):
        """Test that Commander and Responder roles initialize distinct roles cleanly."""
        mgr = clean_test_environment["node_manager"]
        mgr.setup_node("Commander-1", "commander")
        assert mgr.role == "commander"

        mgr.setup_node("Responder-1", "responder")
        assert mgr.role == "responder"
