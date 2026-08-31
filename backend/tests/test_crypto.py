import json
import pytest
from backend.app.crypto.security import (
    DeviceKeyPair,
    verify_signature,
    SymmetricCipher,
    TrustStore,
)


def test_ed25519_key_generation_and_signing():
    device_keys = DeviceKeyPair()
    pub_b64 = device_keys.get_public_key_b64()
    assert len(pub_b64) > 0

    message_bytes = b"ResQMesh Emergency Alert Packet #991"
    signature_b64 = device_keys.sign(message_bytes)
    assert len(signature_b64) > 0

    # Verification with correct key & message
    is_valid = verify_signature(pub_b64, message_bytes, signature_b64)
    assert is_valid is True

    # Verification with tampered message
    is_tampered_valid = verify_signature(pub_b64, b"Tampered Message", signature_b64)
    assert is_tampered_valid is False

    # Verification with wrong public key
    other_device = DeviceKeyPair()
    is_wrong_key_valid = verify_signature(
        other_device.get_public_key_b64(), message_bytes, signature_b64
    )
    assert is_wrong_key_valid is False


def test_symmetric_aes_gcm_encryption_decryption():
    key = SymmetricCipher.generate_key()
    assert len(key) == 32  # 256 bits

    secret_message = "Command Center coordinates: Lat 12.9716, Lon 77.5946"
    encrypted = SymmetricCipher.encrypt(key, secret_message)

    assert "ciphertext" in encrypted
    assert "nonce" in encrypted

    # Successful decryption
    decrypted = SymmetricCipher.decrypt(
        key, encrypted["ciphertext"], encrypted["nonce"]
    )
    assert decrypted == secret_message

    # Decryption with wrong key fails gracefully
    wrong_key = SymmetricCipher.generate_key()
    decrypted_wrong = SymmetricCipher.decrypt(
        wrong_key, encrypted["ciphertext"], encrypted["nonce"]
    )
    assert decrypted_wrong is None


def test_qr_trust_bootstrapping():
    trust_store = TrustStore()
    assert trust_store.is_peer_trusted("device-alpha") is False

    dev_alpha = DeviceKeyPair()
    qr_payload = dev_alpha.generate_qr_bootstrap_payload(
        device_id="device-alpha", role="commander"
    )

    success = trust_store.bootstrap_from_qr_payload(qr_payload)
    assert success is True
    assert trust_store.is_peer_trusted("device-alpha") is True

    stored_pubkey = trust_store.get_peer_public_key("device-alpha")
    assert stored_pubkey == dev_alpha.get_public_key_b64()

    # Invalid QR payload rejection
    invalid_qr = json.dumps({"protocol": "other", "data": "invalid"})
    assert trust_store.bootstrap_from_qr_payload(invalid_qr) is False
