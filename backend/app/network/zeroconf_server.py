import socket
import logging
import threading
from typing import Dict, List, Optional
from zeroconf import Zeroconf, ServiceInfo, ServiceBrowser, ServiceListener

logger = logging.getLogger("ResQMesh.Zeroconf")

SERVICE_TYPE = "_resqmesh._tcp.local."


def get_local_ip() -> str:
    """Helper to detect local IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not actually connect externally, used to get interface IP
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class ResQMeshServiceListener(ServiceListener):
    """mDNS Service Listener to discover active ResQMesh peers on local LAN."""

    def __init__(self, local_device_id: str):
        self.local_device_id = local_device_id
        self.peers: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        with self._lock:
            if name in self.peers:
                logger.info(f"Peer disconnected from LAN mDNS: {name}")
                del self.peers[name]

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            self._update_peer(name, info)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            self._update_peer(name, info)

    def _update_peer(self, name: str, info: ServiceInfo) -> None:
        addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
        if not addresses:
            return

        ip_addr = addresses[0]
        port = info.port
        properties = {
            k.decode("utf-8") if isinstance(k, bytes) else k:
            v.decode("utf-8") if isinstance(v, bytes) else v
            for k, v in info.properties.items()
        }

        peer_device_id = properties.get("device_id", name)
        if peer_device_id == self.local_device_id:
            return  # Ignore self

        with self._lock:
            self.peers[name] = {
                "name": name,
                "device_id": peer_device_id,
                "ip": ip_addr,
                "port": port,
                "properties": properties,
            }
            logger.info(f"Discovered ResQMesh LAN peer: {peer_device_id} at {ip_addr}:{port}")

    def get_peers(self) -> List[dict]:
        with self._lock:
            return list(self.peers.values())


class ResQMeshZeroconfManager:
    """Manager to advertise local node via mDNS and browse for remote ResQMesh peers."""

    def __init__(self, device_id: str, port: int = 8001, node_role: str = "responder"):
        self.device_id = device_id
        self.port = port
        self.node_role = node_role
        self.zeroconf: Optional[Zeroconf] = None
        self.listener: Optional[ResQMeshServiceListener] = None
        self.browser: Optional[ServiceBrowser] = None
        self.service_info: Optional[ServiceInfo] = None
        self.is_running = False

    def start(self) -> None:
        if self.is_running:
            return

        self.zeroconf = Zeroconf()
        local_ip = get_local_ip()
        service_name = f"ResQMesh-{self.device_id[:8]}.{SERVICE_TYPE}"

        self.service_info = ServiceInfo(
            type_=SERVICE_TYPE,
            name=service_name,
            addresses=[socket.inet_aton(local_ip)],
            port=self.port,
            properties={
                "device_id": self.device_id,
                "role": self.node_role,
                "version": "1.0.0",
            },
            server=f"{self.device_id[:8]}.local.",
        )

        self.zeroconf.register_service(self.service_info)
        self.listener = ResQMeshServiceListener(local_device_id=self.device_id)
        self.browser = ServiceBrowser(self.zeroconf, SERVICE_TYPE, self.listener)
        self.is_running = True
        logger.info(f"Zeroconf mDNS service registered: {service_name} at {local_ip}:{self.port}")

    def stop(self) -> None:
        if not self.is_running or not self.zeroconf:
            return

        if self.service_info:
            self.zeroconf.unregister_service(self.service_info)
        self.zeroconf.close()
        self.is_running = False
        logger.info("Zeroconf mDNS service stopped.")

    def get_peers(self) -> List[dict]:
        if self.listener:
            return self.listener.get_peers()
        return []
