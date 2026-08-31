import socket
import json
import time
import logging
import threading
from typing import Dict, List, Optional
from zeroconf import Zeroconf, ServiceInfo, ServiceBrowser, ServiceListener

try:
    from backend.app.services.node_manager import NodeManager
except ImportError:
    from app.services.node_manager import NodeManager

logger = logging.getLogger("ResQMesh.Discovery")

MDNS_SERVICE_TYPE = "_resqmesh._tcp.local."
UDP_BROADCAST_PORT = 52525
BEACON_INTERVAL = 5.0
PEER_TIMEOUT = 30.0


def get_local_ip() -> str:
    """Detect primary local IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class MDNSListener(ServiceListener):
    """mDNS Service Listener for discovering ResQMesh peer services."""

    def __init__(self, on_peer_discovered):
        self.on_peer_discovered = on_peer_discovered

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            self._handle_service(name, info)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            self._handle_service(name, info)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def _handle_service(self, name: str, info: ServiceInfo) -> None:
        addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
        if not addresses:
            return

        ip_addr = addresses[0]
        port = info.port
        props = {
            (k.decode("utf-8") if isinstance(k, bytes) else k): (
                v.decode("utf-8") if isinstance(v, bytes) else v
            )
            for k, v in info.properties.items()
        }

        peer_id = props.get("node_id", name)
        node_name = props.get("node_name", name.split(".")[0])
        role = props.get("role", "responder")

        self.on_peer_discovered(
            {
                "node_id": peer_id,
                "name": node_name,
                "role": role,
                "ip_address": ip_addr,
                "api_port": port,
                "discovery_method": "mDNS",
            }
        )


class DiscoveryEngine:
    """
    Dual-Mode Peer Discovery Engine:
    1. mDNS (Zeroconf) on _resqmesh._tcp.local.
    2. UDP Broadcast fallback on port 52525.
    """

    _instance: Optional["DiscoveryEngine"] = None

    def __init__(self, node_manager: Optional[NodeManager] = None):
        self.node_manager = node_manager or NodeManager.get_instance()
        self.is_running = False

        # mDNS components
        self.zeroconf: Optional[Zeroconf] = None
        self.browser: Optional[ServiceBrowser] = None
        self.service_info: Optional[ServiceInfo] = None

        # UDP broadcast components
        self._udp_sock: Optional[socket.socket] = None
        self._beacon_thread: Optional[threading.Thread] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @classmethod
    def get_instance(cls) -> "DiscoveryEngine":
        if cls._instance is None:
            cls._instance = DiscoveryEngine()
        return cls._instance

    def start(self) -> None:
        """Start both mDNS and UDP broadcast discovery."""
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()

        local_ip = get_local_ip()
        node_id = self.node_manager.node_id
        node_name = self.node_manager.node_name
        role = self.node_manager.role
        port = self.node_manager.api_port

        logger.info(f"Starting Discovery Engine for {node_name} ({node_id}) on {local_ip}:{port}")

        # 1. Start mDNS advertising and listener
        try:
            self.zeroconf = Zeroconf()
            service_name = f"{node_name}-{node_id[:6]}.{MDNS_SERVICE_TYPE}"
            desc = {
                "node_id": node_id,
                "node_name": node_name,
                "role": role,
                "version": "1.0",
            }
            self.service_info = ServiceInfo(
                MDNS_SERVICE_TYPE,
                service_name,
                addresses=[socket.inet_aton(local_ip)],
                port=port,
                properties=desc,
                server=f"{node_name}.local.",
            )
            self.zeroconf.register_service(self.service_info)
            self.browser = ServiceBrowser(
                self.zeroconf, MDNS_SERVICE_TYPE, MDNSListener(self._on_peer_discovered)
            )
            logger.info("mDNS Zeroconf service registered successfully.")
        except Exception as e:
            logger.warning(f"Failed to start mDNS Zeroconf: {e}")

        # 2. Start UDP Broadcast Listener
        try:
            self._udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._udp_sock.bind(("0.0.0.0", UDP_BROADCAST_PORT))
            self._udp_sock.settimeout(1.0)

            self._listener_thread = threading.Thread(
                target=self._listen_udp_broadcasts, daemon=True, name="UDP-Discovery-Listener"
            )
            self._listener_thread.start()
            logger.info(f"UDP Broadcast listener bound to 0.0.0.0:{UDP_BROADCAST_PORT}")
        except Exception as e:
            logger.warning(f"Failed to bind UDP broadcast listener: {e}")

        # 3. Start UDP Beacon Broadcaster
        self._beacon_thread = threading.Thread(
            target=self._send_udp_beacons, daemon=True, name="UDP-Beacon-Broadcaster"
        )
        self._beacon_thread.start()

    def _send_udp_beacons(self) -> None:
        """Periodically broadcast discovery beacons on UDP 52525."""
        tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tx_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        cycle_count = 0
        while not self._stop_event.is_set():
            cycle_count += 1
            try:
                beacon_payload = {
                    "type": "RESQMESH_BEACON",
                    "version": "1.0",
                    "node_id": self.node_manager.node_id,
                    "name": self.node_manager.node_name,
                    "role": self.node_manager.role,
                    "api_port": self.node_manager.api_port,
                    "timestamp": time.time(),
                }
                data = json.dumps(beacon_payload).encode("utf-8")
                # 1. Broadcast to generic LAN broadcast
                tx_sock.sendto(data, ("<broadcast>", UDP_BROADCAST_PORT))

                # 2. Unicast directly to all known peers (penetrates VM NAT / bridges / AP isolation)
                for peer in self.node_manager.get_active_peers():
                    peer_ip = peer.get("ip_address")
                    if peer_ip and not peer_ip.startswith("127."):
                        try:
                            tx_sock.sendto(data, (peer_ip, UDP_BROADCAST_PORT))
                        except Exception:
                            pass

                        # Every 2 cycles (~10s), send reciprocal HTTP ping
                        if cycle_count % 2 == 0:
                            peer_port = peer.get("api_port", 8000)
                            self._send_direct_http_ping(peer_ip, peer_port)

            except Exception as e:
                logger.debug(f"Error sending discovery beacon: {e}")

            self._stop_event.wait(BEACON_INTERVAL)

        tx_sock.close()

    def _send_direct_http_ping(self, peer_ip: str, peer_port: int) -> None:
        """Send direct reciprocal registration over HTTP in background."""
        def _do_ping():
            try:
                import urllib.request
                url = f"http://{peer_ip}:{peer_port}/peers/register"
                payload = {
                    "node_id": self.node_manager.node_id,
                    "name": self.node_manager.node_name,
                    "role": self.node_manager.role,
                    "ip_address": "", # will be inferred from incoming client socket IP on remote
                    "api_port": self.node_manager.api_port,
                    "public_key": self.node_manager.keypair.get_public_key_b64() if self.node_manager.keypair else None,
                    "latency_ms": 1.0,
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "ResQMesh-Discovery/1.0"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    if resp.status == 200:
                        logger.debug(f"Direct HTTP keepalive to {peer_ip}:{peer_port} succeeded.")
            except Exception as e:
                logger.debug(f"Direct HTTP keepalive to {peer_ip}:{peer_port} failed: {e}")

        threading.Thread(target=_do_ping, daemon=True, name=f"Ping-{peer_ip}").start()

    def _listen_udp_broadcasts(self) -> None:
        """Listen for incoming UDP discovery beacons."""
        while not self._stop_event.is_set() and self._udp_sock:
            try:
                data, addr = self._udp_sock.recvfrom(4096)
                packet = json.loads(data.decode("utf-8"))
                if packet.get("type") == "RESQMESH_BEACON":
                    peer_node_id = packet.get("node_id")
                    if peer_node_id and peer_node_id != self.node_manager.node_id:
                        sender_ip = addr[0]
                        # Compute estimated latency if timestamp is synchronized
                        now = time.time()
                        pkt_time = packet.get("timestamp", now)
                        latency_ms = max(1.0, round((now - pkt_time) * 1000, 1))

                        self._on_peer_discovered(
                            {
                                "node_id": peer_node_id,
                                "name": packet.get("name", "Unknown-Peer"),
                                "role": packet.get("role", "responder"),
                                "ip_address": sender_ip,
                                "api_port": packet.get("api_port", 8000),
                                "latency_ms": latency_ms,
                                "discovery_method": "UDP_Broadcast",
                            }
                        )
            except socket.timeout:
                continue
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.debug(f"UDP discovery receive error: {e}")

    def _on_peer_discovered(self, peer_info: dict) -> None:
        """Callback when a peer is discovered via mDNS or UDP."""
        peer_id = peer_info.get("node_id")
        if not peer_id or peer_id == self.node_manager.node_id:
            return

        self.node_manager.register_peer(peer_info)
        peer_ip = peer_info.get("ip_address")
        peer_port = peer_info.get("api_port", 8000)

        logger.info(
            f"Discovered peer [{peer_info.get('discovery_method')}]: {peer_info.get('name')} "
            f"({peer_id}) at {peer_ip}:{peer_port}"
        )

        # Send immediate reciprocal HTTP registration to peer so BOTH sides connect!
        if peer_ip and not peer_ip.startswith("127."):
            self._send_direct_http_ping(peer_ip, peer_port)

        # Trigger immediate outbox flush to deliver any delay-tolerant messages
        try:
            from backend.app.sync.outbox_worker import StoreAndForwardWorker
            StoreAndForwardWorker.get_instance().trigger_flush()
        except Exception:
            try:
                from app.sync.outbox_worker import StoreAndForwardWorker
                StoreAndForwardWorker.get_instance().trigger_flush()
            except Exception:
                pass

    def stop(self) -> None:
        """Stop discovery services cleanly."""
        if not self.is_running:
            return
        self.is_running = False
        self._stop_event.set()

        # Shutdown mDNS
        if self.zeroconf and self.service_info:
            try:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
            except Exception as e:
                logger.debug(f"Error closing zeroconf: {e}")

        # Shutdown UDP socket
        if self._udp_sock:
            try:
                self._udp_sock.close()
            except Exception:
                pass

        logger.info("Discovery Engine stopped.")
