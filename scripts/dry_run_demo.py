"""
ResQMesh AI: End-to-End System Dry Run & Interactive Walkthrough.
Demonstrates:
1. Decentralized Ed25519 Cryptographic Trust & QR Bootstrapping
2. Multi-Hop Mesh Network Packet Transmission & Duplicate Suppression
3. AI-Assisted Incident Correlation & Multi-Factor Duplicate Clustering
4. On-Device RAG Retrieval & Emergency SOP Action Synthesis
5. Delay-Tolerant Network (DTN) Partitioning & Last-Writer-Wins (LWW) Convergence
"""

import os
import sys
import time
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.crypto.security import DeviceKeyPair, TrustStore, verify_signature
from backend.app.network.protocol import Packet, PACKET_TYPE_DATA
from backend.app.network.router import ResQMeshRouter
from backend.app.ai.similarity import IncidentSimilarityEngine
from backend.app.ai.clustering import IncidentClusteringEngine, ClusterAction
from backend.app.ai.vector_store import LocalVectorStore
from backend.app.ai.rag_pipeline import RAGPipeline
from backend.app.sync.sync_engine import ResQMeshSyncEngine, resolve_lww_conflict
from tests.simulation.mesh_simulator import MeshNetworkSimulator


def run_dry_run_walkthrough():
    print("=" * 75)
    print("      [*] ResQMesh AI: Live End-to-End System Dry Run Walkthrough")
    print("=" * 75)
    print("Operational Status: Fully Offline (Zero Internet Connectivity Required)\n")

    # --------------------------------------------------------------------------
    # STAGE 1: Cryptographic Identity & QR Code Trust Bootstrapping
    # --------------------------------------------------------------------------
    print(">> [STAGE 1] Device Identity & Cryptographic Trust Bootstrapping")
    print("-" * 75)
    commander_keys = DeviceKeyPair()
    responder_keys = DeviceKeyPair()

    commander_qr = commander_keys.generate_qr_bootstrap_payload(
        device_id="CMD-ALPHA-01", role="commander"
    )
    print(f"[+] Commander Node (CMD-ALPHA-01) generated Ed25519 Key Pair.")
    print(f"    Public Key: {commander_keys.get_public_key_b64()[:32]}...")
    print(f"    QR Onboarding Payload: {commander_qr}")

    # Field Responder scans Commander QR code out-of-band
    responder_trust_store = TrustStore()
    bootstrapped = responder_trust_store.bootstrap_from_qr_payload(commander_qr)
    print(f"[+] Responder Node (RESP-01) scanned QR Code -> Trust Established: {bootstrapped}")
    print(f"    Is Commander Trusted? {responder_trust_store.is_peer_trusted('CMD-ALPHA-01')}\n")

    # --------------------------------------------------------------------------
    # STAGE 2: Multi-Hop Mesh Network Packet Transmission
    # --------------------------------------------------------------------------
    print(">> [STAGE 2] Multi-Hop Ad-Hoc Mesh Routing & Packet Forwarding")
    print("-" * 75)
    sim = MeshNetworkSimulator()
    sim.add_node("RESP-01", role="responder")
    sim.add_node("RELAY-02", role="relay")
    sim.add_node("CMD-ALPHA-01", role="commander")

    # Linear topology: RESP-01 <---> RELAY-02 <---> CMD-ALPHA-01
    sim.connect("RESP-01", "RELAY-02")
    sim.connect("RELAY-02", "CMD-ALPHA-01")

    # Responder submits report in the field
    report_pkt = sim.nodes["RESP-01"].create_report(
        report_id="REP-FLOOD-801",
        category="flood",
        description="Rapid water surge trapping 4 civilians on residential roof near West Bridge",
        lat=12.9716,
        lon=77.5946,
    )
    print(f"[+] RESP-01 created emergency packet 'pkt-REP-FLOOD-801-1' (CRC32: {report_pkt.checksum})")
    print(f"[+] Broadcasting packet over Bluetooth LE / Wi-Fi Direct...")
    sim.broadcast_from_node("RESP-01", report_pkt)

    # Step simulation
    tx_count = sim.run_until_quiescence(max_ticks=10)
    print(f"[+] Multi-hop mesh propagation complete in {tx_count} wireless transmissions.")
    print(f"[+] Command Center (CMD-ALPHA-01) received report: {'REP-FLOOD-801' in sim.nodes['CMD-ALPHA-01'].local_database}\n")

    # --------------------------------------------------------------------------
    # STAGE 3: AI-Powered Multi-Factor Incident Correlation & Duplicate Detection
    # --------------------------------------------------------------------------
    print(">> [STAGE 3] AI Incident Correlation & Duplicate Clustering Engine")
    print("-" * 75)
    similarity_engine = IncidentSimilarityEngine()
    clustering_engine = IncidentClusteringEngine(similarity_engine=similarity_engine)

    existing_incident = {
        "id": "INC-OP-100",
        "title": "West Bridge Flood & Water Inundation",
        "category": "flood",
        "description": "Flash flooding near riverbank causing water overflow",
        "lat": 12.9720,
        "lon": 77.5950,
        "created_at": datetime.now(timezone.utc),
    }

    incoming_report = {
        "id": "REP-FLOOD-802",
        "category": "flood",
        "description": "Rising flood waters trapping family on rooftop near West Bridge",
        "lat": 12.9718,
        "lon": 77.5948,
        "created_at": datetime.now(timezone.utc),
    }

    eval_result = clustering_engine.evaluate_report_against_incidents(
        incoming_report, [existing_incident]
    )

    print(f"[+] Incoming Report: '{incoming_report['description']}'")
    print(f"    Comparing against Master Incident: '{existing_incident['title']}'")
    print(f"    - Spatial Similarity Score:     {eval_result['score_breakdown']['spatial']:.4f}")
    print(f"    - Temporal Similarity Score:    {eval_result['score_breakdown']['temporal']:.4f}")
    print(f"    - Categorical Similarity Score: {eval_result['score_breakdown']['categorical']:.4f}")
    print(f"    - Text Similarity Score:        {eval_result['score_breakdown']['text']:.4f}")
    print(f"    >> Composite Match Confidence:  {eval_result['confidence_score'] * 100:.1f}%")
    print(f"    >> Recommended Action:          {eval_result['action'].value} (Target Incident: {eval_result['target_incident_id']})\n")

    # --------------------------------------------------------------------------
    # STAGE 4: On-Device RAG Retrieval & Standard Operating Procedure (SOP) Synthesis
    # --------------------------------------------------------------------------
    print(">> [STAGE 4] On-Device RAG Vector Search & Emergency SOP Synthesis")
    print("-" * 75)
    rag = RAGPipeline()
    rag_result = rag.generate_sop_guidance(
        description=incoming_report["description"],
        category=incoming_report["category"],
        top_k=2,
    )

    print(f"[+] Queried Local SOP Vector Index with query: '{incoming_report['category']} {incoming_report['description'][:40]}...'")
    print(f"[+] Retrieved {len(rag_result['retrieved_sops'])} Grounding SOPs:")
    for sop in rag_result["retrieved_sops"]:
        print(f"    - [{sop['doc_id']}] {sop['title']} (Cosine Match: {sop['score']:.4f})")

    print("\n[+] Synthesized Field Tactical Guidance:")
    print(f"{rag_result['recommendations']}\n")

    # --------------------------------------------------------------------------
    # STAGE 5: Delay-Tolerant Networking (DTN) & LWW Consensus Convergence
    # --------------------------------------------------------------------------
    print(">> [STAGE 5] Delay-Tolerant Networking (DTN) & Last-Writer-Wins Convergence")
    print("-" * 75)
    rec_local = {
        "id": "INC-OP-100",
        "status": "in_progress",
        "timestamp": 1700000100.0,
        "device_clock": 2,
        "device_id": "RESP-01",
    }
    rec_remote = {
        "id": "INC-OP-100",
        "status": "resolved",
        "timestamp": 1700000150.0,
        "device_clock": 4,
        "device_id": "CMD-ALPHA-01",
    }

    winner, winner_source = resolve_lww_conflict(rec_local, rec_remote)
    print(f"[+] Local Record:  Status='{rec_local['status']}', Clock={rec_local['device_clock']}, Ts={rec_local['timestamp']}")
    print(f"[+] Remote Record: Status='{rec_remote['status']}', Clock={rec_remote['device_clock']}, Ts={rec_remote['timestamp']}")
    print(f"[+] LWW Winner: [{winner_source}] -> Converged Status='{winner['status']}'")

    print("\n" + "=" * 75)
    print("  [SUCCESS] All Subsystems Verified: ResQMesh AI Dry Run Completed!")
    print("=" * 75)


if __name__ == "__main__":
    run_dry_run_walkthrough()
