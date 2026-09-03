import socket
import json
import time
import logging
import threading
from typing import Dict, List, Optional, Tuple
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

# Explicit Mesh Operational States
class MeshState:
    NOT_INITIALIZED = "NOT_INITIALIZED"
    INITIALIZING = "INITIALIZING"
    CONNECTED = "CONNECTED"          # At least 1 active peer discovered and verified
    DEGRADED = "DEGRADED"            # Mesh engine running, but in standalone mode (0 peers or partial mDNS)
    DISCONNECTED = "DISCONNECTED"    # Local network dropped
    OFFLINE = "OFFLINE"              # Explicit standalone local mode
    FAILED = "FAILED"                # Socket bind or fatal network interface failure


def get_available_network_interfaces() -> List[Dict[str, str]]:
    """Enumerate all available IPv4 network interfaces and classify them."""
    interfaces: List[Dict[str, str]] = []
    seen_ips = set()

    try:
        hostname = socket.gethostname()
        _, _, ip_list = socket.gethostbyname_ex(hostname)
        for ip in ip_list:
            if ip in seen_ips:
                continue
            seen_ips.add(ip)

            # Classify interface type
            if ip.startswith("127."):
                iface_type = "loopback"
            elif ip.startswith("192.168.114.") or ip.startswith("192.168.177.") or ip.startswith("192.168.56."):
                iface_type = "virtual_vmware"
            elif ip.startswith("169.254."):
                iface_type = "link_local_apipa"
            elif ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172."):
                iface_type = "physical_lan_wifi"
            else:
                iface_type = "other"

            interfaces.append({
                "ip": ip,
                "type": iface_type,
                "hostname": hostname,
            })
    except Exception as e:
        logger.debug(f"Interface enumeration error: {e}")

    if not interfaces:
        interfaces.append({"ip": "127.0.0.1", "type": "loopback", "hostname": "localhost"})

    return interfaces


def get_local_ip() -> str:
    """
    Detect primary local IPv4 address.
    Prioritizes physical LAN/Wi-Fi subnets over virtual VMware/VPN adapters,
    and safely falls back to 127.0.0.1 when completely offline.
    """
    try:
        interfaces = get_available_network_interfaces()

        # 1. Prefer physical LAN/Wi-Fi
        physical = [i["ip"] for i in interfaces if i.get("type") == "physical_lan_wifi"]
        if physical:
            return physical[0]

        # 2. Try standard UDP probe without transmitting
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.5)
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass

        # 3. Fallback to any non-loopback
        non_loop = [i["ip"] for i in interfaces if i.get("type") != "loopback"]
        if non_loop:
            return non_loop[0]
    except Exception:
        pass

    return "127.0.0.1"


class MDNSListener(ServiceListener):
    """mDNS Service Listener for discovering ResQMesh peer services."""

    def __init__(self, on_peer_discovered):
        self.on_peer_discovered = on_peer_discovered

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        try:
            info = zc.get_service_info(type_, name)
            if info:
                self._handle_service(name, info)
        except Exception as e:
            logger.debug(f"mDNS add_service error: {e}")

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        try:
            info = zc.get_service_info(type_, name)
            if info:
                self._handle_service(name, info)
        except Exception as e:
            logger.debug(f"mDNS update_service error: {e}")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def _handle_service(self, name: str, info: ServiceInfo) -> None:
        try:
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
        except Exception as e:
            logger.debug(f"mDNS handling error for {name}: {e}")


