import os
import sys
import json
import time
import uuid
import logging
from typing import Optional, Dict, List
from pathlib import Path

try:
    from backend.app.crypto.security import DeviceKeyPair
except ImportError:
    from app.crypto.security import DeviceKeyPair

logger = logging.getLogger("ResQMesh.NodeManager")


def get_app_data_dir() -> Path:
    """Return platform-appropriate application data directory."""
    if sys.platform == "win32":
        app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if app_data:
            base_dir = Path(app_data) / "ResQMesh AI" / "data"
            if not base_dir.exists():
                alt_dir = Path(app_data) / "ResQMeshAI" / "data"
                if alt_dir.exists():
                    base_dir = alt_dir
        else:
            base_dir = Path.home() / ".resqmesh" / "data"
    else:
        base_dir = Path.home() / ".resqmesh" / "data"

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


class NodeManager:
    """Manages local node identity, role, keypair, and active peer registry."""

    _instance: Optional["NodeManager"] = None

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or get_app_data_dir()
        self.config_path = self.data_dir / "node_config.json"

        self.node_id: str = ""
        self.node_name: str = ""
        self.role: str = "responder"  # responder, commander, relay
        self.api_port: int = 8000
        self.keypair: Optional[DeviceKeyPair] = None
        self.is_configured: bool = False
        self.boot_time: float = time.time()

        # In-memory discovered peer registry: node_id -> dict
        self._active_peers: Dict[str, dict] = {}

        self.load_or_initialize()

    @classmethod
    def get_instance(cls) -> "NodeManager":
        if cls._instance is None:
            cls._instance = NodeManager()
        return cls._instance

    def load_or_initialize(self) -> None:
        """Load existing node identity from disk or prepare unconfigured defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.node_id = data.get("node_id", f"node-{uuid.uuid4().hex[:8]}")
                    self.node_name = data.get("node_name", "ResQMesh-Node")
                    self.role = data.get("role", "responder")
                    self.api_port = data.get("api_port", 8000)
                    self.is_configured = data.get("is_configured", True)
                    priv_b64 = data.get("private_key")
                    if priv_b64:
                        self.keypair = DeviceKeyPair.from_private_key_b64(priv_b64)
                    else:
                        self.keypair = DeviceKeyPair()
                    logger.info(f"Loaded existing node identity: {self.node_name} ({self.node_id})")
                    return
            except Exception as e:
                logger.warning(f"Failed to read node config, creating fresh identity: {e}")

        # Default unconfigured identity for first-run onboarding
        self.node_id = f"node-{uuid.uuid4().hex[:8]}"
        self.node_name = f"Node-{self.node_id[-4:].upper()}"
        self.role = "responder"
        self.keypair = DeviceKeyPair()
        self.is_configured = False

    def setup_node(self, name: str, role: str, port: int = 8000) -> dict:
        """First-run setup: configure node name and role (responder / commander)."""
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Node name cannot be empty.")
        if len(clean_name) > 64:
            clean_name = clean_name[:64]

        self.node_name = clean_name
        self.role = role.lower() if role.lower() in ["responder", "commander", "relay"] else "responder"
        self.api_port = port
        self.is_configured = True

        if not self.keypair:
            self.keypair = DeviceKeyPair()

        config_data = {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "role": self.role,
            "api_port": self.api_port,
            "public_key": self.keypair.get_public_key_b64(),
            "private_key": self.keypair.get_private_key_b64(),
            "is_configured": True,
            "updated_at": time.time(),
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Node configured successfully: {self.node_name} [{self.role}]")
        except Exception as e:
            logger.error(f"Failed to write node config: {e}")

        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "role": self.role,
            "api_port": self.api_port,
            "public_key": self.keypair.get_public_key_b64(),
            "is_configured": True,
            "updated_at": config_data["updated_at"],
        }

    def get_status(self) -> dict:
        """Return operational status of this peer node."""
        uptime_seconds = int(time.time() - self.boot_time)
        return {
            "node_id": self.node_id,
            "name": self.node_name,
            "role": self.role,
            "is_configured": self.is_configured,
            "configured": self.is_configured,
            "api_port": self.api_port,
            "public_key": self.keypair.get_public_key_b64() if self.keypair else None,
            "uptime_seconds": uptime_seconds,
            "active_peer_count": len(self.get_active_peers()),
            "status": "online",
        }

    def register_peer(self, peer_data: dict) -> None:
        """Register or update a peer discovered over LAN."""
        peer_id = peer_data.get("node_id")
        if not peer_id or peer_id == self.node_id:
            return  # Do not register self

        if "last_seen" not in peer_data:
            peer_data["last_seen"] = time.time()
        peer_data["status"] = "online"
        self._active_peers[peer_id] = peer_data

    def remove_peer(self, peer_id: str) -> None:
        """Remove a peer from active peers list."""
        if peer_id in self._active_peers:
            del self._active_peers[peer_id]

    def get_active_peers(self, timeout_seconds: float = 30.0) -> List[dict]:
        """Return list of online peers seen within timeout threshold."""
        now = time.time()
        active = []
        for peer_id, peer in list(self._active_peers.items()):
            if now - peer.get("last_seen", 0) <= timeout_seconds:
                active.append(peer)
            else:
                peer["status"] = "offline"
        return active
