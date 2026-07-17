from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from macwise.models import (
    ClaimBasis,
    Evidence,
    Finding,
    FindingTopic,
    PathEvidence,
    Reliability,
    StartupKind,
    StartupRecord,
    StorageLocation,
    UsageLabel,
    stable_path_evidence_id,
    stable_startup_id,
)

COLLECTED_AT = datetime(2026, 7, 17, 21, 0, tzinfo=UTC)


def test_usage_finding_requires_a_typed_label_and_explicit_basis() -> None:
    finding = Finding(
        subject_id="application:example",
        topic=FindingTopic.USAGE,
        statement="Currently running at collection time.",
        basis=ClaimBasis.VERIFIED,
        confidence=Reliability.HIGH,
        usage_label=UsageLabel.ACTIVELY_USED,
        evidence_kinds=("application_process_state",),
    )

    assert finding.usage_label is UsageLabel.ACTIVELY_USED
    assert finding.basis is ClaimBasis.VERIFIED
    assert finding.evidence_kinds == ("application_process_state",)

    with pytest.raises(ValidationError, match="usage_label"):
        Finding(
            subject_id="application:unknown",
            topic=FindingTopic.USAGE,
            statement="No reliable evidence was found.",
            basis=ClaimBasis.UNKNOWN,
            confidence=Reliability.UNKNOWN,
        )


def test_startup_and_path_records_keep_ownership_backup_and_provenance_typed() -> None:
    startup = StartupRecord(
        id=stable_startup_id(StartupKind.LAUNCH_AGENT, "org.example.agent"),
        label="org.example.agent",
        kind=StartupKind.LAUNCH_AGENT,
        source_path="/Library/LaunchAgents/org.example.agent.plist",
        program="/Applications/Example.app/Contents/MacOS/Example",
        bundle_identifier="org.example.app",
        owner_software_ids=("application:example",),
        enabled=None,
        running=False,
        evidence=(
            Evidence(
                kind="launch_plist_metadata",
                value={"label": "org.example.agent"},
                source="synthetic launch plist",
                collected_at=COLLECTED_AT,
                reliability=Reliability.HIGH,
            ),
        ),
    )
    related = PathEvidence(
        id=stable_path_evidence_id("application:example", "/Library/Application Support/Example"),
        subject_id="application:example",
        path="/Library/Application Support/Example",
        kind="application_support",
        size_bytes=4096,
        storage_location=StorageLocation.INTERNAL,
        last_modified_at=COLLECTED_AT,
        backup_excluded=False,
    )

    assert startup.id.startswith("startup:")
    assert startup.owner_software_ids == ("application:example",)
    assert startup.enabled is None
    assert related.id.startswith("path:")
    assert related.backup_excluded is False
    assert related.size_bytes == 4096
