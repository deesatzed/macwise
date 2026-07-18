"""Append-only SQLite persistence for crash-visible execution manifests."""

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from platformdirs import user_data_path
from pydantic import ValidationError

from macwise.models import ExecutionRun, ExecutionState
from macwise.persistence.locking import StateLock

_SCHEMA_VERSION = 1
_SCHEMA = """
CREATE TABLE IF NOT EXISTS execution_revisions (
    run_id TEXT NOT NULL,
    manifest_revision INTEGER NOT NULL CHECK (manifest_revision >= 1),
    plan_id TEXT NOT NULL,
    plan_revision INTEGER NOT NULL,
    state TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    document_json TEXT NOT NULL,
    document_sha256 TEXT NOT NULL,
    PRIMARY KEY (run_id, manifest_revision)
);
CREATE TABLE IF NOT EXISTS active_execution (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    run_id TEXT NOT NULL,
    manifest_revision INTEGER NOT NULL,
    FOREIGN KEY (run_id, manifest_revision)
        REFERENCES execution_revisions(run_id, manifest_revision)
);
"""
_NEW_RUN_ALLOWED_AFTER: frozenset[ExecutionState] = frozenset(
    {
        ExecutionState.SUCCEEDED,
        ExecutionState.FAILED,
        ExecutionState.UNDONE,
    }
)
_ALLOWED_TRANSITIONS: dict[ExecutionState, frozenset[ExecutionState]] = {
    ExecutionState.PREPARED: frozenset(
        {
            ExecutionState.IN_PROGRESS,
            ExecutionState.FAILED,
            ExecutionState.INTERRUPTED,
        }
    ),
    ExecutionState.IN_PROGRESS: frozenset(
        {
            ExecutionState.IN_PROGRESS,
            ExecutionState.SUCCEEDED,
            ExecutionState.PARTIAL,
            ExecutionState.FAILED,
            ExecutionState.VERIFICATION_FAILED,
            ExecutionState.INTERRUPTED,
        }
    ),
    ExecutionState.SUCCEEDED: frozenset({ExecutionState.UNDO_IN_PROGRESS}),
    ExecutionState.PARTIAL: frozenset({ExecutionState.UNDO_IN_PROGRESS}),
    ExecutionState.VERIFICATION_FAILED: frozenset({ExecutionState.UNDO_IN_PROGRESS}),
    ExecutionState.INTERRUPTED: frozenset(
        {
            ExecutionState.INTERRUPTED,
            ExecutionState.IN_PROGRESS,
            ExecutionState.UNDO_IN_PROGRESS,
            ExecutionState.FAILED,
            ExecutionState.PARTIAL,
            ExecutionState.SUCCEEDED,
            ExecutionState.UNDO_PARTIAL,
            ExecutionState.UNDONE,
        }
    ),
    ExecutionState.UNDO_IN_PROGRESS: frozenset(
        {
            ExecutionState.UNDO_IN_PROGRESS,
            ExecutionState.UNDONE,
            ExecutionState.UNDO_PARTIAL,
            ExecutionState.INTERRUPTED,
        }
    ),
    ExecutionState.FAILED: frozenset(),
    ExecutionState.UNDONE: frozenset(),
    ExecutionState.UNDO_PARTIAL: frozenset({ExecutionState.UNDO_IN_PROGRESS}),
}


class ExecutionStoreError(RuntimeError):
    """Bounded public failure for execution-journal access."""


def default_execution_database() -> Path:
    """Return the platform-appropriate execution journal path."""
    return user_data_path("macwise") / "executions.db"


