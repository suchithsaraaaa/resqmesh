import os
import sys
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from backend.app.database import Base, get_db
    from backend.app.main import app
    from backend.app.models import OperationalIncident, Attachment
    from backend.app.services.storage_service import (
        save_attachment_file,
        compute_sha256,
        sanitize_filename,
        find_attachment_file_by_hash,
    )
except ImportError:
    from app.database import Base, get_db
    from app.main import app
    from app.models import OperationalIncident, Attachment
    from app.services.storage_service import (
        save_attachment_file,
        compute_sha256,
        sanitize_filename,
        find_attachment_file_by_hash,
    )

from sqlalchemy.pool import StaticPool

# Test In-Memory Database
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_storage_service_deduplication(tmp_path, monkeypatch):
    """Test that identical file content uses the same hash and reuses the existing file."""
    monkeypatch.setenv("RESQMESH_ATTACHMENTS_DIR", str(tmp_path))

    content = b"Simulated image binary payload 12345"
    expected_hash = compute_sha256(content)

    hash1, path1, size1 = save_attachment_file(content, "photo1.jpg", "image/jpeg")
    assert hash1 == expected_hash
    assert size1 == len(content)

    # Save identical content with a different filename
    hash2, path2, size2 = save_attachment_file(content, "photo2_copy.png", "image/png")
    assert hash2 == expected_hash
    assert hash1 == hash2


def test_sanitize_filename():
    """Verify directory traversal patterns are removed from uploaded filenames."""
    assert sanitize_filename("../../../etc/passwd.jpg") == "passwd.jpg"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe.png") == "cmd.exe.png"
    assert sanitize_filename("safe_field_photo.jpeg") == "safe_field_photo.jpeg"


def test_attachment_api_lifecycle(client, tmp_path, monkeypatch):
    """Test complete API lifecycle: upload, metadata query, streaming file, and hash download."""
    monkeypatch.setenv("RESQMESH_ATTACHMENTS_DIR", str(tmp_path))

    # 1. Create an operational incident
    inc_resp = client.post(
        "/incidents/",
        json={
            "title": "Bridge Structural Fracture",
            "category": "structural",
            "severity": "critical",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "broadcaster_name": "Field-Alpha",
        }
    )
    assert inc_resp.status_code == 201
    inc_data = inc_resp.json()
    incident_id = inc_data["incident_id"]

    # 2. Upload two photo attachments
    file1_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtestimage1"
    file2_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00testimage2"

    upload_resp = client.post(
        f"/incidents/{incident_id}/attachments",
        files=[
            ("files", ("crack_overview.png", io.BytesIO(file1_bytes), "image/png")),
            ("files", ("pillar_zoom.jpg", io.BytesIO(file2_bytes), "image/jpeg")),
        ]
    )
    assert upload_resp.status_code == 201
    attachments = upload_resp.json()
    assert len(attachments) == 2
    att1 = attachments[0]
    att2 = attachments[1]

    assert att1["incident_id"] == incident_id
    assert att1["filename"] == "crack_overview.png"
    assert att1["mime_type"] == "image/png"
    assert att1["sha256_hash"] == compute_sha256(file1_bytes)

    assert att2["filename"] == "pillar_zoom.jpg"
    assert att2["mime_type"] == "image/jpeg"
    assert att2["sha256_hash"] == compute_sha256(file2_bytes)

    # 3. Query attachments for the incident
    list_resp = client.get(f"/incidents/{incident_id}/attachments")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert len(listed) == 2

    # 4. Stream binary file by attachment ID
    stream_resp = client.get(f"/attachments/{att1['id']}/file")
    assert stream_resp.status_code == 200
    assert stream_resp.content == file1_bytes

    # 5. Download binary file by SHA-256 hash (mesh peer sync)
    hash_resp = client.get(f"/attachments/download/{att2['sha256_hash']}")
    assert hash_resp.status_code == 200
    assert hash_resp.content == file2_bytes


def test_upload_to_nonexistent_incident(client):
    """Uploading attachments to an invalid incident ID should return 404."""
    resp = client.post(
        "/incidents/invalid-nonexistent-id/attachments",
        files=[("files", ("test.jpg", io.BytesIO(b"data"), "image/jpeg"))]
    )
    assert resp.status_code == 404


