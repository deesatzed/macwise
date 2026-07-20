#!/usr/bin/env python3
"""Write or verify the digest for frozen evaluator-contract inputs."""

import argparse
import os
import sys
import tempfile
from pathlib import Path

from macwise_eval.oracle import contract_digest


def parse_args() -> argparse.Namespace:
    """Parse the explicit write/check command shape."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", type=Path, metavar="LOCK")
    mode.add_argument("--check", type=Path, metavar="LOCK")
    parser.add_argument("inputs", nargs="+", type=Path, metavar="INPUT")
    return parser.parse_args()


def write_lock(path: Path, digest: str) -> None:
    """Atomically write one digest without following an existing symlink."""
    if path.is_symlink():
        raise ValueError("contract lock must not be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".contract-", dir=path.parent, text=True)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(f"{digest}\n")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def read_lock(path: Path) -> str:
    """Read one exact digest from a regular lock file."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("contract lock must be a regular file")
    value = path.read_text(encoding="utf-8")
    if len(value) != 65 or not value.endswith("\n"):
        raise ValueError("contract lock has invalid content")
    digest = value[:-1]
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("contract lock has invalid digest")
    return digest


def main() -> int:
    """Write or verify the frozen contract digest."""
    args = parse_args()
    digest = contract_digest(tuple(args.inputs))
    if args.write is not None:
        write_lock(args.write, digest)
        print(f"wrote contract digest: {digest}")
        return 0

    expected = read_lock(args.check)
    if expected != digest:
        print(
            "contract digest differs; review the evaluator contract before replacing its lock",
            file=sys.stderr,
        )
        return 2
    print(f"contract digest verified: {digest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"contract verification failed: {error}", file=sys.stderr)
        raise SystemExit(2) from None
