from datetime import UTC, datetime, timedelta

from macwise.models import (
    ClaimBasis,
    EntityType,
    Evidence,
    FindingTopic,
    InstallRole,
    PathEvidence,
    Reliability,
    SoftwareRecord,
    StartupKind,
    StartupRecord,
    UsageLabel,
)
from macwise.services.analysis import analyze_usage

COLLECTED_AT = datetime(2026, 7, 18, 0, 0, tzinfo=UTC)


def record(
    name: str,
    *,
    running: bool | None = None,
    install_role: InstallRole = InstallRole.UNKNOWN,
    reverse_dependencies: tuple[str, ...] = (),
    project_references: tuple[str, ...] = (),
    last_used_at: datetime | None = None,
) -> SoftwareRecord:
    evidence = (
        (
            Evidence(
                kind="spotlight_last_used",
                value=last_used_at.isoformat(),
                source="synthetic mdls",
                collected_at=COLLECTED_AT,
                reliability=Reliability.MEDIUM,
            ),
        )
        if last_used_at is not None
        else ()
    )
    return SoftwareRecord(
        id=f"application:{name}",
        entity_type=EntityType.APPLICATION,
        name=name,
        display_name=name,
        running=running,
        install_role=install_role,
        reverse_dependencies=reverse_dependencies,
        project_references=project_references,
        evidence=evidence,
    )


def test_usage_analysis_applies_cautious_multi_signal_precedence() -> None:
    active = record("active", running=True)
    recent = record("recent", last_used_at=COLLECTED_AT - timedelta(days=5))
    indirect = record(
        "indirect",
        install_role=InstallRole.DEPENDENCY,
        reverse_dependencies=("parent",),
    )
    probable = record("probable")
    configured = record("configured")
    stale = record("stale", last_used_at=COLLECTED_AT - timedelta(days=365))
    unknown = record("unknown")
    confirmed = record("confirmed")
    startup = (
        StartupRecord(
            id="startup:configured",
            label="configured-helper",
            kind=StartupKind.LAUNCH_AGENT,
            owner_software_ids=(configured.id,),
            running=False,
        ),
    )
    paths = (
        PathEvidence(
            id="path:probable",
            subject_id=probable.id,
            path="/Library/Application Support/probable",
            kind="application_support",
            size_bytes=100,
            last_modified_at=COLLECTED_AT - timedelta(days=2),
        ),
    )

    findings = analyze_usage(
        (active, recent, indirect, probable, configured, stale, unknown, confirmed),
        startup=startup,
        path_evidence=paths,
        collected_at=COLLECTED_AT,
        user_confirmed_unused=(confirmed.id,),
    )

    by_subject = {finding.subject_id: finding for finding in findings}
    assert by_subject[active.id].usage_label is UsageLabel.ACTIVELY_USED
    assert by_subject[active.id].basis is ClaimBasis.VERIFIED
    assert by_subject[recent.id].usage_label is UsageLabel.RECENTLY_USED
    assert by_subject[recent.id].basis is ClaimBasis.VERIFIED
    assert by_subject[indirect.id].usage_label is UsageLabel.INDIRECTLY_REQUIRED
    assert by_subject[indirect.id].basis is ClaimBasis.INFERRED
    assert by_subject[probable.id].usage_label is UsageLabel.PROBABLY_USED
    assert by_subject[configured.id].usage_label is UsageLabel.CONFIGURED_BUT_IDLE
    assert by_subject[stale.id].usage_label is UsageLabel.POSSIBLY_UNUSED
    assert by_subject[stale.id].confidence is Reliability.LOW
    assert by_subject[unknown.id].usage_label is UsageLabel.NO_RELIABLE_EVIDENCE
    assert by_subject[unknown.id].basis is ClaimBasis.UNKNOWN
    assert by_subject[confirmed.id].usage_label is UsageLabel.USER_CONFIRMED_UNUSED
    assert by_subject[confirmed.id].basis is ClaimBasis.USER_CONFIRMED
    assert all(finding.topic is FindingTopic.USAGE for finding in findings)
    assert "never used" not in " ".join(finding.statement for finding in findings).casefold()


def test_active_startup_and_project_reference_are_evidence_linked() -> None:
    service = record("service")
    project_tool = record("project-tool", project_references=("Brewfile",))
    startup = (
        StartupRecord(
            id="startup:service",
            label="service",
            kind=StartupKind.HOMEBREW_SERVICE,
            owner_software_ids=(service.id,),
            running=True,
            evidence=(
                Evidence(
                    kind="homebrew_service_status",
                    value="started",
                    source="synthetic brew",
                    collected_at=COLLECTED_AT,
                    reliability=Reliability.HIGH,
                ),
            ),
        ),
    )

    findings = analyze_usage(
        (service, project_tool),
        startup=startup,
        path_evidence=(),
        collected_at=COLLECTED_AT,
    )
    by_subject = {finding.subject_id: finding for finding in findings}

    assert by_subject[service.id].usage_label is UsageLabel.ACTIVELY_USED
    assert "homebrew_service_status" in by_subject[service.id].evidence_kinds
    assert by_subject[project_tool.id].usage_label is UsageLabel.INDIRECTLY_REQUIRED
    assert "homebrew_formula_metadata" in by_subject[project_tool.id].evidence_kinds
