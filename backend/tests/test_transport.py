import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.app.models
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.crypto.security import DeviceKeyPair
from backend.app.network.transport import HandshakeManager, PeerConnection

# Isolated test DB for handshake endpoint
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_handshake_crypto_mutual_authentication():
    """Verify mutual Ed25519 challenge-response handshake between two nodes."""
    node_a_id = "NODE-LAPTOP-ALPHA"
    keypair_a = DeviceKeyPair()

    node_b_id = "NODE-LAPTOP-BETA"
    keypair_b = DeviceKeyPair()

    # Step 1: Node A creates SYN challenge
    syn = HandshakeManager.create_syn(node_a_id, "commander", keypair_a)
    assert syn["type"] == "HANDSHAKE_SYN"
    assert syn["node_id"] == node_a_id
    assert "signature" in syn

    # Step 2: Node B verifies SYN and creates ACK
    valid_syn, ack = HandshakeManager.verify_syn_and_create_ack(syn, node_b_id, keypair_b)
    assert valid_syn is True
    assert ack is not None
    assert ack["type"] == "HANDSHAKE_ACK"
    assert ack["node_id"] == node_b_id
    assert ack["echo_nonce"] == syn["nonce"]

    # Step 3: Node A verifies ACK
    valid_ack = HandshakeManager.verify_ack(ack, syn["nonce"])
    assert valid_ack is True


def test_handshake_tamper_rejection():
    """Verify that a tampered handshake challenge is immediately rejected."""
    keypair_a = DeviceKeyPair()
    keypair_b = DeviceKeyPair()

    syn = HandshakeManager.create_syn("NODE-ALPHA", "commander", keypair_a)

    # Tamper with node_id in flight
    syn["node_id"] = "NODE-IMPERSONATOR"

    valid, ack = HandshakeManager.verify_syn_and_create_ack(syn, "NODE-BETA", keypair_b)
    assert valid is False
    assert ack is None


def test_handshake_http_endpoint():
    """Verify /handshake endpoint processes valid challenge and returns signed ACK."""
    remote_keypair = DeviceKeyPair()
    syn = HandshakeManager.create_syn("NODE-REMOTE-CLIENT", "responder", remote_keypair)

    resp = client.post("/handshake", json=syn)
    assert resp.status_code == 200
    ack = resp.json()
    assert ack["type"] == "HANDSHAKE_ACK"
    assert ack["echo_nonce"] == syn["nonce"]

    # Verify ACK signature
    assert HandshakeManager.verify_ack(ack, syn["nonce"]) is True
