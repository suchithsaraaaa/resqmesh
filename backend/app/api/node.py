import json
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = logging.getLogger("ResQMesh.NodeAPI")

try:
    from backend.app.database import get_db
    from backend.app.models import (
        NodeRecord,
        EventLog,
        OutboxItem,
        OperationalIncident,
        Report,
        ChatMessage,
        ResourceRequest,
    )
    from backend.app.schemas import (
        NodeRecordResponse,
        EventLogCreate,
        EventLogResponse,
        OutboxItemResponse,
    )
    from backend.app.services.node_manager import NodeManager
except ImportError:
    from app.database import get_db
    from app.models import (
        NodeRecord,
        EventLog,
        OutboxItem,
        OperationalIncident,
        Report,
        ChatMessage,
        ResourceRequest,
    )
    from app.schemas import (
        NodeRecordResponse,
        EventLogCreate,
        EventLogResponse,
        OutboxItemResponse,
    )
    from app.services.node_manager import NodeManager

try:
    from backend.app.crypto.security import DeviceKeyPair
    from backend.app.network.transport import HandshakeManager
    from backend.app.network.event_protocol import EventProtocolEngine
    from backend.app.network.relay import MeshRelayManager
    from backend.app.sync.delta_sync import DeltaSyncEngine
except ImportError:
    from app.crypto.security import DeviceKeyPair
    from app.network.transport import HandshakeManager
    from app.network.event_protocol import EventProtocolEngine
    from app.network.relay import MeshRelayManager
    from app.sync.delta_sync import DeltaSyncEngine

router = APIRouter(tags=["Node Core & Peer Network"])
node_manager = NodeManager.get_instance()


class NodeSetupRequest(BaseModel):
    name: str
    role: str = "responder"  # responder, commander
    port: int = 8000


class PeerRegisterRequest(BaseModel):
    node_id: str
    name: str
    role: str = "responder"
    ip_address: str
    api_port: int = 8000
    public_key: Optional[str] = None
    latency_ms: float = 0.0


# --- Local Node Management ---
@router.get("/node/status")
def get_local_node_status():
    """Return local node identity, role, configuration state, and uptime."""
    return NodeManager.get_instance().get_status()


@router.get("/node/mesh-status")
def get_mesh_network_status():
    """Return live operational mesh state, network interfaces, and peer metrics."""
    try:
        from backend.app.network.discovery import DiscoveryEngine
    except ImportError:
        from app.network.discovery import DiscoveryEngine

    return DiscoveryEngine.get_instance().get_mesh_status()


@router.post("/node/mesh-restart")
@router.post("/node/mesh-retry")
def retry_mesh_network_discovery():
    """Restart local peer discovery and re-probe network interfaces."""
    try:
        from backend.app.network.discovery import DiscoveryEngine
    except ImportError:
        from app.network.discovery import DiscoveryEngine

    return DiscoveryEngine.get_instance().restart()


@router.post("/node/setup")
def setup_local_node(setup_in: NodeSetupRequest, db: Session = Depends(get_db)):
    """First-run onboarding: configure node name and role (responder vs commander)."""
    mgr = NodeManager.get_instance()
    result = mgr.setup_node(
        name=setup_in.name,
        role=setup_in.role,
        port=setup_in.port,
    )

    # Persist or update local node record in SQLite
    local_record = db.query(NodeRecord).filter_by(node_id=result["node_id"]).first()
    if not local_record:
        local_record = NodeRecord(
            node_id=result["node_id"],
            name=result["node_name"],
            role=result["role"],
            public_key=result["public_key"],
            api_port=result["api_port"],
            status="online",
        )
        db.add(local_record)
    else:
        local_record.name = result["node_name"]
        local_record.role = result["role"]
        local_record.api_port = result["api_port"]
    db.commit()

    # Dynamically update Discovery Engine beacons
    try:
        from backend.app.network.discovery import DiscoveryEngine
        DiscoveryEngine.get_instance().update_node_info(
            name=result["node_name"],
            role=result["role"],
            port=result["api_port"],
        )
    except Exception as e:
        logger.debug(f"Discovery update note: {e}")

    return result


