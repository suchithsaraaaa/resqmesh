import os
import sys
import hashlib
from pathlib import Path
from typing import Tuple, Optional

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def get_attachments_dir() -> Path:
    """Return platform-appropriate local storage directory for attachments."""
    override = os.environ.get("RESQMESH_ATTACHMENTS_DIR")
    if override:
        base_dir = Path(override)
    elif sys.platform == "win32":
        app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if app_data:
            base_dir = Path(app_data) / "ResQMesh AI" / "attachments"
        else:
            base_dir = Path.home() / ".resqmesh" / "attachments"
    else:
        base_dir = Path.home() / ".resqmesh" / "attachments"

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def compute_sha256(content: bytes) -> str:
    """Compute SHA-256 checksum hex digest of binary content."""
    return hashlib.sha256(content).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and invalid characters."""
    base = os.path.basename(filename)
    clean = "".join(c for c in base if c.isalnum() or c in "._- ")
    return clean or "unnamed_image.jpg"


def get_extension_from_name_or_mime(filename: str, mime_type: Optional[str] = None) -> str:
    """Extract and validate normalized file extension."""
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_EXTENSIONS:
        return ext
    if mime_type and mime_type.lower() in ALLOWED_MIME_TYPES:
        return ALLOWED_MIME_TYPES[mime_type.lower()]
    return ".jpg"


def save_attachment_file(content: bytes, original_filename: str, mime_type: Optional[str] = None) -> Tuple[str, str, int]:
    """
    Save attachment to content-addressed storage using SHA-256 hash.
    Performs automatic deduplication: if identical file content already exists on disk,
    the existing path is reused without rewriting.
    Returns: (sha256_hash, local_path, file_size)
    """
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size ({len(content)} bytes) exceeds 10MB limit.")

    sha256_hash = compute_sha256(content)
    ext = get_extension_from_name_or_mime(original_filename, mime_type)
    target_filename = f"{sha256_hash}{ext}"

    storage_dir = get_attachments_dir()
    target_path = storage_dir / target_filename

    # Content deduplication: if file already exists and size matches, reuse it
    if target_path.exists() and target_path.stat().st_size == len(content):
        return sha256_hash, str(target_path), len(content)

    with open(target_path, "wb") as f:
        f.write(content)

    return sha256_hash, str(target_path), len(content)


def find_attachment_file_by_hash(sha256_hash: str) -> Optional[Path]:
    """Locate stored attachment file by its SHA-256 hash regardless of extension."""
    clean_hash = "".join(c for c in sha256_hash if c.isalnum()).lower()
    if len(clean_hash) != 64:
        return None

    storage_dir = get_attachments_dir()
    for ext in ALLOWED_EXTENSIONS:
        candidate = storage_dir / f"{clean_hash}{ext}"
        if candidate.exists() and candidate.is_file():
            return candidate

    # Search for any file prefixed with the hash
    matches = list(storage_dir.glob(f"{clean_hash}.*"))
    if matches and matches[0].is_file():
        return matches[0]

    return None
