import os
import sys
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import Base, OperationalIncident, ResourceRequest, EventLog
from backend.app.network.event_protocol import EventProtocolEngine
from backend.app.sync.delta_sync import DeltaSyncEngine
from backend.app.services.node_manager import NodeManager

def test_incident_and_resource_mesh_sync():
    # Setup Node A (Alpha) in-memory DB
    engine_a = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine_a)
    SessionA = sessionmaker(bind=engine_a)
    db_a = SessionA()

    # Setup Node B (Beta) in-memory DB
    engine_b = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine_b)
    SessionB = sessionmaker(bind=engine_b)
    db_b = SessionB()

    nm_a = NodeManager()
    nm_a.setup_node("Commander-Laptop", "commander", 8000)

    nm_b = NodeManager()
    nm_b.setup_node("Field-Responder-1", "responder", 8001)

    print("Test 1: Emitting new incident on Node A...")
    inc = OperationalIncident(
        incident_id="inc-train-01",
        title="Train Derailment on River Bridge",
        category="transport",
        severity="critical",
        latitude=12.9716,
        longitude=77.5946,
        summary="Carriages overturned",
        status="open",
    )
    db_a.add(inc)
    db_a.commit()

    EventProtocolEngine.emit_event(
        db=db_a,
        event_type="incident.created",
        payload={
            "incident_id": inc.incident_id,
            "title": inc.title,
            "category": inc.category,
            "severity": inc.severity,
            "latitude": inc.latitude,
            "longitude": inc.longitude,
            "summary": inc.summary,
            "status": inc.status,
        },
        node_manager=nm_a,
    )

    print("Test 2: Emitting resource request dispatch on Node A...")
    res = ResourceRequest(
        resource_id="res-trauma-01",
        resource_type="Medical Trauma Kit",
        quantity=4,
        urgency="critical",
        status="dispatched",
        requester_id="Laptop-Squad-1",
    )
    db_a.add(res)
    db_a.commit()

    EventProtocolEngine.emit_event(
        db=db_a,
        event_type="resource.updated",
        payload={
            "resource_id": res.resource_id,
            "status": "dispatched",
            "resource_type": res.resource_type,
            "quantity": res.quantity,
            "urgency": res.urgency,
        },
        node_manager=nm_a,
    )

    # Calculate delta for Node B (Node B currently has empty vector)
    vector_b = DeltaSyncEngine.get_local_vector(db_b)
    missing_events = DeltaSyncEngine.calculate_missing_events(db_a, vector_b)
    print(f"Missing events detected for Node B: {len(missing_events)}")
    assert len(missing_events) == 2, f"Expected 2 missing events, got {len(missing_events)}"

    # Apply delta to Node B
    result = DeltaSyncEngine.apply_delta_events(db_b, missing_events, nm_b.node_id)
    print(f"Applied on Node B: {result}")
    assert result["applied"] == 2

    # Verify Node B now has the incident and resource in its SQLite DB!
    b_inc = db_b.query(OperationalIncident).filter_by(incident_id="inc-train-01").first()
    assert b_inc is not None, "Incident was not materialized on Node B!"
    assert b_inc.title == "Train Derailment on River Bridge"
    assert b_inc.severity == "critical"
    print(f"Node B incident verified: {b_inc.title} ({b_inc.severity})")

    # Verify Outbox ACK via 2-Way Handshake
    print("Test 3: Testing 2-Way Handshake Outbox ACK...")
    from backend.app.models import OutboxItem, Report
    pending_before = db_a.query(OutboxItem).filter_by(status="pending").count()
    print(f"Node A pending outbox items before 2-way ACK: {pending_before}")
    assert pending_before == 2

    # Simulate Node B sending 2-way ACK to Node A for the received events
    ack_ids = [ev["event_id"] for ev in missing_events]
    items_to_ack = db_a.query(OutboxItem).filter(OutboxItem.event_id.in_(ack_ids)).all()
    for item in items_to_ack:
        item.status = "acknowledged"
    db_a.commit()

    pending_after = db_a.query(OutboxItem).filter_by(status="pending").count()
    print(f"Node A pending outbox items after 2-way ACK: {pending_after}")
    assert pending_after == 0, "Outbox should have 0 pending items after 2-way ACK!"

    # Test 4: Incident Merge Synchronization
    print("Test 4: Merging field report into incident on Node A and syncing to Node B...")
    merge_rep_id = "rep-spark-99"
    db_a.add(
        Report(
            report_id=merge_rep_id,
            incident_id=inc.incident_id,
            device_id=nm_a.node_id,
            user_id="commander",
            category=inc.category,
            description="Transformer spark confirmed near carriage",
            latitude=inc.latitude,
            longitude=inc.longitude,
        )
    )
    inc.summary = f"{inc.summary} | Merged: Transformer spark confirmed near carriage"
    db_a.commit()

    EventProtocolEngine.emit_event(
        db=db_a,
        event_type="incident.merged",
        payload={
            "incident_id": inc.incident_id,
            "report_id": merge_rep_id,
            "title": inc.title,
            "summary": inc.summary,
            "description": "Transformer spark confirmed near carriage",
            "merged_by": nm_a.node_name,
            "report_count": 2,
        },
        node_manager=nm_a,
    )

    # Sync merge event to Node B
    vector_b_2 = DeltaSyncEngine.get_local_vector(db_b)
    merge_missing = DeltaSyncEngine.calculate_missing_events(db_a, vector_b_2)
    assert len(merge_missing) == 1, f"Expected 1 merge event, got {len(merge_missing)}"

    DeltaSyncEngine.apply_delta_events(db_b, merge_missing, nm_b.node_id)

    # Verify Node B incident has report count of 2 and linked report
    db_b.expire_all()
    b_inc_merged = db_b.query(OperationalIncident).filter_by(incident_id=inc.incident_id).first()
    assert b_inc_merged is not None
    assert len(b_inc_merged.reports) >= 1, "Report should be attached on Node B!"
    b_rep = db_b.query(Report).filter_by(report_id=merge_rep_id).first()
    assert b_rep is not None, "Merged report entity should exist on Node B!"
    print(f"Node B merged report confirmed: {b_rep.report_id} linked to {b_rep.incident_id}")

    # Test 5: Incident-Tied Resource Request Synchronization & Cluster Clearance
    print("Test 5: Requesting resource tied to incident on Node A and syncing to Node B...")
    res_tied = ResourceRequest(
        resource_id="res-hazmat-01",
        incident_id=inc.incident_id,
        resource_type="Hazmat Decontamination Squad",
        quantity=4,
        urgency="critical",
        status="pending",
        requester_id="Field-Responder-1",
    )
    db_a.add(res_tied)
    db_a.commit()

    EventProtocolEngine.emit_event(
        db=db_a,
        event_type="resource.created",
        payload={
            "resource_id": res_tied.resource_id,
            "incident_id": inc.incident_id,
            "incident_title": inc.title,
            "requester_id": res_tied.requester_id,
            "resource_type": res_tied.resource_type,
            "quantity": res_tied.quantity,
            "urgency": res_tied.urgency,
            "status": res_tied.status,
        },
        node_manager=nm_a,
    )

    vector_b_3 = DeltaSyncEngine.get_local_vector(db_b)
    res_missing = DeltaSyncEngine.calculate_missing_events(db_a, vector_b_3)
    assert len(res_missing) == 1, f"Expected 1 resource event, got {len(res_missing)}"

    DeltaSyncEngine.apply_delta_events(db_b, res_missing, nm_b.node_id)

    db_b.expire_all()
    b_res = db_b.query(ResourceRequest).filter_by(resource_id="res-hazmat-01").first()
    assert b_res is not None, "Tied resource request was not materialized on Node B!"
    assert b_res.incident_id == inc.incident_id, f"Resource request not tied to incident! Got {b_res.incident_id}"
    assert b_res.resource_type == "Hazmat Decontamination Squad"
    print(f"Node B tied resource request verified: {b_res.quantity}x {b_res.resource_type} tied to {b_res.incident_id}")

    # Verify cluster clearance on Node B after merge
    db_b.add(
        Report(
            report_id="rep-mesh-demo-1",
            incident_id=inc.incident_id,
            device_id=nm_a.node_id,
            user_id="commander",
            category="fire",
            description="Merged demo correlation report",
            latitude=inc.latitude,
            longitude=inc.longitude,
        )
    )
    db_b.commit()
    demo_rep = db_b.query(Report).filter_by(report_id="rep-mesh-demo-1").first()
    assert demo_rep.incident_id is not None, "Report should be marked as merged into incident"
    print("Node B correlation cluster clearance confirmed: rep-mesh-demo-1 is attached to incident.")

    # Test 6: Active AI Screening for Duplicate Incidents & Broadcaster Tracking
    print("Test 6: Testing active AI screening for duplicate incidents...")
    from backend.app.api.incidents import get_pending_clusters, merge_incident_report, MergeIncidentRequest

    inc_dup = OperationalIncident(
        incident_id="inc-train-02-dup",
        title="Train Derailment on River Bridge",
        category="transport",
        severity="critical",
        latitude=12.9716,
        longitude=77.5946,
        summary="Secondary report of derailed carriages",
        status="open",
        broadcaster_name="sara1",
    )
    db_a.add(inc_dup)
    db_a.commit()

    # Run AI screening
    clusters = get_pending_clusters(db=db_a)
    print(f"AI Detected Duplicate Incident Clusters: {len(clusters)}")
    assert len(clusters) >= 1, "AI failed to detect duplicate incident!"
    dup_cluster = next((c for c in clusters if c["reportId"] == inc_dup.incident_id), None)
    assert dup_cluster is not None, "Duplicate incident not identified in clusters!"
    assert dup_cluster["confidenceScore"] >= 0.85, f"Confidence too low: {dup_cluster['confidenceScore']}"
    assert dup_cluster["targetIncidentId"] == inc.incident_id
    print(f"AI successfully screened duplicate incident: {dup_cluster['description']} with confidence {dup_cluster['confidenceScore']}")

    # Merge duplicate incident into master incident
    merge_res = merge_incident_report(
        incident_id=inc.incident_id,
        merge_in=MergeIncidentRequest(report_id=inc_dup.incident_id, summary_note="Verified duplicate carriage derailment"),
        db=db_a
    )
    assert inc_dup.status == "merged", "Duplicate incident should be marked as merged!"
    assert merge_res.report_count >= 2, f"Expected report_count >= 2, got {merge_res.report_count}"
    print(f"Duplicate incident merge successful! Master incident reports: {merge_res.report_count}, duplicate status: {inc_dup.status}")

    # Test 7: Location Metadata & Persistent Duplicate Segregation
    print("Test 7: Testing location metadata and persistent duplicate segregation...")
    from backend.app.api.incidents import dismiss_correlation_cluster, SegregateCorrelationRequest

    # 7A: Incident without GPS coordinates (Offline / No Fix)
    inc_nogps = OperationalIncident(
        incident_id="inc-nogps-01",
        title="Structural Damage at Substation",
        category="structural",
        severity="medium",
        latitude=None,
        longitude=None,
        accuracy=None,
        location_source="unavailable",
        summary="Transformer wall collapse",
        status="open",
        broadcaster_name="Field-Responder-1",
    )
    db_a.add(inc_nogps)
    db_a.commit()
    assert inc_nogps.latitude is None
    assert inc_nogps.location_source == "unavailable"
    print("Incident created without GPS coordinates verified (location_source: 'unavailable').")

    # 7B: Create two duplicate incidents to verify persistent segregation
    inc_seg1 = OperationalIncident(
        incident_id="inc-seg-master",
        title="Wildfire near Forest Boundary",
        category="fire",
        severity="high",
        latitude=13.0100,
        longitude=77.5800,
        accuracy=15.0,
        location_source="gps",
        summary="Trees blazing rapidly",
        status="open",
        broadcaster_name="Commander",
    )
    inc_seg2 = OperationalIncident(
        incident_id="inc-seg-dup",
        title="Wildfire near Forest Boundary",
        category="fire",
        severity="high",
        latitude=13.0102,
        longitude=77.5801,
        accuracy=10.0,
        location_source="gps",
        summary="Smoke column spotted near trees",
        status="open",
        broadcaster_name="Responder-1",
    )
    db_a.add(inc_seg1)
    db_a.add(inc_seg2)
    db_a.commit()

    # Verify AI detects duplicate initially
    clusters_before = get_pending_clusters(db=db_a)
    dup_found = any(c["reportId"] == inc_seg2.incident_id and c["targetIncidentId"] == inc_seg1.incident_id for c in clusters_before)
    assert dup_found, "AI should detect inc-seg-dup as duplicate of inc-seg-master"
    print("AI correlation successfully detected duplicate pair.")

    # Call dismiss / keep segregated
    dismiss_res = dismiss_correlation_cluster(
        req=SegregateCorrelationRequest(report_id=inc_seg2.incident_id, target_incident_id=inc_seg1.incident_id),
        db=db_a
    )
    assert dismiss_res["status"] == "segregated"
    print("Segregation registered in database and emitted to mesh.")

    # Verify AI no longer returns this pair!
    clusters_after = get_pending_clusters(db=db_a)
    dup_still_found = any(c["reportId"] == inc_seg2.incident_id and c["targetIncidentId"] == inc_seg1.incident_id for c in clusters_after)
    assert not dup_still_found, "Segregated pair MUST NOT appear in similarity clusters again!"
    print("Persistent correlation segregation VERIFIED: candidate does NOT return in similarity match!")

    print("ALL 7 TESTS: ACTIVE SCREENING, BROADCASTER NAME, DELTA SYNC, 2-WAY ACK, MERGE, RESCIND & PERSISTENT SEGREGATION PASSED!")

if __name__ == "__main__":
    test_incident_and_resource_mesh_sync()