# --- Peer Management & Authentication ---
@router.post("/handshake")
def handle_handshake(syn_payload: dict, db: Session = Depends(get_db)):
    """Handle incoming peer handshake challenge and respond with authenticated ACK."""
    if not node_manager.keypair:
        node_manager.keypair = DeviceKeyPair()

    valid, ack_payload = HandshakeManager.verify_syn_and_create_ack(
        syn_payload=syn_payload,
        local_node_id=node_manager.node_id,
        keypair=node_manager.keypair,
    )
    if not valid or not ack_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Handshake verification failed or invalid signature",
        )

    # Register/update peer authenticated record in database
    remote_node_id = syn_payload.get("node_id")
    remote_pub_key = syn_payload.get("public_key")
    remote_role = syn_payload.get("role", "responder")
    existing = db.query(NodeRecord).filter_by(node_id=remote_node_id).first()
    if existing:
        existing.public_key = remote_pub_key
        existing.role = remote_role
        existing.status = "online"
    else:
        db.add(
            NodeRecord(
                node_id=remote_node_id,
                name=f"Peer-{remote_node_id[-4:].upper()}",
                role=remote_role,
                public_key=remote_pub_key,
                status="online",
            )
        )
    db.commit()

    return ack_payload


@router.get("/peers/")
def list_discovered_peers():
    """List currently active LAN peer nodes."""
    return node_manager.get_active_peers()


class PeerConnectRequest(BaseModel):
    peer_address: str  # e.g. "192.168.114.128:8000" or "192.168.114.128"


