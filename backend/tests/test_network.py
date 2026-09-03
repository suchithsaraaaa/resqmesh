import asyncio
import pytest
from backend.app.network.zeroconf_server import get_local_ip, ResQMeshZeroconfManager
from backend.app.network.socket_server import ResQMeshSocketServer


def test_get_local_ip():
    ip = get_local_ip()
    assert isinstance(ip, str)
    assert len(ip.split(".")) == 4


def test_zeroconf_manager_lifecycle():
    import time
    manager = ResQMeshZeroconfManager(device_id="test-device-001", port=8005)
    manager.start()
    assert manager.is_running is True
    peers = manager.get_peers()
    assert isinstance(peers, list)
    time.sleep(0.1)
    manager.stop()
    assert manager.is_running is False


@pytest.mark.asyncio
async def test_socket_server_communication():
    server = ResQMeshSocketServer(host="127.0.0.1", port=8002)
    received_messages = []

    def handle_msg(payload, sender_ip):
        received_messages.append((payload, sender_ip))

    server.register_handler(handle_msg)
    await server.start()
    assert server.is_running is True

    test_payload = {
        "uuid": "test-uuid-1234",
        "eventType": "status_update",
        "deviceId": "node-alpha",
        "payload": {"status": "ACTIVE"}
    }

    success = await server.send_to_peer("127.0.0.1", 8002, test_payload)
    assert success is True

    # Allow brief event loop ticks for socket receive loop
    await asyncio.sleep(0.1)

    assert len(received_messages) == 1
    received_payload, sender_ip = received_messages[0]
    assert received_payload["uuid"] == "test-uuid-1234"
    assert received_payload["eventType"] == "status_update"
    assert sender_ip == "127.0.0.1"

    await server.stop()
    assert server.is_running is False
