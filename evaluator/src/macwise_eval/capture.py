"""Private local capture of independently collected evaluation reference receipts."""

import platform
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from macwise_eval.io import canonical_json, receipt_digest
from macwise_eval.models import (
    CapsuleManifest,
    CorpusRole,
    DisclosureClass,
    EnvironmentIdentity,
    ProvenanceClass,
    Receipt,
    ScenarioOracle,
    ToolVersion,
)
from macwise_eval.reference.capture import (
    CommandRunner,
    ReferenceObservation,
    collect_reference_observations,
)
from macwise_eval.system import FixedCommandRunner


@dataclass(frozen=True)
class CaptureResult:
    """Safe aggregate result returned after writing a private capsule."""

    capsule_id: str
    observation_count: int


def _empty_private_directory(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("private output directory must not be a symlink")
    if path.exists():
        if not path.is_dir() or any(path.iterdir()):
            raise ValueError("private output directory must be empty")
    else:
        path.mkdir(parents=True)


def _environment() -> EnvironmentIdentity:
    macos_version = platform.mac_ver()[0] or "unknown"
    return EnvironmentIdentity(
        macos_product_version=macos_version,
        macos_build="unknown",
        darwin_version=platform.release() or "unknown",
        architecture=platform.machine() or "unknown",
        tools=(ToolVersion(name="python", version=platform.python_version()),),
    )


def _write_observation(path: Path, observation: ReferenceObservation) -> None:
    path.write_text(
        canonical_json(
            {
                "document": dict(observation.document),
                "limitations": observation.limitations,
                "source": observation.source,
                "source_correlated": observation.source_correlated,
            }
        ),
        encoding="utf-8",
    )


def capture_private_capsule(
    output_dir: Path,
    *,
    runner: CommandRunner | None = None,
    app_roots: tuple[Path, ...] | None = None,
) -> CaptureResult:
    """Collect local read-only evidence into an ignored explicit private output directory."""
    _empty_private_directory(output_dir)
    effective_runner = runner or FixedCommandRunner(
        timeout_seconds=10, max_output_bytes=1024 * 1024
    )
    effective_roots = app_roots or (Path("/Applications"), Path.home() / "Applications")
    observations = collect_reference_observations(effective_runner, app_roots=effective_roots)
    reference_directory = output_dir / "reference"
    reference_directory.mkdir()
    receipts: list[Receipt] = []
    for name, observation in observations.items():
        path = reference_directory / f"{name}.json"
        _write_observation(path, observation)
        receipts.append(
            Receipt(
                receipt_id=f"reference-{name}",
                relative_path=path.relative_to(output_dir).as_posix(),
                sha256=receipt_digest(path),
                source=observation.source,
                collected_at=datetime.now(UTC),
                source_correlated=observation.source_correlated,
            )
        )
    captured_at = datetime.now(UTC)
    capsule_id = f"live-private-{captured_at.strftime('%Y%m%d%H%M%S')}"
    manifest = CapsuleManifest(
        capsule_id=capsule_id,
        provenance=ProvenanceClass.LIVE_PRIVATE,
        disclosure=DisclosureClass.PRIVATE,
        corpus_role=CorpusRole.FRESH_HOLDOUT,
        captured_at=captured_at,
        environment=_environment(),
        macwise_version="unrecorded",
        audit_schema_version=4,
        receipts=tuple(receipts),
        oracle_version="unassigned",
        limitations=(
            "This private reference capture must be paired with close-in-time product output.",
            "macOS build is unknown until the reference environment collector records it.",
        ),
        reviewed_sanitized=False,
    )
    oracle = ScenarioOracle(
        scenario_id=capsule_id,
        version="unassigned",
        limitations=("No public scenario oracle has been assigned to this private holdout.",),
    )
    (output_dir / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")
    (output_dir / "oracle.json").write_text(canonical_json(oracle), encoding="utf-8")
    return CaptureResult(capsule_id=capsule_id, observation_count=len(observations))
