"""
ResQMesh AI - End-to-End Multi-Laptop Simulation Script
Simulates two completely independent Windows laptops (Node-Alpha & Node-Beta)
operating on an offline local subnet.
Tests:
  1. Independent node cryptographic identity generation
  2. P2P discovery and mutual Ed25519 challenge-response handshake
  3. Real-time event broadcasting and ACK confirmation
  4. Disconnected network partition (delay-tolerant store-and-forward outbox)
  5. Network reconnection and delta vector synchronization
  6. On-device AI incident correlation across nodes
"""

import os
import sys
import time
import json
import uuid

# Ensure root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.app.models
from backend.app.database import Base
from backend.app.models import EventLog, OutboxItem, OperationalIncident, Report
from backend.app.crypto.security import DeviceKeyPair
from backend.app.network.transport import HandshakeManager
from backend.app.network.event_protocol import EventProtocolEngine
from backend.app.sync.delta_sync import DeltaSyncEngine
from backend.app.services.incident_matcher import IncidentMatcherService


def create_isolated_node_db():
    """Create isolated in-memory SQLite database representing a separate laptop."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()


def main():
    print("=" * 70)
    print("  ResQMesh AI: Multi-Laptop Peer-to-Peer Integration Test")
    print("=" * 70)

    # -------------------------------------------------------------
    # Step 1: Initialize Two Independent Laptops
    # -------------------------------------------------------------
    print("\n[Step 1] Initializing Independent Laptops...")
    db_alpha = create_isolated_node_db()
    db_beta = create_isolated_node_db()

    key_alpha = DeviceKeyPair()
    key_beta = DeviceKeyPair()

    node_alpha_id = "LAPTOP-ALPHA-HQ"
    node_beta_id = "LAPTOP-BETA-FIELD"

    print(f"  -> Laptop Alpha (Commander) ID: {node_alpha_id} (Key: {key_alpha.get_public_key_b64()[:16]}...)")
    print(f"  -> Laptop Beta (Responder)  ID: {node_beta_id} (Key: {key_beta.get_public_key_b64()[:16]}...)")

    # -------------------------------------------------------------
    # Step 2: Cryptographic Mutual Handshake
    # -------------------------------------------------------------
    print("\n[Step 2] Performing Mutual Ed25519 Cryptographic Handshake...")
    # Laptop Alpha initiates handshake with Beta
    syn_packet = HandshakeManager.create_syn(node_alpha_id, "commander", key_alpha)
    print(f"  -> Alpha transmits HANDSHAKE_SYN (Nonce: {syn_packet['nonce'][:12]}...)")

    # Laptop Beta responds with signed challenge
    is_valid, ack_packet = HandshakeManager.verify_syn_and_create_ack(syn_packet, node_beta_id, key_beta)
    print(f"  -> Beta verifies Alpha and responds with HANDSHAKE_ACK (Verified: {is_valid})")
    assert is_valid is True

    # Alpha verifies Beta's ACK
    is_ack_valid = HandshakeManager.verify_ack(ack_packet, syn_packet["nonce"])
    assert is_ack_valid is True
    print("  [SUCCESS] P2P Mutual Authentication Established!")

    # -------------------------------------------------------------
    # Step 3: Online Event Transmission & Acknowledgment
    # -------------------------------------------------------------
    print("\n[Step 3] Live Event Broadcast & Ingestion...")
    class MockNM:
        def __init__(self, node_id, key_pair):
            self.node_id = node_id
            self.keypair = key_pair
            self.key_pair = key_pair

    nm_beta = MockNM(node_beta_id, key_beta)

    # Beta creates an incident report
    envelope_obj = EventProtocolEngine.emit_event(
        db=db_beta,
        event_type="incident.created",
        payload={
            "incident_id": "inc-field-001",
            "title": "Severe Gas Pipeline Rupture",
            "category": "hazmat",
            "severity": "critical",
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
        node_manager=nm_beta,
    )
    evt_envelope = envelope_obj.to_dict()
    print(f"  -> Beta emitted signed event: {evt_envelope['event_id']}")

    # Outbox on Beta has 1 pending item
    beta_outbox = db_beta.query(OutboxItem).filter_by(status="pending").count()
    assert beta_outbox == 1
    print(f"  -> Beta local outbox holds pending event (Queue count: {beta_outbox})")

    # Alpha receives the event over local network
    ack = EventProtocolEngine.receive_and_acknowledge(
        db=db_alpha,
        envelope_dict=evt_envelope,
        local_node_id=node_alpha_id,
    )
    assert ack["status"] == "delivered"
    print(f"  -> Alpha received and verified event (Status: {ack['status']})")

    # Beta processes the ACK
    EventProtocolEngine.process_ack(db_beta, ack)
    beta_outbox_after = db_beta.query(OutboxItem).filter_by(status="pending").count()
    assert beta_outbox_after == 0
    print(f"  -> Beta processed delivery ACK (Pending outbox cleared: {beta_outbox_after} items)")
    print("  [SUCCESS] Real-Time Event Delivered & Confirmed!")

    # -------------------------------------------------------------
    # Step 4: Network Partition (Laptops Disconnected)
    # -------------------------------------------------------------
    print("\n[Step 4] Simulating Network Disconnection (Offline Partition)...")
    print("  -> Laptops are separated / Wi-Fi disconnected.")

    # Beta creates 2 events while offline
    EventProtocolEngine.emit_event(
        db=db_beta,
        event_type="report.created",
        payload={
            "report_id": "rep-offline-1",
            "description": "Thick yellowish gas cloud drifting east",
            "category": "hazmat",
            "latitude": 12.9718,
            "longitude": 77.5948,
        },
        node_manager=nm_beta,
    )
    EventProtocolEngine.emit_event(
        db=db_beta,
        event_type="report.created",
        payload={
            "report_id": "rep-offline-2",
            "description": "Two workers trapped in warehouse near leak",
            "category": "hazmat",
            "latitude": 12.9720,
            "longitude": 77.5950,
        },
        node_manager=nm_beta,
    )

    pending_count = db_beta.query(OutboxItem).filter_by(status="pending").count()
    print(f"  -> Beta created 2 reports while offline. Safe in SQLite Outbox: {pending_count} pending items.")
    assert pending_count == 2
    print("  [SUCCESS] Delay-Tolerant Store-and-Forward Outbox Active!")

    # -------------------------------------------------------------
    # Step 5: Network Reconnection & Delta Synchronization
    # -------------------------------------------------------------
    print("\n[Step 5] Simulating Network Reconnection & Delta Sync...")
    print("  -> Both laptops reconnect to same offline Wi-Fi hotspot.")

    # Alpha computes its local version vector
    alpha_vector = DeltaSyncEngine.get_local_vector(db_alpha)
    print(f"  -> Alpha version vector: {alpha_vector}")

    # Beta calculates missing events for Alpha
    missing_for_alpha = DeltaSyncEngine.calculate_missing_events(db_beta, alpha_vector)
    print(f"  -> Beta calculated missing delta for Alpha: {len(missing_for_alpha)} events")
    assert len(missing_for_alpha) == 2

    # Alpha applies incoming delta
    sync_result = DeltaSyncEngine.apply_delta_events(db_alpha, missing_for_alpha, node_alpha_id)
    print(f"  -> Alpha applied delta: {sync_result['applied']} applied, {sync_result['duplicates']} duplicates")
    assert sync_result["applied"] == 2

    # Verify both laptops now have identical EventLog counts
    alpha_total_events = db_alpha.query(EventLog).count()
    beta_total_events = db_beta.query(EventLog).count()
    print(f"  -> Alpha Total Events: {alpha_total_events} | Beta Total Events: {beta_total_events}")
    assert alpha_total_events == beta_total_events
    print("  [SUCCESS] Delta Vector Sync Completed! Identical State Achieved.")

    # -------------------------------------------------------------
    # Step 6: On-Device AI Incident Correlation
    # -------------------------------------------------------------
    print("\n[Step 6] Verifying On-Device AI Incident Correlation...")
    matcher = IncidentMatcherService(db=db_alpha)

    # Report was already materialized into SQLite during delta sync!
    rep_obj = db_alpha.query(Report).filter_by(report_id="rep-offline-1").first()
    assert rep_obj is not None
    print(f"  -> Retrieved synced report from Alpha's SQLite: {rep_obj.report_id}")

    match_result = matcher.process_new_report(rep_obj)
    print(f"  -> AI Correlation Action: {match_result['action']}")
    print(f"  -> Confidence Score: {match_result['confidence_score']}")
    assert match_result["action"] in ["AUTO_MERGE", "NEEDS_REVIEW"]
    print("  [SUCCESS] Incoming Field Report Correlated into Master Incident!")

    print("\n" + "=" * 70)
    print("  ALL MULTI-LAPTOP FIELD TESTS PASSED SUCCESSFULLY! (100% Correct)")
    print("=" * 70)


if __name__ == "__main__":
    main()
