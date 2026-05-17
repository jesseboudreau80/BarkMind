"""
Storage abstraction layer for BarkMind media.

MVP: LocalStorage only.
Future: S3Storage (Cloudflare R2 / AWS S3) via MEDIA_BACKEND=s3.
"""
from __future__ import annotations

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import settings


class StorageBackend(ABC):
    """Abstract interface for all storage backends."""

    @abstractmethod
    def write_stream(self, rel_path: str, data: bytes) -> None:
        """Write raw bytes to the given relative path."""

    @abstractmethod
    def delete(self, rel_path: str) -> None:
        """Delete a file. No-op if it does not exist."""

    @abstractmethod
    def exists(self, rel_path: str) -> bool:
        """Return True if the path exists."""

    @abstractmethod
    def url(self, rel_path: str) -> str:
        """Return a URL that resolves to this path for the API client."""

    @abstractmethod
    def absolute_path(self, rel_path: str) -> Path:
        """Resolve rel_path to an absolute filesystem path (local backends only)."""

    def makedirs(self, rel_dir: str) -> None:
        """Ensure directory exists (local backends only — S3 is a flat namespace)."""
        self.absolute_path(rel_dir).mkdir(parents=True, exist_ok=True)


class LocalStorage(StorageBackend):
    """Stores media on local disk under a configured root directory."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def write_stream(self, rel_path: str, data: bytes) -> None:
        dest = self._safe_resolve(rel_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    def delete(self, rel_path: str) -> None:
        path = self._safe_resolve(rel_path)
        if path.exists():
            path.unlink()

    def exists(self, rel_path: str) -> bool:
        return self._safe_resolve(rel_path).exists()

    def url(self, rel_path: str) -> str:
        return f"/media/{rel_path}"

    def absolute_path(self, rel_path: str) -> Path:
        return self._safe_resolve(rel_path)

    def _safe_resolve(self, rel_path: str) -> Path:
        """Resolve relative path, guarding against directory traversal."""
        resolved = (self.root / rel_path).resolve()
        if not str(resolved).startswith(str(self.root)):
            raise ValueError(f"Directory traversal attempt detected: {rel_path!r}")
        return resolved

    def list_all_files(self) -> list[str]:
        """Return all stored file paths relative to root (for cleanup audit)."""
        result = []
        for p in self.root.rglob("*"):
            if p.is_file():
                result.append(str(p.relative_to(self.root)))
        return result


class S3Storage(StorageBackend):
    """Stub for future S3/R2 implementation.

    Set MEDIA_BACKEND=s3 when ready to implement.
    """

    def write_stream(self, rel_path: str, data: bytes) -> None:
        raise NotImplementedError("S3 storage not yet implemented. Use MEDIA_BACKEND=local.")

    def delete(self, rel_path: str) -> None:
        raise NotImplementedError

    def exists(self, rel_path: str) -> bool:
        raise NotImplementedError

    def url(self, rel_path: str) -> str:
        raise NotImplementedError

    def absolute_path(self, rel_path: str) -> Path:
        raise NotImplementedError("S3 storage has no local filesystem path.")

    def makedirs(self, rel_dir: str) -> None:
        pass  # S3 is a flat namespace — no-op


def get_storage() -> StorageBackend:
    """Return the configured storage backend singleton."""
    backend = settings.media_backend.lower()
    if backend == "s3":
        raise NotImplementedError(
            "S3 storage is not yet implemented. Set MEDIA_BACKEND=local."
        )
    # local
    root = Path(settings.media_root)
    if not root.is_absolute():
        # Relative to the project root (one level above backend/)
        root = Path(__file__).parent.parent.parent.parent / settings.media_root
    return LocalStorage(root)


# Canonical sub-directory names within a case's media folder
def case_original_dir(case_id: str) -> str:
    return f"cases/{case_id}/original"


def case_thumbnails_dir(case_id: str) -> str:
    return f"cases/{case_id}/thumbnails"


def case_derived_dir(case_id: str) -> str:
    """For future processed variants (not yet used)."""
    return f"cases/{case_id}/derived"


def case_frames_dir(case_id: str) -> str:
    """For future frame-extraction pipeline (AI Phase 3+)."""
    return f"cases/{case_id}/frames"


def ensure_case_dirs(storage: StorageBackend, case_id: str) -> None:
    """Pre-create the full directory tree for a case."""
    for dir_fn in (
        case_original_dir,
        case_thumbnails_dir,
        case_derived_dir,
        case_frames_dir,
    ):
        storage.makedirs(dir_fn(case_id))
