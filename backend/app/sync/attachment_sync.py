import os
import urllib.request
import urllib.error
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List

try:
    from backend.app.models import Attachment
    from backend.app.services.storage_service import (
        save_attachment_file,
        find_attachment_file_by_hash,
        compute_sha256,
    )
except ImportError:
    from app.models import Attachment
    from app.services.storage_service import (
        save_attachment_file,
        find_attachment_file_by_hash,
        compute_sha256,
    )

logger = logging.getLogger("ResQMesh.AttachmentSync")


class AttachmentSyncManager:
    """
    Manages peer-to-peer out-of-band transfer of binary attachments.
    Ensures:
    1. Lightweight mesh event logs (metadata only).
    2. Pull-on-demand transfer of missing binaries by SHA-256 hash.
    3. Content deduplication: reuses existing local files when available.
    4. Cryptographic integrity: validates SHA-256 prior to committing to local store.
    """

    @staticmethod
    def sync_pending_attachments(peer_url: str, db) -> Dict[str, Any]:
        """
        Scan for attachments with sync_status='pending' and pull missing binaries
        from the specified remote peer URL over HTTP.
        """
        pending_attachments: List[Attachment] = (
            db.query(Attachment)
            .filter_by(sync_status="pending")
            .all()
        )

        if not pending_attachments:
            return {"synced": 0, "deduplicated": 0, "failed": 0}

        synced_count = 0
        deduplicated_count = 0
        failed_count = 0

        clean_peer_url = peer_url.rstrip("/")

        for att in pending_attachments:
            # 1. Local Deduplication Check: Check if we already have this SHA-256 on disk
            existing_local = find_attachment_file_by_hash(att.sha256_hash)
            if existing_local and existing_local.exists() and existing_local.stat().st_size > 0:
                att.local_path = str(existing_local)
                att.sync_status = "synced"
                db.commit()
                deduplicated_count += 1
                logger.info(f"Local deduplication: attachment '{att.filename}' reused hash {att.sha256_hash[:8]}")
                continue

            # 2. Out-of-Band HTTP Retrieval by SHA-256 Hash
            download_url = f"{clean_peer_url}/attachments/download/{att.sha256_hash}"
            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": "ResQMesh-P2P-Sync/1.0"},
                method="GET",
            )

            try:
                with urllib.request.urlopen(req, timeout=15.0) as response:
                    if response.status == 200:
                        binary_data = response.read()
                        if not binary_data:
                            failed_count += 1
                            continue

                        # 3. Cryptographic Verification: Verify SHA-256 checksum matches metadata
                        calculated_hash = compute_sha256(binary_data)
                        if calculated_hash.lower() != att.sha256_hash.lower():
                            logger.error(
                                f"Corrupted transfer for {att.filename}: expected hash {att.sha256_hash}, got {calculated_hash}"
                            )
                            att.sync_status = "failed"
                            db.commit()
                            failed_count += 1
                            continue

                        # 4. Atomic Write to Content-Addressed Local Store
                        sha256_hash, local_path, file_size = save_attachment_file(
                            content=binary_data,
                            original_filename=att.filename,
                            mime_type=att.mime_type,
                        )

                        att.local_path = local_path
                        att.file_size = file_size
                        att.sync_status = "synced"
                        db.commit()
                        synced_count += 1
                        logger.info(
                            f"Successfully synced attachment '{att.filename}' ({file_size} bytes, {sha256_hash[:8]}) from {clean_peer_url}"
                        )
                    else:
                        failed_count += 1
            except urllib.error.HTTPError as he:
                # Peer might not have this file yet (e.g. 404); remain pending for future attempts
                if he.code != 404:
                    logger.debug(f"HTTP error downloading attachment {att.sha256_hash[:8]} from {clean_peer_url}: {he}")
                failed_count += 1
            except Exception as ex:
                logger.debug(f"Network error downloading attachment {att.sha256_hash[:8]} from {clean_peer_url}: {ex}")
                failed_count += 1

        return {
            "synced": synced_count,
            "deduplicated": deduplicated_count,
            "failed": failed_count,
        }
