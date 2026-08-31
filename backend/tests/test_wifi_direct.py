import pytest
import json
from backend.app.network.wifi_direct import ResQMeshWiFiDirectManager, WIFI_DIRECT_GO_IP
from backend.app.network.protocol import Packet


def test_wifi_direct_group_creation():
    wf_mgr = ResQMeshWiFiDirectManager(device_id="node-wfd-01")
    assert wf_mgr.is_group_owner is False
    assert wf_mgr.group_owner_ip is None

    assert wf_mgr.create_group() is True
    assert wf_mgr.is_group_owner is True
    assert wf_mgr.group_owner_ip == WIFI_DIRECT_GO_IP

    wf_mgr.remove_group()
    assert wf_mgr.is_group_owner is False
    assert wf_mgr.group_owner_ip is None


def test_wifi_direct_peer_discovery():
    wf_mgr = ResQMeshWiFiDirectManager(device_id="node-wfd-01")
    peer = wf_mgr.add_discovered_peer(
        device_address="48:5f:99:11:22:33", device_name="ResQMesh-Mobile-Node", is_go=False
    )

    assert peer.device_address == "48:5f:99:11:22:33"
    assert peer.device_name == "ResQMesh-Mobile-Node"
    assert peer.is_group_owner is False
    assert "48:5f:99:11:22:33" in wf_mgr.discovered_peers


def test_wifi_direct_incoming_payload_processing():
    wf_mgr = ResQMeshWiFiDirectManager(device_id="node-wfd-01")
    received_packets = []

    def handler(pkt, sender):
        received_packets.append((pkt, sender))

    wf_mgr.register_packet_handler(handler)

    pkt = Packet(
        packet_id="pkt-wfd-001",
        sender_id="node-wfd-02",
        payload={"event": "HIGH_RES_SATELLITE_IMAGE", "bytes_transferred": 1048576},
    )

    raw_json = json.dumps(pkt.to_dict())

    processed = wf_mgr.process_incoming_payload(raw_json, sender_ip="192.168.49.2")

    assert processed is not None
    assert processed.packet_id == "pkt-wfd-001"
    assert len(received_packets) == 1
    assert received_packets[0][0].packet_id == "pkt-wfd-001"
    assert received_packets[0][1] == "192.168.49.2"