@router.post("/peers/register", status_code=status.HTTP_200_OK)
def register_peer(peer_in: PeerRegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Register or update an active peer discovered over mDNS, UDP broadcast, or reciprocal handshake."""
    client_host = request.client.host if request.client else None

    # In VM / NAT networks, peer_in.ip_address might be empty, 127.0.0.1, or an isolated interface.
    # The incoming TCP socket client_host is the guaranteed routable address!
    ip_to_use = peer_in.ip_address
    if not ip_to_use or ip_to_use.startswith("127.") or ip_to_use == "0.0.0.0":
        if client_host:
            ip_to_use = client_host
    elif client_host and client_host not in ["127.0.0.1", "localhost", "::1"] and ip_to_use != client_host:
        # In VMware NAT / virtual bridge, client_host is how the VM reaches back to the host!
        logger.info(f"Using routable client host {client_host} instead of reported {ip_to_use}")
        ip_to_use = client_host

    peer_dict = peer_in.model_dump()
    peer_dict["ip_address"] = ip_to_use
    peer_dict["last_seen"] = time.time()
    peer_dict["status"] = "online"

    node_manager.register_peer(peer_dict)

    # Update in database
    existing = db.query(NodeRecord).filter_by(node_id=peer_in.node_id).first()
    if existing:
        existing.name = peer_in.name
        existing.role = peer_in.role
        existing.ip_address = ip_to_use
        existing.api_port = peer_in.api_port
        existing.latency_ms = peer_in.latency_ms
        existing.status = "online"
    else:
        new_peer = NodeRecord(
            node_id=peer_in.node_id,
            name=peer_in.name,
            role=peer_in.role,
            ip_address=ip_to_use,
            api_port=peer_in.api_port,
            public_key=peer_in.public_key,
            latency_ms=peer_in.latency_ms,
            status="online",
        )
        db.add(new_peer)
    db.commit()

    # Trigger outbox flush so any pending incidents sync immediately
    try:
        from backend.app.sync.outbox_worker import StoreAndForwardWorker
        StoreAndForwardWorker.get_instance().trigger_flush()
    except Exception:
        try:
            from app.sync.outbox_worker import StoreAndForwardWorker
            StoreAndForwardWorker.get_instance().trigger_flush()
        except Exception:
            pass

    return {
        "status": "ok",
        "registered_peer": peer_in.node_id,
        "my_node": {
            "node_id": node_manager.node_id,
            "name": node_manager.node_name,
            "role": node_manager.role,
            "api_port": node_manager.api_port,
        },
    }


@router.post("/peers/connect", status_code=status.HTTP_200_OK)
def connect_peer_manually(req_in: PeerConnectRequest, db: Session = Depends(get_db)):
    """Manually connect to a remote peer by IP:port and establish bidirectional mesh link."""
    raw_addr = req_in.peer_address.strip()
    if ":" in raw_addr:
        parts = raw_addr.split(":")
        host = parts[0].strip()
        try:
            port = int(parts[1].strip())
        except ValueError:
            port = 8000
    else:
        host = raw_addr
        port = 8000

    import urllib.request
    try:
        url = f"http://{host}:{port}/node/status"
        req = urllib.request.Request(url, headers={"User-Agent": "ResQMesh-Node/1.0"})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=400, detail=f"Remote peer returned HTTP {resp.status}")
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot reach remote peer at {host}:{port}: {e}")

    remote_node_id = data.get("node_id")
    remote_name = data.get("name", "Remote-Peer")
    remote_role = data.get("role", "responder")
    remote_pubkey = data.get("public_key")

    peer_record = {
        "node_id": remote_node_id,
        "name": remote_name,
        "role": remote_role,
        "ip_address": host,
        "api_port": port,
        "public_key": remote_pubkey,
        "discovery_method": "Manual_Direct",
        "last_seen": time.time(),
        "status": "online",
    }
    node_manager.register_peer(peer_record)

    # Persist in DB
    existing = db.query(NodeRecord).filter_by(node_id=remote_node_id).first()
    if existing:
        existing.name = remote_name
        existing.role = remote_role
        existing.ip_address = host
        existing.api_port = port
        existing.status = "online"
    else:
        db.add(
            NodeRecord(
                node_id=remote_node_id,
                name=remote_name,
                role=remote_role,
                ip_address=host,
                api_port=port,
                public_key=remote_pubkey,
                status="online",
            )
        )
    db.commit()

    # Reciprocally register ourselves on the remote peer!
    my_payload = {
        "node_id": node_manager.node_id,
        "name": node_manager.node_name,
        "role": node_manager.role,
        "ip_address": "",
        "api_port": node_manager.api_port,
        "public_key": node_manager.keypair.get_public_key_b64() if node_manager.keypair else None,
    }
    try:
        reg_url = f"http://{host}:{port}/peers/register"
        req2 = urllib.request.Request(
            reg_url,
            data=json.dumps(my_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req2, timeout=4.0)
    except Exception as e:
        logger.warning(f"Could not reciprocally register on remote peer: {e}")

    # Trigger outbox flush
    try:
        from backend.app.sync.outbox_worker import StoreAndForwardWorker
        StoreAndForwardWorker.get_instance().trigger_flush()
    except Exception:
        try:
            from app.sync.outbox_worker import StoreAndForwardWorker
            StoreAndForwardWorker.get_instance().trigger_flush()
        except Exception:
            pass

    return {"status": "connected", "peer": peer_record}


@router.post("/events/ingest", status_code=status.HTTP_200_OK)
def ingest_event(event_in: EventLogCreate, db: Session = Depends(get_db)):
    """
    Idempotently ingest an incoming event from a peer.
    Returns delivery ACK and triggers multi-hop relay to adjacent peers.
    """
    ack = EventProtocolEngine.receive_and_acknowledge(
        db=db,
        envelope_dict=event_in.model_dump(),
        local_node_id=node_manager.node_id,
    )

    # If event was newly delivered and TTL permits, relay across multi-hop mesh
    if ack.get("status") == "delivered":
        try:
            MeshRelayManager.get_instance().handle_and_relay_event(
                event_dict=event_in.model_dump(),
                incoming_sender_id=event_in.origin_node_id,
            )
        except Exception:
            pass

    return ack


@router.post("/events/ack", status_code=status.HTTP_200_OK)
def receive_event_ack(ack_in: dict, db: Session = Depends(get_db)):
    """Process incoming delivery ACK from peer to mark outbox item acknowledged."""
    success = EventProtocolEngine.process_ack(db, ack_in)
    return {
        "status": "acknowledged" if success else "not_found",
        "event_id": ack_in.get("event_id"),
    }


@router.get("/events/outbox", response_model=List[OutboxItemResponse])
def get_pending_outbox_items(db: Session = Depends(get_db)):
    """List pending events awaiting synchronization with peers."""
    return db.query(OutboxItem).filter_by(status="pending").all()


# --- Distributed Delta Sync & Vector Consensus ---
@router.post("/sync/vector", status_code=status.HTTP_200_OK)
def handle_vector_sync(sync_in: dict, db: Session = Depends(get_db)):
    """
    Receive peer's version vector, return missing event delta in chronological order,
    and execute 2-way handshake acknowledging verified events in outbox.
    """
    remote_vector = sync_in.get("vector", {})
    sender_node_id = sync_in.get("sender_node_id")
    missing_events = DeltaSyncEngine.calculate_missing_events(db, remote_vector)

    # 2-WAY HANDSHAKE: If peer vector confirms it has our events, mark local outbox as acknowledged
    if remote_vector and node_manager.node_id in remote_vector:
        last_ts = remote_vector[node_manager.node_id].get("last_timestamp", 0.0)
        if last_ts > 0:
            pending_items = db.query(OutboxItem).filter_by(status="pending").all()
            for item in pending_items:
                ev_log = db.query(EventLog).filter_by(event_id=item.event_id).first()
                if ev_log and ev_log.timestamp <= last_ts + 0.001:
                    item.status = "acknowledged"
            db.commit()

    return {
        "node_id": node_manager.node_id,
        "missing_events": missing_events,
        "local_vector": DeltaSyncEngine.get_local_vector(db),
        "timestamp": time.time(),
    }


@router.post("/sync/ack", status_code=status.HTTP_200_OK)
def receive_sync_ack(ack_in: dict, db: Session = Depends(get_db)):
    """Process 2-way verification ACK to transition outbox items to acknowledged."""
    event_ids = ack_in.get("acknowledged_event_ids", [])
    if event_ids:
        items = db.query(OutboxItem).filter(OutboxItem.event_id.in_(event_ids)).all()
        for item in items:
            item.status = "acknowledged"
        db.commit()
    return {"status": "acknowledged", "count": len(event_ids)}


@router.get("/events/feed")
def get_live_event_feed(db: Session = Depends(get_db)):
    """Return chronological event stream for live tactical notification feed."""
    logs = db.query(EventLog).order_by(EventLog.timestamp.desc()).limit(30).all()
    feed = []
    for log in logs:
        try:
            payload = json.loads(log.payload) if isinstance(log.payload, str) else log.payload
        except Exception:
            payload = {}
        feed.append({
            "event_id": log.event_id,
            "event_type": log.event_type,
            "origin_node_id": log.origin_node_id,
            "timestamp": log.timestamp,
            "payload": payload,
        })
    return feed


@router.get("/sync/status")
def get_sync_status(db: Session = Depends(get_db)):
    """Return local vector clock state and sync metrics."""
    local_vector = DeltaSyncEngine.get_local_vector(db)
    pending_outbox_count = db.query(OutboxItem).filter_by(status="pending").count()
    return {
        "node_id": node_manager.node_id,
        "local_vector": local_vector,
        "pending_outbox_count": pending_outbox_count,
        "status": "synchronized" if pending_outbox_count == 0 else "syncing",
    }


@router.get("/node/routes")
def get_mesh_routes():
    """Return active multi-hop routing table with hop counts, next-hop relays, and latency metrics."""
    try:
        from backend.app.network.router import ResQMeshRouter
    except ImportError:
        from app.network.router import ResQMeshRouter
    router = ResQMeshRouter.get_instance(node_manager.node_id)
    return router.get_routes()


@router.get("/node/topology")
def get_mesh_topology():
    """Return visual multi-hop graph topology representation of nodes, links, and relay hops."""
    try:
        from backend.app.network.router import ResQMeshRouter
    except ImportError:
        from app.network.router import ResQMeshRouter
    router = ResQMeshRouter.get_instance(node_manager.node_id)
    return router.get_topology()

