"""Explicit, durable project files (.yadilab) with optimistic concurrency."""
from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path

from .json_boundary import decode_json_document
from .model import ProjectValidationError, validate_project

FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class ProjectConflictError(Exception):
    def __init__(self, actual_hash: str):
        super().__init__("project changed or already exists")
        self.actual_hash = actual_hash


class ProjectStore:
    def __init__(self, directory: Path):
        self.root = Path(directory).expanduser().resolve()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)

    def path(self, slug: str) -> Path:
        if not isinstance(slug, str) or not FILENAME_RE.fullmatch(slug):
            raise ProjectValidationError("filename: expected 1–64 letters, numbers, _ or -; must begin alphanumeric")
        return self.root / (slug + ".yadilab")

    @staticmethod
    def _hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _regular_file_bytes(path: Path) -> bytes | None:
        """Read a regular project inode without following the final symlink.

        O_NONBLOCK prevents a maliciously substituted FIFO from blocking the
        loopback HTTP server before we can reject the non-regular inode.
        The returned bytes come from the opened fd, not a second path lookup.
        """
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
        try:
            fd = os.open(path, flags)
        except FileNotFoundError:
            return None
        except OSError as error:
            if error.errno in (errno.ELOOP, errno.EISDIR, errno.ENXIO, errno.ENODEV):
                raise ProjectValidationError(
                    "project file: symbolic links and special files are forbidden"
                ) from None
            raise
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ProjectValidationError(
                    "project file: expected a regular file, not a link or special file"
                )
            with os.fdopen(fd, "rb") as stream:
                fd = -1  # fdopen owns it; context manager always closes it.
                return stream.read()
        finally:
            if fd >= 0:
                os.close(fd)

    def read(self, slug: str) -> dict:
        path = self.path(slug)
        raw = self._regular_file_bytes(path)
        if raw is None:
            raise FileNotFoundError("project does not exist")
        document = decode_json_document(raw, context="saved project")
        try:
            project = validate_project(document)
        except ProjectValidationError as error:
            if "interface IPv4 cannot be the subnet network or broadcast address" not in str(error):
                raise
            raise ProjectValidationError(
                f"{error}. The saved file was not changed; correct the IPv4 address "
                "explicitly in a copy of the file, then open that copy."
            ) from None
        return {"filename": slug, "sha256": self._hash(raw), "bytes": len(raw), "project": project}

    def list(self) -> list[dict]:
        items = []
        with os.scandir(self.root) as directory:
            for entry in directory:
                if not entry.name.endswith(".yadilab"):
                    continue
                slug = entry.name[:-len(".yadilab")]
                if not FILENAME_RE.fullmatch(slug):
                    continue
                try:
                    metadata = entry.stat(follow_symlinks=False)
                except FileNotFoundError:
                    # A concurrent rename/delete is not a durable project.
                    continue
                if not stat.S_ISREG(metadata.st_mode):
                    continue
                items.append({"filename": slug, "bytes": metadata.st_size,
                              "modifiedAt": metadata.st_mtime})
        return sorted(items, key=lambda item: item["filename"])

    def save(self, slug: str, document: object, expected_sha256: str | None = None) -> dict:
        path = self.path(slug)
        project = validate_project(document)
        if expected_sha256 is not None and (not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)):
            raise ProjectValidationError("expectedSha256: must be a SHA-256 string or null")
        # The lock file is never replaced: its regular inode remains a
        # stable flock target while the project file is atomically renamed.
        # Reject substituted symlinks/directories/FIFOs before taking a lock
        # or touching the user project; FIFOs must never block on open.
        try:
            lock_fd = os.open(self.root / f".lock-{slug}",
                              os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW |
                              os.O_NONBLOCK | os.O_CLOEXEC, 0o600)
        except OSError as error:
            if error.errno in (errno.ELOOP, errno.EISDIR, errno.ENXIO, errno.ENODEV):
                raise ProjectValidationError(
                    "project lock: expected a regular file, not a link or special file"
                ) from None
            raise
        try:
            if not stat.S_ISREG(os.fstat(lock_fd).st_mode):
                raise ProjectValidationError(
                    "project lock: expected a regular file, not a link or special file")
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            try:
                existing = self._regular_file_bytes(path)
                actual = self._hash(existing) if existing is not None else ""
                # No expected hash means create-only; an explicit matching
                # hash means intentional overwrite of the loaded version.
                if existing is not None and expected_sha256 != actual:
                    raise ProjectConflictError(actual)
                if existing is None and expected_sha256 is not None:
                    raise ProjectConflictError("")
                data = (json.dumps(project, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
                fd, temp_name = tempfile.mkstemp(prefix=".pending-", suffix=".tmp", dir=self.root)
                try:
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temp_name, path)
                    # The directory fsync makes the rename durable on Linux.
                    dfd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(dfd)
                    finally:
                        os.close(dfd)
                finally:
                    if os.path.exists(temp_name):
                        os.unlink(temp_name)
                return {"filename": slug, "sha256": self._hash(data), "bytes": len(data), "project": project}
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)
