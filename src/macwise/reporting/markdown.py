"""Plain-language Markdown rendering for MacWise audit documents."""

from macwise.models import AuditDocument, ClaimBasis, EntityType, InstallRole, SoftwareRecord
from macwise.text import safe_display_text


def _markdown_text(value: str) -> str:
    escaped = safe_display_text(value).replace("\\", "\\\\")
    for character in ("`", "*", "_", "[", "]", "<", ">"):
        escaped = escaped.replace(character, f"\\{character}")
    return escaped


def _bytes(value: int | None) -> str:
    if value is None:
        return "unknown"
    amount = float(value)
    units = ("bytes", "KiB", "MiB", "GiB", "TiB")
    unit = units[0]
    for candidate in units:
        unit = candidate
        if amount < 1024 or candidate == units[-1]:
            break
        amount /= 1024
    return f"{int(amount)} {unit}" if unit == "bytes" else f"{amount:.1f} {unit}"


def _role(record: SoftwareRecord) -> str:
    if record.install_role is InstallRole.EXPLICIT:
        return "explicitly installed"
    if record.install_role is InstallRole.DEPENDENCY:
        return "dependency"
    return "installation role unknown"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _tri_state(value: bool | None) -> str:
    return "unknown" if value is None else _yes_no(value)


def _human_label(value: str) -> str:
    return _markdown_text(value.replace("_", " "))


def _software_lines(record: SoftwareRecord) -> list[str]:
    version = f", version {_markdown_text(record.version)}" if record.version else ""
    lines = [f"- **{_markdown_text(record.display_name)}** — {_role(record)}{version}"]
    if record.install_path:
        lines.append(f"  - Location: `{_markdown_text(record.install_path)}`")
    if record.install_source:
        lines.append(f"  - Install source: {_markdown_text(record.install_source)}")
    if record.publisher:
        lines.append(f"  - Publisher: {_markdown_text(record.publisher)}")
    if record.signing_identity:
        lines.append(f"  - Signing identity: {_markdown_text(record.signing_identity)}")
    if record.team_identifier:
        lines.append(f"  - Signing team: {_markdown_text(record.team_identifier)}")
    if record.size_bytes is not None:
        lines.append(
            f"  - Size: {_bytes(record.size_bytes)} on {record.storage_location.value} storage"
        )
    if record.architectures:
        lines.append(f"  - Architectures: {', '.join(map(_markdown_text, record.architectures))}")
    if record.running is not None:
        lines.append(f"  - Running at collection time: {_yes_no(record.running)}")
    if record.components:
        lines.append(f"  - Components: {', '.join(map(_markdown_text, record.components))}")
    if record.executables:
        lines.append(f"  - Executables: {', '.join(map(_markdown_text, record.executables))}")
    if record.dependencies:
        lines.append(f"  - Depends on: {', '.join(map(_markdown_text, record.dependencies))}")
    if record.reverse_dependencies:
        lines.append(
            f"  - Required by: {', '.join(map(_markdown_text, record.reverse_dependencies))}"
        )
    if record.service_status:
        lines.append(f"  - Background service: {_markdown_text(record.service_status)}")
    package_state: list[str] = []
    if record.linked is not None:
        package_state.append(f"Linked: {_yes_no(record.linked)}")
    if record.pinned is not None:
        package_state.append(f"pinned: {_yes_no(record.pinned)}")
    if package_state:
        lines.append(f"  - {'; '.join(package_state)}")
    if record.project_references:
        lines.append(
            f"  - Project references: {', '.join(map(_markdown_text, record.project_references))}"
        )
    if record.caveats:
        lines.append(f"  - Caveats: {_markdown_text(record.caveats)}")
    return lines