class DiscoveryEngine:
    """
    Dual-Mode Peer Discovery Engine:
    1. mDNS (Zeroconf) on _resqmesh._tcp.local.
    2. UDP Broadcast fallback on port 52525.
    
    Includes explicit state tracking, interface fallback, and non-blocking lifecycle.
    """

    _instance: Optional["DiscoveryEngine"] = None

    def __init__(self, node_manager: Optional[NodeManager] = None):
        self.node_manager = node_manager or NodeManager.get_instance()
        self.is_running = False
        self.state: str = MeshState.NOT_INITIALIZED
        self.last_beacon_time: float = 0.0
        self.mdns_active: bool = False
        self.udp_active: bool = False
        self.last_error: Optional[str] = None

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
        """Start both mDNS and UDP broadcast discovery asynchronously without blocking."""
        if self.is_running:
            return
        self.is_running = True
        self.state = MeshState.INITIALIZING
        self._stop_event.clear()
        self.last_error = None

        threading.Thread(target=self._init_discovery_pipeline, daemon=True, name="Mesh-Discovery-Init").start()

    def _init_discovery_pipeline(self) -> None:
        """Asynchronously initialize discovery sockets and protocols."""
        local_ip = get_local_ip()
        node_id = self.node_manager.node_id
        node_name = self.node_manager.node_name
        role = self.node_manager.role
        port = self.node_manager.api_port

        logger.info(f"Starting Discovery Engine for {node_name} ({node_id}) on {local_ip}:{port}")

        # 1. Start mDNS advertising and listener with 3-second timeout protection
        try:
            self.zeroconf = Zeroconf()
            clean_svc_name = f"{node_name.replace(' ', '-')[:20]}-{node_id[:6]}.{MDNS_SERVICE_TYPE}"
            desc = {
                "node_id": node_id,
                "node_name": node_name,
                "role": role,
                "version": "1.0",
            }
            self.service_info = ServiceInfo(
                MDNS_SERVICE_TYPE,
                clean_svc_name,
                addresses=[socket.inet_aton(local_ip)],
                port=port,
                properties=desc,
                server=f"{node_name.replace(' ', '-')[:20]}.local.",
            )
            self.zeroconf.register_service(self.service_info)
            self.browser = ServiceBrowser(
                self.zeroconf, MDNS_SERVICE_TYPE, MDNSListener(self._on_peer_discovered)
            )
            self.mdns_active = True
            logger.info("mDNS Zeroconf service registered successfully.")
        except Exception as e:
            self.mdns_active = False
            self.last_error = f"mDNS unavailable: {e}"
            logger.warning(f"mDNS Zeroconf unavailable: {e} (operating with UDP broadcast)")

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
            self.udp_active = True
            logger.info(f"UDP Broadcast listener bound to 0.0.0.0:{UDP_BROADCAST_PORT}")
        except Exception as e:
            self.udp_active = False
            self.last_error = f"UDP bind error: {e}"
            logger.warning(f"Failed to bind UDP broadcast listener: {e}")

        # 3. Start UDP Beacon Broadcaster
        self._beacon_thread = threading.Thread(
            target=self._send_udp_beacons, daemon=True, name="UDP-Beacon-Broadcaster"
        )
        self._beacon_thread.start()

        # Update operational state
        if local_ip == "127.0.0.1" and not self.mdns_active and not self.udp_active:
            self.state = MeshState.OFFLINE
        elif len(self.node_manager.get_active_peers()) > 0:
            self.state = MeshState.CONNECTED
        else:
            self.state = MeshState.DEGRADED

    def update_node_info(self, name: str, role: str, port: int = 8000) -> None:
        """Update node metadata and re-advertise mDNS and UDP beacons dynamically."""
        logger.info(f"Updating Discovery Engine metadata: {name} [{role}] on port {port}")
        local_ip = get_local_ip()

        # Re-register mDNS if active
        if self.zeroconf and self.service_info:
            try:
                self.zeroconf.unregister_service(self.service_info)
                clean_svc_name = f"{name.replace(' ', '-')[:20]}-{self.node_manager.node_id[:6]}.{MDNS_SERVICE_TYPE}"
                desc = {
                    "node_id": self.node_manager.node_id,
                    "node_name": name,
                    "role": role,
                    "version": "1.0",
                }
                self.service_info = ServiceInfo(
                    MDNS_SERVICE_TYPE,
                    clean_svc_name,
                    addresses=[socket.inet_aton(local_ip)],
                    port=port,
                    properties=desc,
                    server=f"{name.replace(' ', '-')[:20]}.local.",
                )
                self.zeroconf.register_service(self.service_info)
            except Exception as e:
                logger.debug(f"mDNS re-registration notice: {e}")

        # Trigger immediate UDP burst beacon
        self._send_single_beacon()

    def _send_single_beacon(self) -> None:
        """Send a single one-off discovery beacon."""
        try:
            tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            tx_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            tx_sock.settimeout(0.5)

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
            tx_sock.sendto(data, ("<broadcast>", UDP_BROADCAST_PORT))
            tx_sock.close()
        except Exception:
            pass

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
                try:
                    tx_sock.sendto(data, ("<broadcast>", UDP_BROADCAST_PORT))
                except Exception:
                    pass

                self.last_beacon_time = time.time()

                # 2. Unicast directly to all known peers
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

                # Update mesh state dynamically based on peers
                if len(self.node_manager.get_active_peers()) > 0:
                    self.state = MeshState.CONNECTED
                elif get_local_ip() == "127.0.0.1":
                    self.state = MeshState.OFFLINE
                else:
                    self.state = MeshState.DEGRADED

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
                    "ip_address": "",
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
        self.state = MeshState.CONNECTED
        peer_ip = peer_info.get("ip_address")
        peer_port = peer_info.get("api_port", 8000)

        logger.info(
            f"Discovered peer [{peer_info.get('discovery_method')}]: {peer_info.get('name')} "
            f"({peer_id}) at {peer_ip}:{peer_port}"
        )

        if peer_ip and not peer_ip.startswith("127."):
            self._send_direct_http_ping(peer_ip, peer_port)

        try:
            from backend.app.sync.outbox_worker import StoreAndForwardWorker
            StoreAndForwardWorker.get_instance().trigger_flush()
        except Exception:
            try:
                from app.sync.outbox_worker import StoreAndForwardWorker
                StoreAndForwardWorker.get_instance().trigger_flush()
            except Exception:
                pass

    def get_mesh_status(self) -> dict:
        """Return comprehensive diagnostic status of mesh discovery subsystem."""
        active_peers = self.node_manager.get_active_peers()
        peer_count = len(active_peers)

        if not self.is_running:
            state = MeshState.NOT_INITIALIZED
        elif peer_count > 0:
            state = MeshState.CONNECTED
        elif get_local_ip() == "127.0.0.1":
            state = MeshState.OFFLINE
        elif not self.mdns_active and not self.udp_active:
            state = MeshState.FAILED
        else:
            state = MeshState.DEGRADED

        return {
            "state": state,
            "is_running": self.is_running,
            "local_ip": get_local_ip(),
            "interfaces": get_available_network_interfaces(),
            "mdns_active": self.mdns_active,
            "udp_active": self.udp_active,
            "active_peer_count": peer_count,
            "peers": active_peers,
            "last_beacon_time": self.last_beacon_time,
            "last_error": self.last_error,
        }

    def stop(self) -> None:
        """Stop discovery services cleanly."""
        if not self.is_running:
            return
        self.is_running = False
        self.state = MeshState.NOT_INITIALIZED
        self._stop_event.set()

        if self.zeroconf and self.service_info:
            try:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
            except Exception as e:
                logger.debug(f"Error closing zeroconf: {e}")

        if self._udp_sock:
            try:
                self._udp_sock.close()
            except Exception:
                pass

        self.mdns_active = False
        self.udp_active = False
        logger.info("Discovery Engine stopped.")

    def restart(self) -> dict:
        """Cleanly restart mesh discovery subsystem and return updated status."""
        logger.info("Restarting Mesh Discovery Subsystem...")
        self.stop()
        time.sleep(0.5)
        self.start()
        return self.get_mesh_status()
