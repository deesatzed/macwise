#!/usr/bin/env python3
"""Generate sanitized product-side JSON fixtures for evaluator parser tests."""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from macwise.models import (
    AuditDocument,
    CollectorState,
    CollectorStatus,
    EntityType,
    SoftwareRecord,
    StorageLocation,
    VolumeRecord,
    stable_software_id,
)
from macwise.models.checkup import CheckupPriority, CheckupSummary
from macwise.reporting.json_report import render_json


def parse_args() -> argparse.Namespace:
    """Require one explicit output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def ensure_empty_output_directory(path: Path) -> None:
    """Create an explicit destination only when it is empty and not a symlink."""
    if path.is_symlink():
        raise ValueError("output directory must not be a symlink")
    if path.exists():
        if not path.is_dir() or any(path.iterdir()):
            raise ValueError("output directory must be empty")
    else:
        path.mkdir(parents=True)


def build_audit(collected_at: datetime) -> AuditDocument:
    """Construct a small synthetic audit using production serialization only."""
    return AuditDocument(
        audit_id="audit:evaluation-fixture",
        collected_at=collected_at,
        software=(
            SoftwareRecord(
                id=stable_software_id(EntityType.APPLICATION, "org.example.evaluator"),
                entity_type=EntityType.APPLICATION,
                name="Evaluator Example",
                display_name="Evaluator Example",
                version="1.0",
                install_path="/Applications/Evaluator Example.app",
                size_bytes=1_000_000,
                storage_location=StorageLocation.INTERNAL,
            ),
        ),
        volumes=(
            VolumeRecord(
                id="volume:evaluation-root",
                name="Evaluation Root",
                device_identifier="disk-evaluation",
                mount_point="/",
                location=StorageLocation.INTERNAL,
                capacity_bytes=500_000_000,
                free_bytes=168_577_466_368,
            ),
        ),
        collectors=(
            CollectorStatus(
                collector="applications",
                state=CollectorState.COMPLETE,
                collected_at=collected_at,
                records_count=1,
            ),
            CollectorStatus(
                collector="storage",
                state=CollectorState.COMPLETE,
                collected_at=collected_at,
                records_count=1,
            ),
        ),
    )


def build_checkup(collected_at: datetime) -> CheckupSummary:
    """Construct a deterministic read-only checkup fixture."""
    return CheckupSummary(
        collected_at=collected_at,
        priorities=(
            CheckupPriority(
                key="storage_review",
                title="Review storage",
                observed_count=1,
                reason="One measured application is large enough to review.",
                evidence="Synthetic mounted storage and bundle-size facts.",
                benefit="Reviewing it can clarify where detailed storage work is useful.",
                limitation="Bundle size is not reclaimable-space proof.",
                next_command="macwise review largest",
            ),
        ),
        report_confidence=80,
        largest_missing_evidence="Synthetic fixture has no direct recent-use evidence.",
    )


def main() -> int:
    """Write only synthetic output artifacts to the explicit empty destination."""
    args = parse_args()
    try:
        ensure_empty_output_directory(args.output_dir)
        collected_at = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
        (args.output_dir / "audit-v4.json").write_text(
            render_json(build_audit(collected_at)), encoding="utf-8"
        )
        (args.output_dir / "checkup.json").write_text(
            build_checkup(collected_at).model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as error:
        print(f"Could not generate evaluator product output: {error}", file=sys.stderr)
        return 2
    print(f"Saved sanitized product outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