def render_markdown(audit: AuditDocument) -> str:
    """Render verified inventory separately from limitations and unknowns."""
    lines = [
        "# MacWise Audit",
        "",
        f"Schema version: {audit.schema_version}",
        f"Collected: {audit.collected_at.isoformat()}",
        "",
        "## Verified inventory",
        "",
        "### Applications",
        "",
    ]
    applications = [item for item in audit.software if item.entity_type is EntityType.APPLICATION]
    if applications:
        for record in applications:
            lines.extend(_software_lines(record))
    else:
        lines.append("- No application records were collected.")

    lines.extend(["", "### Homebrew software", ""])
    homebrew = [
        item
        for item in audit.software
        if item.entity_type in {EntityType.HOMEBREW_FORMULA, EntityType.HOMEBREW_CASK}
    ]
    if homebrew:
        for record in homebrew:
            lines.extend(_software_lines(record))
    else:
        lines.append("- No Homebrew records were collected.")

    lines.extend(["", "### Storage", ""])
    if audit.volumes:
        for volume in audit.volumes:
            capacity = _bytes(volume.capacity_bytes)
            free = _bytes(volume.free_bytes)
            mount = (
                f" at `{_markdown_text(volume.mount_point)}`"
                if volume.mount_point
                else " (unmounted)"
            )
            lines.append(
                f"- **{_markdown_text(volume.name)}** — {volume.location.value}{mount}; "
                f"{free} free of {capacity}"
            )
            hierarchy: list[str] = []
            if volume.parent_device_identifier:
                hierarchy.append(f"Parent disk: {_markdown_text(volume.parent_device_identifier)}")
            if volume.apfs_container_identifier:
                hierarchy.append(
                    f"APFS container: {_markdown_text(volume.apfs_container_identifier)}"
                )
            if hierarchy:
                lines.append(f"  - {'; '.join(hierarchy)}")
            if volume.physical_store_identifiers:
                lines.append(
                    "  - Physical stores: "
                    f"{', '.join(map(_markdown_text, volume.physical_store_identifiers))}"
                )
            if volume.ownership_enabled is not None:
                lines.append(f"  - Ownership enabled: {_yes_no(volume.ownership_enabled)}")
            if volume.time_machine_role:
                lines.append(f"  - Time Machine role: {_markdown_text(volume.time_machine_role)}")
            if volume.time_machine_destination is not None:
                lines.append(
                    "  - Configured Time Machine destination: "
                    f"{_yes_no(volume.time_machine_destination)}"
                )
            if volume.time_machine_excluded is not None:
                lines.append(
                    f"  - Excluded from Time Machine: {_yes_no(volume.time_machine_excluded)}"
                )
    else:
        lines.append("- No storage records were collected.")

    software_by_id = {record.id: record for record in audit.software}
    volume_by_id = {volume.id: volume for volume in audit.volumes}
    basis_sections = (
        (ClaimBasis.VERIFIED, "Verified"),
        (ClaimBasis.INFERRED, "Inferred"),
        (ClaimBasis.USER_CONFIRMED, "User-confirmed"),
        (ClaimBasis.UNKNOWN, "Unknown"),
    )
    lines.extend(["", "## Evidence-linked findings", ""])
    for basis, heading in basis_sections:
        lines.extend([f"### {heading}", ""])
        findings = [finding for finding in audit.findings if finding.basis is basis]
        if not findings:
            lines.append("- None recorded.")
            lines.append("")
            continue
        for finding in findings:
            subject = software_by_id.get(finding.subject_id)
            subject_label = subject.display_name if subject is not None else finding.subject_id
            if finding.usage_label is not None:
                topic = f"Usage: {_human_label(finding.usage_label.value)}"
            else:
                topic = _human_label(finding.topic.value).capitalize()
            lines.append(
                f"- **{_markdown_text(subject_label)}** — {topic}; "
                f"{_human_label(finding.confidence.value)} confidence"
            )
            lines.append(f"  - {_markdown_text(finding.statement)}")
            if finding.evidence_kinds:
                lines.append(
                    "  - Evidence: "
                    f"{', '.join(_human_label(value) for value in finding.evidence_kinds)}"
                )
            for limitation in finding.limitations:
                lines.append(f"  - Limitation: {_markdown_text(limitation)}")
        lines.append("")

    lines.extend(["## Startup and background items", ""])
    if audit.startup:
        for item in audit.startup:
            owners = [
                software_by_id[owner_id].display_name
                for owner_id in item.owner_software_ids
                if owner_id in software_by_id
            ]
            lines.append(f"- **{_markdown_text(item.label)}** — {_human_label(item.kind.value)}")
            lines.append(
                f"  - Owner: {', '.join(map(_markdown_text, owners)) if owners else 'unknown'}"
            )
            lines.append(
                f"  - Enabled: {_tri_state(item.enabled)}; running: {_tri_state(item.running)}"
            )
            if item.source_path:
                lines.append(f"  - Source: `{_markdown_text(item.source_path)}`")
    else:
        lines.append("- No startup or background records were collected.")

    lines.extend(["", "## Related data measurements", ""])
    if audit.path_evidence:
        for item in audit.path_evidence:
            subject = software_by_id.get(item.subject_id)
            subject_label = subject.display_name if subject is not None else item.subject_id
            lines.append(
                f"- **{_markdown_text(subject_label)}** — {_human_label(item.kind)}: "
                f"{_bytes(item.size_bytes)} on {item.storage_location.value} storage at "
                f"`{_markdown_text(item.path)}`"
            )
            if item.backup_excluded is True:
                backup_fact = "excluded from Time Machine"
            elif item.backup_excluded is False:
                backup_fact = "not excluded from Time Machine"
            else:
                backup_fact = "Time Machine exclusion unknown"
            lines.append(f"  - Backup fact: {backup_fact}; this does not prove coverage.")
            if item.last_modified_at is not None:
                lines.append(f"  - Last modified: {item.last_modified_at.isoformat()}")
    else:
        lines.append("- No related-data paths were measured.")

    lines.extend(["", "## Backup facts", ""])
    if audit.backup is None:
        lines.extend(
            [
                "- Configured: unknown",
                "- Available destinations: unknown",
                "- Last verifiable backup: unknown",
            ]
        )
    else:
        lines.append(f"- Configured: {_tri_state(audit.backup.configured)}")
        if audit.backup.available_destination_volume_ids:
            destinations = [
                volume_by_id[volume_id].name if volume_id in volume_by_id else volume_id
                for volume_id in audit.backup.available_destination_volume_ids
            ]
            lines.append(
                f"- Available destinations: {', '.join(map(_markdown_text, destinations))}"
            )
        else:
            lines.append("- Available destinations: none observed")
        latest = (
            audit.backup.last_backup_at.isoformat()
            if audit.backup.last_backup_at is not None
            else "unknown"
        )
        lines.append(f"- Last verifiable backup: {latest}")
        for limitation in audit.backup.limitations:
            lines.append(f"- Limitation: {_markdown_text(limitation)}")
    lines.append("- Backup coverage is not verified.")

    lines.extend(["", "## Collection limitations", ""])
    limitation_lines = [
        f"- {_markdown_text(status.collector)}: {_markdown_text(limitation)}"
        for status in audit.collectors
        for limitation in status.limitations
    ]
    lines.extend(limitation_lines or ["- None reported by the completed collectors."])

    lines.extend(
        [
            "",
            "## Unknown in this phase",
            "",
            *(
                []
                if audit.findings
                else ["- Direct and recent usage evidence has not been collected."]
            ),
            *(
                []
                if audit.startup and audit.path_evidence
                else ["- Startup ownership and related user data have not been fully assessed."]
            ),
            "- Backup coverage has not been verified.",
            "- No cleanup recommendation or removal-safety conclusion is made here.",
            "",
            "This report is read-only. MacWise did not change this Mac.",
        ]
    )
    return "\n".join(lines) + "\n"
