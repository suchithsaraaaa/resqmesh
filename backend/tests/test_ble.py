import pytest
from backend.app.network.ble_manager import (
    ResQMeshBLEManager,
    RESQMESH_BLE_SERVICE_UUID,
    RESQMESH_BLE_TX_CHARACTERISTIC_UUID,
    RESQMESH_BLE_RX_CHARACTERISTIC_UUID,
)
from backend.app.network.protocol import Packet


def test_ble_uuids():
    assert RESQMESH_BLE_SERVICE_UUID == "0000fd00-0000-1000-8000-00805f9b34fb"
    assert RESQMESH_BLE_TX_CHARACTERISTIC_UUID == "0000fd01-0000-1000-8000-00805f9b34fb"
    assert RESQMESH_BLE_RX_CHARACTERISTIC_UUID == "0000fd02-0000-1000-8000-00805f9b34fb"


def test_ble_manager_advertising_and_scanning():
    ble_mgr = ResQMeshBLEManager(device_id="node-ble-01")
    assert ble_mgr.is_advertising is False
    assert ble_mgr.is_scanning is False

    assert ble_mgr.start_advertising() is True
    assert ble_mgr.is_advertising is True

    assert ble_mgr.start_scanning() is True
    assert ble_mgr.is_scanning is True

    ble_mgr.stop_advertising()
    ble_mgr.stop_scanning()

    assert ble_mgr.is_advertising is False
    assert ble_mgr.is_scanning is False


def test_ble_peer_discovery():
    ble_mgr = ResQMeshBLEManager(device_id="node-ble-01")
    peer = ble_mgr.handle_discovered_peer(
        device_id="node-ble-02", address="AA:BB:CC:DD:EE:FF", rssi=-55
    )

    assert peer.device_id == "node-ble-02"
    assert peer.address == "AA:BB:CC:DD:EE:FF"
    assert peer.rssi == -55
    assert "node-ble-02" in ble_mgr.discovered_peers


def test_ble_payload_chunking_and_reassembly():
    ble_mgr = ResQMeshBLEManager(device_id="node-ble-01", mtu_size=100)
    large_payload = "A" * 250

    chunks = ble_mgr.chunk_payload(large_payload)
    assert len(chunks) == 4  # 80 bytes max chunk size (100 - 20) -> 80*3 + 10 = 250
    assert ble_mgr.reassemble_chunks(chunks) == large_payload


def test_ble_incoming_packet_processing():
    ble_mgr = ResQMeshBLEManager(device_id="node-ble-01")
    received_packets = []

    def handler(pkt, sender):
        received_packets.append((pkt, sender))

    ble_mgr.register_packet_handler(handler)

    test_pkt = Packet(
        packet_id="pkt-ble-001",
        sender_id="node-ble-02",
        payload={"message": "Emergency broadcast test over BLE"},
    )
    raw_str = test_pkt.to_dict()

    import json

    raw_json = json.dumps(raw_str)

    processed = ble_mgr.process_incoming_raw_payload(raw_json, sender_id="node-ble-02")

    assert processed is not None
    assert processed.packet_id == "pkt-ble-001"
    assert len(received_packets) == 1
    assert received_packets[0][0].packet_id == "pkt-ble-001"
    assert received_packets[0][1] == "node-ble-02"
