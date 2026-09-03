import os
import json
import base64
import time
import logging
from typing import Dict, Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("ResQMesh.Security")


class DeviceKeyPair:
    """Ed25519 Device Key Pair for asymmetric device authentication and digital signing."""

    def __init__(self, private_key: Optional[ed25519.Ed25519PrivateKey] = None):
        self._private_key = private_key or ed25519.Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()

    def get_public_key_bytes(self) -> bytes:
        from cryptography.hazmat.primitives import serialization
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def get_public_key_b64(self) -> str:
        return base64.b64encode(self.get_public_key_bytes()).decode("utf-8")

    def get_private_key_bytes(self) -> bytes:
        from cryptography.hazmat.primitives import serialization
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def get_private_key_b64(self) -> str:
        return base64.b64encode(self.get_private_key_bytes()).decode("utf-8")

    @classmethod
    def from_private_key_b64(cls, priv_b64: str) -> "DeviceKeyPair":
        """Recreate DeviceKeyPair from base64 raw private key bytes."""
        try:
            priv_bytes = base64.b64decode(priv_b64)
            priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
            return cls(private_key=priv_key)
        except Exception as e:
            logger.warning(f"Failed to deserialize private key: {e}. Generating new key.")
            return cls()

    def sign(self, data: bytes) -> str:
        """Sign binary payload and return base64-encoded signature."""
        sig = self._private_key.sign(data)
        return base64.b64encode(sig).decode("utf-8")

    def generate_qr_bootstrap_payload(self, device_id: str, role: str = "responder") -> str:
        """Generate JSON string for QR Code Trust Bootstrapping."""
        payload = {
            "version": "1.0",
            "protocol": "resqmesh-auth",
            "device_id": device_id,
            "role": role,
            "public_key": self.get_public_key_b64(),
            "timestamp": time.time(),
        }
        return json.dumps(payload)


def verify_signature(public_key_b64: str, data: bytes, signature_b64: str) -> bool:
    """Verify Ed25519 signature of payload bytes."""
    try:
        pub_bytes = base64.b64decode(public_key_b64)
        sig_bytes = base64.b64decode(signature_b64)
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        pub_key.verify(sig_bytes, data)
        return True
    except Exception as e:
        logger.debug(f"Signature verification failed: {e}")
        return False


class SymmetricCipher:
    """AES-256-GCM authenticated symmetric encryption for sensitive mesh payload channels."""

    @staticmethod
    def generate_key() -> bytes:
        """Generate 256-bit (32 bytes) random encryption key."""
        return AESGCM.generate_key(bit_length=256)

    @staticmethod
    def encrypt(key_bytes: bytes, plaintext: str) -> Dict[str, str]:
        """
        Encrypt plaintext string using AES-256-GCM.
        Returns dict with base64 ciphertext and nonce.
        """
        aesgcm = AESGCM(key_bytes)
        nonce = os.urandom(12)  # 96-bit nonce
        data_bytes = plaintext.encode("utf-8")
        ciphertext_with_tag = aesgcm.encrypt(nonce, data_bytes, None)

        return {
            "ciphertext": base64.b64encode(ciphertext_with_tag).decode("utf-8"),
            "nonce": base64.b64encode(nonce).decode("utf-8"),
        }

    @staticmethod
    def decrypt(key_bytes: bytes, ciphertext_b64: str, nonce_b64: str) -> Optional[str]:
        """Decrypt AES-256-GCM ciphertext."""
        try:
            aesgcm = AESGCM(key_bytes)
            nonce = base64.b64decode(nonce_b64)
            ciphertext = base64.b64decode(ciphertext_b64)
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"AES-GCM decryption failed: {e}")
            return None


class TrustStore:
    """Registry of verified peer public keys and QR-bootstrapped device certificates."""

    def __init__(self):
        self.trusted_peers: Dict[str, dict] = {}

    def add_trusted_peer(
        self, device_id: str, public_key_b64: str, role: str = "responder", verified_via_qr: bool = False
    ) -> None:
        self.trusted_peers[device_id] = {
            "device_id": device_id,
            "public_key": public_key_b64,
            "role": role,
            "verified_via_qr": verified_via_qr,
            "added_at": time.time(),
        }
        logger.info(f"Added trusted peer: {device_id} ({role}) [QR: {verified_via_qr}]")

    def is_peer_trusted(self, device_id: str) -> bool:
        return device_id in self.trusted_peers

    def get_peer_public_key(self, device_id: str) -> Optional[str]:
        peer = self.trusted_peers.get(device_id)
        return peer.get("public_key") if peer else None

    def bootstrap_from_qr_payload(self, qr_json_str: str) -> bool:
        """Parse scanned QR Code payload and record trusted peer certificate."""
        try:
            data = json.loads(qr_json_str)
            if data.get("protocol") != "resqmesh-auth":
                return False

            device_id = data["device_id"]
            public_key = data["public_key"]
            role = data.get("role", "responder")

            self.add_trusted_peer(
                device_id=device_id,
                public_key_b64=public_key,
                role=role,
                verified_via_qr=True,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to bootstrap trust from QR code: {e}")
            return False
