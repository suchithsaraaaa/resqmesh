import time
import pytest
from backend.app.sync.sync_engine import (
    ResQMeshSyncEngine,
    OutboxItem,
    resolve_lww_conflict,
)


def test_lww_conflict_resolution():
    # 1. Timestamp winner
    rec_local = {"id": "1", "timestamp": 100.0, "device_clock": 5, "device_id": "a"}
    rec_remote = {"id": "1", "timestamp": 200.0, "device_clock": 2, "device_id": "z"}

    winning, source = resolve_lww_conflict(rec_local, rec_remote)
    assert source == "REMOTE"
    assert winning["timestamp"] == 200.0

    # 2. Clock tie-breaker winner
    rec_local_clk = {"id": "1", "timestamp": 100.0, "device_clock": 10, "device_id": "a"}
    rec_remote_clk = {"id": "1", "timestamp": 100.0, "device_clock": 5, "device_id": "z"}

    winning2, source2 = resolve_lww_conflict(rec_local_clk, rec_remote_clk)
    assert source2 == "LOCAL"
    assert winning2["device_clock"] == 10

    # 3. Device ID tie-breaker winner
    rec_local_dev = {"id": "1", "timestamp": 100.0, "device_clock": 5, "device_id": "alpha"}
    rec_remote_dev = {"id": "1", "timestamp": 100.0, "device_clock": 5, "device_id": "beta"}

    winning3, source3 = resolve_lww_conflict(rec_local_dev, rec_remote_dev)
    assert source3 == "REMOTE"
    assert winning3["device_id"] == "beta"


def test_sync_engine_outbox_queue_and_delta():
    sync = ResQMeshSyncEngine(local_device_id="node-local")

    t_before = time.time() - 1.0

    item1 = sync.enqueue_change(
        item_id="out-101",
        entity_type="Report",
        entity_id="rep-001",
        action="CREATE",
        payload={"category": "fire"},
    )

    item2 = sync.enqueue_change(
        item_id="out-102",
        entity_type="Report",
        entity_id="rep-002",
        action="CREATE",
        payload={"category": "medical"},
    )

    assert len(sync.outbox) == 2

    delta = sync.generate_delta_bundle(since_timestamp=t_before)
    assert len(delta) == 2

    # Acknowledge item1
    sync.process_sync_ack(peer_id="node-peer-1", acked_item_ids=["out-101"], sync_timestamp=time.time())

    assert len(sync.outbox) == 1
    assert "out-101" not in sync.outbox
    assert "out-102" in sync.outbox


def test_sync_engine_delta_processing():
    sync = ResQMeshSyncEngine(local_device_id="node-local")

    local_db = {
        "rep-001": {
            "entity_id": "rep-001",
            "timestamp": 100.0,
            "device_clock": 1,
            "description": "Old text",
        }
    }

    incoming_delta = [
        {
            "entity_id": "rep-001",
            "timestamp": 150.0,
            "device_clock": 2,
            "description": "Updated text via peer",
        },
        {
            "entity_id": "rep-002",
            "timestamp": 120.0,
            "device_clock": 1,
            "description": "Brand new report via peer",
        },
    ]

    applied = sync.process_incoming_delta(incoming_delta, local_db)

    assert len(applied) == 2
    assert applied[0]["entity_id"] == "rep-001"
    assert applied[1]["entity_id"] == "rep-002"
