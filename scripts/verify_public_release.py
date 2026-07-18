#!/usr/bin/env python3
"""Verify one published MacWise release identity across PyPI and GitHub."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
VERSION_PATTERN = re.compile(r"^1\.0\.0rc[0-9]+$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class VerificationError(RuntimeError):
    """A bounded cross-channel release verification failure."""


def read_local(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise VerificationError(f"Fixture is not a regular file: {path.name}")
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise VerificationError(f"Fixture exceeds the size limit: {path.name}")
    return path.read_bytes()


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "macwise-release-verifier/1"})
    try:
        with urlopen(request, timeout=20) as response:
            data = response.read(MAX_DOCUMENT_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        raise VerificationError(f"Could not fetch required release evidence: {url}") from error
    if len(data) > MAX_DOCUMENT_BYTES:
        raise VerificationError(f"Release evidence exceeds the size limit: {url}")
    return data


def json_object(data: bytes, label: str) -> dict[str, object]:
    try:
        value: object = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VerificationError(f"{label} is not valid JSON.") from error
    if not isinstance(value, dict):
        raise VerificationError(f"{label} is not a JSON object.")
    return cast(dict[str, object], value)


def pypi_digests(document: dict[str, object], version: str) -> dict[str, str]:
    info = document.get("info")
    urls = document.get("urls")
    if not isinstance(info, dict) or not isinstance(urls, list):
        raise VerificationError("PyPI release identity does not match the requested version.")
    typed_info = cast(dict[str, object], info)
    if typed_info.get("version") != version:
        raise VerificationError("PyPI release identity does not match the requested version.")
    result: dict[str, str] = {}
    for raw in cast(list[object], urls):
        if not isinstance(raw, dict):
            continue
        item = cast(dict[str, object], raw)
        digests = item.get("digests")
        filename = item.get("filename")
        typed_digests = cast(dict[str, object], digests) if isinstance(digests, dict) else {}
        digest = typed_digests.get("sha256")
        if (
            isinstance(filename, str)
            and isinstance(digest, str)
            and DIGEST_PATTERN.fullmatch(digest)
        ):
            result[filename] = digest
    return result


def github_assets(document: dict[str, object], version: str) -> tuple[set[str], str | None]:
    if document.get("tag_name") != f"v{version}" or document.get("prerelease") is not True:
        raise VerificationError("GitHub prerelease identity does not match the requested version.")
    assets = document.get("assets")
    if not isinstance(assets, list):
        raise VerificationError("GitHub release assets are missing.")
    names: set[str] = set()
    checksum_url: str | None = None
    for raw in cast(list[object], assets):
        if not isinstance(raw, dict):
            continue
        item = cast(dict[str, object], raw)
        name = item.get("name")
        if isinstance(name, str):
            names.add(name)
            if name == "SHA256SUMS" and isinstance(item.get("browser_download_url"), str):
                checksum_url = cast(str, item["browser_download_url"])
    return names, checksum_url


def checksum_map(data: bytes) -> dict[str, str]:
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise VerificationError("SHA256SUMS is not UTF-8.") from error
    result: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  (?:dist/)?([^/\s]+)", line)
        if match is None or match.group(2) in result:
            raise VerificationError("SHA256SUMS contains an invalid or duplicate entry.")
        result[match.group(2)] = match.group(1)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("--pypi-json", type=Path)
    parser.add_argument("--github-json", type=Path)
    parser.add_argument("--checksums", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    version = cast(str, args.version)
    if VERSION_PATTERN.fullmatch(version) is None:
        raise VerificationError("Version must be an exact 1.0.0 release candidate.")
    fixture_paths = (args.pypi_json, args.github_json, args.checksums)
    local = all(path is not None for path in fixture_paths)
    if any(path is not None for path in fixture_paths) and not local:
        raise VerificationError("Fixture inputs must be supplied together.")

    pypi_data = (
        read_local(cast(Path, args.pypi_json))
        if local
        else fetch(f"https://pypi.org/pypi/macwise/{version}/json")
    )
    github_data = (
        read_local(cast(Path, args.github_json))
        if local
        else fetch(f"https://api.github.com/repos/deesatzed/macwise/releases/tags/v{version}")
    )
    github_document = json_object(github_data, "GitHub release evidence")
    asset_names, checksum_url = github_assets(github_document, version)
    if local:
        checksum_data = read_local(cast(Path, args.checksums))
    else:
        if checksum_url is None:
            raise VerificationError("GitHub release has no downloadable SHA256SUMS asset.")
        checksum_data = fetch(checksum_url)

    sdist = f"macwise-{version}.tar.gz"
    wheel = f"macwise-{version}-py3-none-any.whl"
    expected = (sdist, wheel)
    pypi = pypi_digests(json_object(pypi_data, "PyPI release evidence"), version)
    checksums = checksum_map(checksum_data)
    if not all(name in asset_names for name in (*expected, "SHA256SUMS")):
        raise VerificationError("GitHub release is missing an expected artifact.")
    if any(pypi.get(name) != checksums.get(name) for name in expected):
        raise VerificationError("PyPI and GitHub artifact digests do not match.")
    print(
        json.dumps(
            {
                "artifacts": list(expected),
                "status": "verified",
                "tag": f"v{version}",
                "version": version,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as error:
        print(f"Release verification failed: {error}", file=sys.stderr)
        raise SystemExit(2) from None
