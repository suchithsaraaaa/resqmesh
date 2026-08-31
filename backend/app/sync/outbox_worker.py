import json
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Optional, List

try:
    from backend.app.database import SessionLocal
    from backend.app.models import OutboxItem, EventLog
    from backend.app.network.transport import PeerTransportPool
    from backend.app.services.node_manager import NodeManager
except ImportError:
    from app.database import SessionLocal
    from app.models import OutboxItem, EventLog
    from app.network.transport import PeerTransportPool
    from app.services.node_manager import NodeManager

logger = logging.getLogger("ResQMesh.OutboxWorker")

DEFAULT_INTERVAL = 3.0  # seconds between outbox sweep checks
MAX_ATTEMPTS = 15


class StoreAndForwardWorker:
    """
    Background worker that continuously sweeps the local SQLite OutboxItem table
    and transmits pending events to available LAN peers, applying backoff on failure.
    """

    _instance: Optional["StoreAndForwardWorker"] = None

    def __init__(self, interval: float = DEFAULT_INTERVAL):
        self.interval = interval
        self.is_running = False
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

    @classmethod
    def get_instance(cls) -> "StoreAndForwardWorker":
        if cls._instance is None:
            cls._instance = StoreAndForwardWorker()
        return cls._instance

    def start(self) -> None:
        """Start the background store-and-forward sweep thread."""
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._run_loop, daemon=True, name="Outbox-Store-Forward-Worker"
        )
        self._worker_thread.start()
        logger.info("Store-and-Forward Outbox worker started.")

    def trigger_flush(self) -> None:
        """Signal the worker to immediately sweep the outbox upon peer reconnection."""
        self._wake_event.set()

    def _run_loop(self) -> None:
        last_sync_time = 0.0
        while not self._stop_event.is_set():
            try:
                self.flush_outbox()
                now = time.time()
                if now - last_sync_time >= 10.0:
                    last_sync_time = now
                    self.sync_all_peers()
            except Exception as e:
                logger.error(f"Error during outbox flush cycle: {e}")

            # Sleep until interval expires or woken by a peer reconnection event
            self._wake_event.wait(self.interval)
            self._wake_event.clear()

    def sync_all_peers(self, session=None) -> None:
        """Run bidirectional delta vector sync with all active peers every 10 seconds."""
        db = session or SessionLocal()
        try:
            try:
                from backend.app.sync.delta_sync import DeltaSyncEngine
            except ImportError:
                from app.sync.delta_sync import DeltaSyncEngine

            nm = NodeManager.get_instance()
            active_peers = nm.get_active_peers()
            for peer in active_peers:
                peer_ip = peer.get("ip_address")
                peer_port = peer.get("api_port", 8000)
                if peer_ip and not peer_ip.startswith("127."):
                    url = f"http://{peer_ip}:{peer_port}"
                    DeltaSyncEngine.sync_with_peer_url(url, db, nm.node_id)
        except Exception as e:
            logger.debug(f"Periodic peer delta sync failed: {e}")
        finally:
            if not session:
                db.close()

    def flush_outbox(self, session=None) -> int:
        """
        Sweep pending outbox items and attempt delivery to connected peers.
        Returns the count of successfully delivered events.
        """
        db = session or SessionLocal()
        delivered_count = 0

        try:
            pending_items: List[OutboxItem] = (
                db.query(OutboxItem)
                .filter(OutboxItem.status == "pending")
                .filter(OutboxItem.attempts < MAX_ATTEMPTS)
                .all()
            )

            if not pending_items:
                return 0

            transport_pool = PeerTransportPool.get_instance()
            nm = NodeManager.get_instance()
            active_peers = nm.get_active_peers()

            if not active_peers:
                # No peers online; delay delivery until peer discovery
                return 0

            for outbox_item in pending_items:
                event_log = db.query(EventLog).filter_by(event_id=outbox_item.event_id).first()
                if not event_log:
                    # Orphaned outbox item
                    outbox_item.status = "failed"
                    continue

                # Prepare wire packet payload
                try:
                    payload_data = json.loads(event_log.payload)
                except Exception:
                    payload_data = event_log.payload

                event_envelope = {
                    "event_id": event_log.event_id,
                    "event_type": event_log.event_type,
                    "origin_node_id": event_log.origin_node_id,
                    "timestamp": event_log.timestamp,
                    "version": event_log.version,
                    "hop_count": event_log.hop_count + 1,
                    "signature": event_log.signature,
                    "payload": payload_data,
                }

                # Attempt delivery to active peers
                delivered_to_any = False
                for peer in active_peers:
                    peer_id = peer.get("node_id")
                    if outbox_item.target_node_id and outbox_item.target_node_id != peer_id:
                        continue  # Targeted to another specific peer

                    # Connect and send
                    conn = transport_pool.connections.get(peer_id)
                    if not conn:
                        transport_pool.connect_and_authenticate(peer)
                        conn = transport_pool.connections.get(peer_id)

                    if conn:
                        if conn.post_event(event_envelope):
                            delivered_to_any = True
                            logger.info(
                                f"Delivered outbox event {outbox_item.event_id} to peer {peer_id}"
                            )

                if delivered_to_any:
                    outbox_item.status = "acknowledged"
                    delivered_count += 1
                else:
                    outbox_item.attempts += 1
                    outbox_item.last_attempt_at = datetime.now(timezone.utc)

            db.commit()
        finally:
            if not session:
                db.close()

        return delivered_count

    def stop(self) -> None:
        """Cleanly stop the worker thread."""
        if not self.is_running:
            return
        self.is_running = False
        self._stop_event.set()
        self._wake_event.set()
        logger.info("Store-and-Forward Outbox worker stopped.")