def test_attachment_mesh_sync_success(tmp_path, monkeypatch):
    """Test out-of-band P2P attachment synchronization and SHA-256 verification."""
    monkeypatch.setenv("RESQMESH_ATTACHMENTS_DIR", str(tmp_path))
    from unittest.mock import patch, MagicMock

    try:
        from backend.app.sync.attachment_sync import AttachmentSyncManager
    except ImportError:
        from app.sync.attachment_sync import AttachmentSyncManager

    db = TestingSessionLocal()
    try:
        # Create incident on Node B
        inc = OperationalIncident(
            incident_id="inc-sync-001",
            title="Flooded Tunnel",
            category="flood",
            severity="high",
        )
        db.add(inc)

        # Node B receives event metadata with missing binary
        test_content = b"High-res camera photo from responder squad alpha"
        test_hash = compute_sha256(test_content)
        att = Attachment(
            id="att-sync-001",
            incident_id="inc-sync-001",
            filename="tunnel_entry.jpg",
            mime_type="image/jpeg",
            file_size=len(test_content),
            sha256_hash=test_hash,
            local_path="",
            source_node_id="peer-node-alpha",
            sync_status="pending",
        )
        db.add(att)
        db.commit()

        # Mock remote peer download returning the binary data
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = test_content
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            res = AttachmentSyncManager.sync_pending_attachments("http://192.168.1.105:8000", db)

        assert res["synced"] == 1
        assert res["failed"] == 0

        # Verify DB state updated to synced
        db.refresh(att)
        assert att.sync_status == "synced"
        assert os.path.exists(att.local_path)
        with open(att.local_path, "rb") as f:
            assert f.read() == test_content
    finally:
        db.close()


def test_attachment_mesh_sync_local_deduplication(tmp_path, monkeypatch):
    """Test that existing local files are deduplicated without re-downloading."""
    monkeypatch.setenv("RESQMESH_ATTACHMENTS_DIR", str(tmp_path))

    try:
        from backend.app.sync.attachment_sync import AttachmentSyncManager
    except ImportError:
        from app.sync.attachment_sync import AttachmentSyncManager

    db = TestingSessionLocal()
    try:
        content = b"Shared map diagram"
        test_hash, local_path, _ = save_attachment_file(content, "map.png", "image/png")

        inc = OperationalIncident(
            incident_id="inc-sync-002",
            title="Chemical Leak",
            category="chemical",
            severity="critical",
        )
        db.add(inc)

        # New attachment pointing to the same hash
        att = Attachment(
            id="att-sync-002",
            incident_id="inc-sync-002",
            filename="site_map.png",
            mime_type="image/png",
            file_size=len(content),
            sha256_hash=test_hash,
            local_path="",
            source_node_id="peer-beta",
            sync_status="pending",
        )
        db.add(att)
        db.commit()

        # Sync should deduplicate without making any network calls
        res = AttachmentSyncManager.sync_pending_attachments("http://192.168.1.110:8000", db)
        assert res["deduplicated"] == 1
        assert res["synced"] == 0

        db.refresh(att)
        assert att.sync_status == "synced"
        assert att.local_path == local_path
    finally:
        db.close()


def test_attachment_mesh_sync_corrupted_hash(tmp_path, monkeypatch):
    """Test that corrupted payloads that fail SHA-256 checksum are rejected."""
    monkeypatch.setenv("RESQMESH_ATTACHMENTS_DIR", str(tmp_path))
    from unittest.mock import patch, MagicMock

    try:
        from backend.app.sync.attachment_sync import AttachmentSyncManager
    except ImportError:
        from app.sync.attachment_sync import AttachmentSyncManager

    db = TestingSessionLocal()
    try:
        inc = OperationalIncident(
            incident_id="inc-sync-003",
            title="Forest Fire Smoke",
            category="fire",
            severity="medium",
        )
        db.add(inc)

        expected_hash = compute_sha256(b"Original valid photo")
        att = Attachment(
            id="att-sync-003",
            incident_id="inc-sync-003",
            filename="smoke.jpg",
            mime_type="image/jpeg",
            file_size=100,
            sha256_hash=expected_hash,
            local_path="",
            source_node_id="peer-gamma",
            sync_status="pending",
        )
        db.add(att)
        db.commit()

        # Remote peer returns corrupted bytes
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"Corrupted packet bits"
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            res = AttachmentSyncManager.sync_pending_attachments("http://192.168.1.115:8000", db)

        assert res["failed"] == 1
        assert res["synced"] == 0

        db.refresh(att)
        assert att.sync_status == "failed"
    finally:
        db.close()