def canonical_execution_json(run: ExecutionRun) -> str:
    """Return the one canonical persisted representation of a manifest revision."""
    return json.dumps(
        run.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def execution_digest(run: ExecutionRun) -> str:
    """Return the full integrity and undo-approval digest for a manifest revision."""
    return hashlib.sha256(canonical_execution_json(run).encode()).hexdigest()


class ExecutionStore:
    """Read and append complete immutable execution-manifest revisions."""

    def __init__(self, path: Path | None = None, *, lock_path: Path | None = None) -> None:
        selected = path if path is not None else default_execution_database()
        self.path = selected.expanduser().absolute()
        selected_lock = lock_path if lock_path is not None else self.path.parent / "macwise.lock"
        self.lock_path = selected_lock.expanduser().absolute()

    def _reject_symlink_ancestors(self) -> None:
        for ancestor in (self.path.parent, *self.path.parent.parents):
            if ancestor.is_symlink():
                raise ExecutionStoreError(
                    "The execution state path contains a symbolic link ancestor."
                )

    def _validate_path(self, *, create_parent: bool) -> None:
        self._reject_symlink_ancestors()
        if self.path.is_symlink():
            raise ExecutionStoreError("The execution database cannot be a symbolic link.")
        if self.path.exists() and not self.path.is_file():
            raise ExecutionStoreError("The execution database path is not a regular file.")
        parent = self.path.parent
        if parent.exists() and not parent.is_dir():
            raise ExecutionStoreError("The execution state parent is not a directory.")
        if create_parent:
            try:
                parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            except OSError as error:
                raise ExecutionStoreError(
                    "MacWise could not create the execution state directory."
                ) from error
            if parent.is_symlink() or not parent.is_dir():
                raise ExecutionStoreError("The execution state directory is unsafe.")
            self._reject_symlink_ancestors()

    def _connect(self, *, read_only: bool = False) -> sqlite3.Connection:
        target: str | Path = self.path
        if read_only:
            target = f"{self.path.as_uri()}?mode=ro"
        connection = sqlite3.connect(target, timeout=1.0, uri=read_only)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 1000")
        return connection

    @staticmethod
    def _schema_version(connection: sqlite3.Connection) -> int:
        row = connection.execute("PRAGMA user_version").fetchone()
        return int(row[0]) if row is not None else 0

    @staticmethod
    def _table_names(connection: sqlite3.Connection) -> set[str]:
        return {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    @classmethod
    def _require_known_schema(cls, connection: sqlite3.Connection, version: int) -> None:
        if version > _SCHEMA_VERSION:
            raise ExecutionStoreError(
                "The execution database was created by a newer MacWise schema."
            )
        if version != _SCHEMA_VERSION:
            raise ExecutionStoreError("The execution database schema is not supported.")
        if not {"execution_revisions", "active_execution"} <= cls._table_names(connection):
            raise ExecutionStoreError("The execution database schema is invalid.")

    @classmethod
    def _ensure_schema(cls, connection: sqlite3.Connection) -> None:
        version = cls._schema_version(connection)
        if version > _SCHEMA_VERSION:
            raise ExecutionStoreError(
                "The execution database was created by a newer MacWise schema."
            )
        if version == 0:
            connection.executescript(_SCHEMA)
            connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
            connection.commit()
            return
        cls._require_known_schema(connection, version)

    def active(self) -> ExecutionRun | None:
        """Return the active manifest revision without initializing absent state."""
        self._validate_path(create_parent=False)
        if not self.path.exists():
            return None
        try:
            with closing(self._connect(read_only=True)) as connection:
                version = self._schema_version(connection)
                if version == 0:
                    if self._table_names(connection):
                        raise ExecutionStoreError("The execution database schema is not supported.")
                    return None
                self._require_known_schema(connection, version)
                row = connection.execute(
                    """
                    SELECT revisions.document_json, revisions.document_sha256
                    FROM active_execution AS active
                    JOIN execution_revisions AS revisions
                      ON revisions.run_id = active.run_id
                     AND revisions.manifest_revision = active.manifest_revision
                    WHERE active.singleton_id = 1
                    """
                ).fetchone()
        except ExecutionStoreError:
            raise
        except sqlite3.Error as error:
            raise ExecutionStoreError("MacWise could not read the execution database.") from error
        if row is None:
            return None
        document_json, expected_digest = str(row[0]), str(row[1])
        if hashlib.sha256(document_json.encode()).hexdigest() != expected_digest:
            raise ExecutionStoreError("The active execution manifest failed its integrity check.")
        try:
            return ExecutionRun.model_validate_json(document_json)
        except (ValidationError, ValueError) as error:
            raise ExecutionStoreError("The active execution manifest is invalid.") from error

    def latest_undoable(self) -> ExecutionRun | None:
        """Return the latest integrity-checked run with an observed inverse surface."""
        self._validate_path(create_parent=False)
        if not self.path.exists():
            return None
        try:
            with closing(self._connect(read_only=True)) as connection:
                self._require_known_schema(connection, self._schema_version(connection))
                rows = connection.execute(
                    """
                    SELECT revisions.document_json, revisions.document_sha256
                    FROM execution_revisions AS revisions
                    JOIN (
                        SELECT run_id, MAX(manifest_revision) AS manifest_revision
                        FROM execution_revisions
                        GROUP BY run_id
                    ) AS latest
                      ON latest.run_id = revisions.run_id
                     AND latest.manifest_revision = revisions.manifest_revision
                    ORDER BY revisions.rowid DESC
                    """
                ).fetchall()
        except ExecutionStoreError:
            raise
        except sqlite3.Error as error:
            raise ExecutionStoreError("MacWise could not read execution history.") from error
        allowed_states = {
            ExecutionState.SUCCEEDED,
            ExecutionState.PARTIAL,
            ExecutionState.VERIFICATION_FAILED,
            ExecutionState.UNDO_PARTIAL,
            ExecutionState.IN_PROGRESS,
            ExecutionState.UNDO_IN_PROGRESS,
            ExecutionState.INTERRUPTED,
        }
        for raw_json, raw_digest in rows:
            document_json = str(raw_json)
            if hashlib.sha256(document_json.encode()).hexdigest() != str(raw_digest):
                raise ExecutionStoreError(
                    "An execution history manifest failed its integrity check."
                )
            try:
                run = ExecutionRun.model_validate_json(document_json)
            except (ValidationError, ValueError) as error:
                raise ExecutionStoreError("An execution history manifest is invalid.") from error
            if run.state in allowed_states and any(
                (
                    action.after is not None
                    and action.state.value in {"verified", "failed", "undo_failed"}
                )
                or action.state.value in {"in_progress", "undo_in_progress"}
                for action in run.actions
            ):
                return run
        return None

    def append(self, run: ExecutionRun, *, state_lock: StateLock) -> None:
        """Append one manifest revision while the caller holds the shared state lock."""
        if state_lock.path != self.lock_path or not state_lock.is_held:
            raise ExecutionStoreError("The exact shared state lock must be held for append.")
        self._validate_path(create_parent=True)
        document_json = canonical_execution_json(run)
        digest = execution_digest(run)
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect()
            self._ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            duplicate = connection.execute(
                "SELECT 1 FROM execution_revisions WHERE run_id = ? AND manifest_revision = ?",
                (run.run_id, run.manifest_revision),
            ).fetchone()
            if duplicate is not None:
                raise ExecutionStoreError("That immutable execution revision already exists.")

            active_row = connection.execute(
                """
                SELECT revisions.run_id, revisions.manifest_revision, revisions.state,
                       revisions.document_json, revisions.document_sha256
                FROM active_execution AS active
                JOIN execution_revisions AS revisions
                  ON revisions.run_id = active.run_id
                 AND revisions.manifest_revision = active.manifest_revision
                WHERE active.singleton_id = 1
                """
            ).fetchone()
            if active_row is not None and (
                hashlib.sha256(str(active_row[3]).encode()).hexdigest() != str(active_row[4])
            ):
                raise ExecutionStoreError(
                    "The active execution manifest failed its integrity check."
                )
            if run.manifest_revision == 1:
                if active_row is not None and ExecutionState(str(active_row[2])) not in (
                    _NEW_RUN_ALLOWED_AFTER
                ):
                    raise ExecutionStoreError(
                        "An unresolved execution must be recovered before a new run."
                    )
            else:
                expected = (run.run_id, run.manifest_revision - 1)
                active_identity = (
                    (str(active_row[0]), int(active_row[1])) if active_row is not None else None
                )
                assert active_row is not None
                active_previous = ExecutionRun.model_validate_json(str(active_row[3]))
                if active_identity == expected:
                    previous = active_previous
                else:
                    if active_previous.state is not ExecutionState.UNDONE:
                        raise ExecutionStoreError(
                            "The execution revision does not follow the active manifest."
                        )
                    history_row = connection.execute(
                        """
                        SELECT run_id, manifest_revision, document_json, document_sha256
                        FROM execution_revisions
                        WHERE run_id = ?
                        ORDER BY manifest_revision DESC
                        LIMIT 1
                        """,
                        (run.run_id,),
                    ).fetchone()
                    history_identity = (
                        (str(history_row[0]), int(history_row[1]))
                        if history_row is not None
                        else None
                    )
                    if history_identity != expected:
                        raise ExecutionStoreError(
                            "The execution revision does not follow recoverable history."
                        )
                    assert history_row is not None
                    if hashlib.sha256(str(history_row[2]).encode()).hexdigest() != str(
                        history_row[3]
                    ):
                        raise ExecutionStoreError(
                            "The execution history manifest failed its integrity check."
                        )
                    previous = ExecutionRun.model_validate_json(str(history_row[2]))
                if (
                    previous.plan_id != run.plan_id
                    or previous.plan_revision != run.plan_revision
                    or previous.plan_digest != run.plan_digest
                    or previous.created_at != run.created_at
                    or run.state not in _ALLOWED_TRANSITIONS[previous.state]
                ):
                    raise ExecutionStoreError(
                        "The execution revision changes immutable identity or state order."
                    )

            connection.execute(
                """
                INSERT INTO execution_revisions (
                    run_id, manifest_revision, plan_id, plan_revision, state, updated_at,
                    document_json, document_sha256
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.manifest_revision,
                    run.plan_id,
                    run.plan_revision,
                    run.state.value,
                    run.updated_at.isoformat(),
                    document_json,
                    digest,
                ),
            )
            connection.execute(
                """
                INSERT INTO active_execution (singleton_id, run_id, manifest_revision)
                VALUES (1, ?, ?)
                ON CONFLICT(singleton_id) DO UPDATE SET
                    run_id = excluded.run_id,
                    manifest_revision = excluded.manifest_revision
                """,
                (run.run_id, run.manifest_revision),
            )
            connection.commit()
        except ExecutionStoreError:
            if connection is not None:
                connection.rollback()
            raise
        except (sqlite3.Error, ValidationError, ValueError) as error:
            if connection is not None:
                connection.rollback()
            raise ExecutionStoreError(
                "MacWise could not append the execution manifest safely."
            ) from error
        finally:
            if connection is not None:
                connection.close()
