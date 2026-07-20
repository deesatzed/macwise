"""Utilities for freezing independently authored oracle and policy inputs."""

import hashlib
from pathlib import Path


def contract_digest(paths: tuple[Path, ...]) -> str:
    """Return a deterministic SHA-256 digest over named regular contract inputs."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda candidate: candidate.as_posix()):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"contract input is not a regular file: {path}")
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
