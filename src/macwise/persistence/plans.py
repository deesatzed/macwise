"""Append-only SQLite persistence for immutable cleanup-plan revisions."""

import hashlib
import json
import sqlite3
from pathlib import Path

from platformdirs import user_data_path
from pydantic import ValidationError

from macwise.models import PlanDocument

_SCHEMA_VERSION = 1
_SCHEMA = """
CREATE TABLE IF NOT EXISTS plan_revisions (
    plan_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    created_at TEXT NOT NULL,
    document_json TEXT NOT NULL,
    document_sha256 TEXT NOT NULL,
    PRIMARY KEY (plan_id, revision)
);
CREATE TABLE IF NOT EXISTS active_plan (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    plan_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    FOREIGN KEY (plan_id, revision)
        REFERENCES plan_revisions(plan_id, revision)
);
"""


class PlanStoreError(RuntimeError):
    """Bounded public failure for local planning-state access."""


def default_plan_database() -> Path:
    """Return the platform-appropriate local MacWise state database."""
    return user_data_path("macwise") / "macwise.db"


def _canonical_json(plan: PlanDocument) -> str:
    return json.dumps(
        plan.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


class PlanStore:
    """Read and append complete immutable plan revisions."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else default_plan_database()

    def _validate_path(self, *, create_parent: bool) -> None:
        if self.path.is_symlink():
            raise PlanStoreError("The planning database cannot be a symbolic link.")
        if self.path.exists() and not self.path.is_file():
            raise PlanStoreError("The planning database path is not a regular file.")
        parent = self.path.parent
        if parent.is_symlink():
            raise PlanStoreError("The planning state directory cannot be a symbolic link.")
        if parent.exists() and not parent.is_dir():
            raise PlanStoreError("The planning state parent is not a directory.")
        if create_parent:
            try:
                parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            except OSError as error:
                raise PlanStoreError(
                    "MacWise could not create the planning state directory."
                ) from error
            if parent.is_symlink() or not parent.is_dir():
                raise PlanStoreError("The planning state directory is unsafe.")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=1.0)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 1000")
        return connection

    @staticmethod
    def _ensure_schema(connection: sqlite3.Connection) -> None:
        row = connection.execute("PRAGMA user_version").fetchone()
        version = int(row[0]) if row is not None else 0
        if version > _SCHEMA_VERSION:
            raise PlanStoreError("The planning database was created by a newer MacWise schema.")
        if version == 0:
            connection.executescript(_SCHEMA)
            connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
            connection.commit()

    def active(self) -> PlanDocument | None:
        """Return the active immutable revision, verifying integrity and schema."""
        self._validate_path(create_parent=False)
        if not self.path.exists():
            return None
        try:
            with self._connect() as connection:
                self._ensure_schema(connection)
                row = connection.execute(
                    """
                    SELECT revisions.document_json, revisions.document_sha256
                    FROM active_plan AS active
                    JOIN plan_revisions AS revisions
                      ON revisions.plan_id = active.plan_id
                     AND revisions.revision = active.revision
                    WHERE active.singleton_id = 1
                    """
                ).fetchone()
        except PlanStoreError:
            raise
        except sqlite3.Error as error:
            raise PlanStoreError("MacWise could not read the planning database.") from error
        if row is None:
            return None
        document_json, expected_digest = str(row[0]), str(row[1])
        actual_digest = hashlib.sha256(document_json.encode()).hexdigest()
        if actual_digest != expected_digest:
            raise PlanStoreError("The active plan failed its integrity check.")
        try:
            return PlanDocument.model_validate_json(document_json)
        except (ValidationError, ValueError) as error:
            raise PlanStoreError("The active plan document is invalid.") from error

    def append(self, plan: PlanDocument) -> None:
        """Atomically append a revision and advance the active pointer."""
        self._validate_path(create_parent=True)
        document_json = _canonical_json(plan)
        digest = hashlib.sha256(document_json.encode()).hexdigest()
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            duplicate = connection.execute(
                "SELECT 1 FROM plan_revisions WHERE plan_id = ? AND revision = ?",
                (plan.plan_id, plan.revision),
            ).fetchone()
            if duplicate is not None:
                raise PlanStoreError("That immutable plan revision already exists.")

            active = connection.execute(
                "SELECT plan_id, revision FROM active_plan WHERE singleton_id = 1"
            ).fetchone()
            if active is not None and str(active[0]) == plan.plan_id:
                expected_revision = int(active[1]) + 1
                if plan.revision != expected_revision:
                    raise PlanStoreError("The plan revision does not follow the active revision.")
            elif plan.revision != 1:
                raise PlanStoreError("A new active plan must begin at revision 1.")

            connection.execute(
                """
                INSERT INTO plan_revisions (
                    plan_id, revision, created_at, document_json, document_sha256
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    plan.plan_id,
                    plan.revision,
                    plan.created_at.isoformat(),
                    document_json,
                    digest,
                ),
            )
            connection.execute(
                """
                INSERT INTO active_plan (singleton_id, plan_id, revision)
                VALUES (1, ?, ?)
                ON CONFLICT(singleton_id) DO UPDATE SET
                    plan_id = excluded.plan_id,
                    revision = excluded.revision
                """,
                (plan.plan_id, plan.revision),
            )
            connection.commit()
        except PlanStoreError:
            if connection is not None:
                connection.rollback()
            raise
        except sqlite3.Error as error:
            if connection is not None:
                connection.rollback()
            raise PlanStoreError("MacWise could not append the plan revision.") from error
        finally:
            if connection is not None:
                connection.close()
