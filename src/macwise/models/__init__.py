"""Public normalized models used across MacWise interfaces."""

from macwise.models.audit import AuditDocument, CollectorState, CollectorStatus
from macwise.models.evidence import Evidence, Reliability
from macwise.models.software import EntityType, InstallRole, SoftwareRecord, stable_software_id
from macwise.models.storage import StorageLocation, VolumeRecord, stable_volume_id

__all__ = [
    "AuditDocument",
    "CollectorState",
    "CollectorStatus",
    "EntityType",
    "Evidence",
    "InstallRole",
    "Reliability",
    "SoftwareRecord",
    "StorageLocation",
    "VolumeRecord",
    "stable_software_id",
    "stable_volume_id",
]
