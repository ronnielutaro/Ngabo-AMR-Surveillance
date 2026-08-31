"""Local durable SQLite queue for the Ngabo Connect edge (Epic #171).

This is EDGE-side durability only. Firestore remains cloud canonical state. The
queue survives restart, de-duplicates by file SHA-256, and implements bounded
exponential backoff so a bad upload does not loop forever.
"""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS connect_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_sha256 TEXT NOT NULL UNIQUE,
    lab_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at REAL NOT NULL,
    created_at REAL NOT NULL,
    acknowledged_at REAL,
    remote_batch_id TEXT,
    last_error TEXT
);
"""


class ConnectQueue:
    """Restart-safe SQLite-backed connect queue."""

    def __init__(
        self,
        db_path: Path,
        *,
        max_attempts: int = 5,
        backoff_base: float = 2.0,
        now: Callable[[], float] | None = None,
    ) -> None:
        self._db = sqlite3.connect(str(db_path))
        self._db.row_factory = sqlite3.Row
        self._db.executescript(_SCHEMA)
        self._db.commit()
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base
        self._now = now if now is not None else time.time

    def add(self, *, file_path: str, file_sha256: str, lab_id: str, source_id: str) -> int:
        """Insert one logical upload; de-duplicate by SHA-256."""
        now = self._now()
        self._db.execute(
            "INSERT OR IGNORE INTO connect_queue "
            "(file_path, file_sha256, lab_id, source_id, status, attempt_count, "
            "next_attempt_at, created_at) VALUES (?,?,?,?, 'QUEUED', 0, ?, ?)",
            (file_path, file_sha256, lab_id, source_id, now, now),
        )
        self._db.commit()
        row = self._db.execute(
            "SELECT id FROM connect_queue WHERE file_sha256=?", (file_sha256,)
        ).fetchone()
        return int(row["id"])

    def next_due(self) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT * FROM connect_queue WHERE status IN ('QUEUED','RETRYING') "
            "AND next_attempt_at <= ? ORDER BY id LIMIT 1",
            (self._now(),),
        ).fetchone()
        return dict(row) if row is not None else None

    def mark_syncing(self, item_id: int) -> None:
        self._db.execute(
            "UPDATE connect_queue SET status='SYNCING' WHERE id=?", (item_id,)
        )
        self._db.commit()

    def mark_acknowledged(self, item_id: int, remote_batch_id: str) -> None:
        self._db.execute(
            "UPDATE connect_queue SET status='ACKNOWLEDGED', acknowledged_at=?, "
            "remote_batch_id=?, last_error=NULL WHERE id=?",
            (self._now(), remote_batch_id, item_id),
        )
        self._db.commit()

    def mark_retry(self, item_id: int, error: str) -> None:
        row = self._db.execute(
            "SELECT attempt_count FROM connect_queue WHERE id=?", (item_id,)
        ).fetchone()
        attempts = int(row["attempt_count"]) if row else 0
        if attempts + 1 >= self._max_attempts:
            self.mark_failed(item_id, error)
            return
        delay = min(3600.0, self._backoff_base ** (attempts + 1))
        self._db.execute(
            "UPDATE connect_queue SET status='RETRYING', attempt_count=attempt_count+1, "
            "next_attempt_at=?, last_error=? WHERE id=?",
            (self._now() + delay, error, item_id),
        )
        self._db.commit()

    def mark_failed(self, item_id: int, error: str) -> None:
        self._db.execute(
            "UPDATE connect_queue SET status='FAILED', attempt_count=attempt_count+1, "
            "last_error=? WHERE id=?",
            (error, item_id),
        )
        self._db.commit()

    def close(self) -> None:
        self._db.close()
