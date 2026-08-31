"""Ngabo Connect edge client: watched-folder capture + HMAC-signed upload (#171).

The automation is the product. This module polls a configured folder for stable
``.csv`` exports, computes a SHA-256, enqueues them into the durable SQLite queue,
and syncs due items to the intake endpoint using HMAC-SHA256. It is the only edge
component; one-time folder configuration is human, every batch is not.
"""

from __future__ import annotations

import hashlib
import time
import urllib.request
from pathlib import Path

from ngabo.infrastructure.connect.connect_queue import ConnectQueue
from ngabo.infrastructure.connect.hmac_auth import compute_signature

SCAN_INTERVAL_SECONDS = 1.0
STABLE_INTERVAL_SECONDS = 0.5


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_size_mtime(path: Path, *, interval: float = STABLE_INTERVAL_SECONDS) -> bool:
    size_a, mtime_a = path.stat().st_size, path.stat().st_mtime
    time.sleep(interval)
    size_b, mtime_b = path.stat().st_size, path.stat().st_mtime
    return size_a == size_b and mtime_a == mtime_b


def walk_and_enqueue(
    watch_dir: Path,
    queue: ConnectQueue,
    *,
    lab_id: str,
    source_id: str,
) -> list[int]:
    ids: list[int] = []
    for path in sorted(watch_dir.glob("*.csv")):
        if not stable_size_mtime(path):
            continue  # still being written
        sha = file_sha256(path)
        item_id = queue.add(
            file_path=str(path), file_sha256=sha, lab_id=lab_id, source_id=source_id
        )
        ids.append(item_id)
    return ids


def sync_due(
    queue: ConnectQueue,
    *,
    intake_url: str,
    secret: bytes,
    lab_id: str,
    source_id: str,
    filename: str,
) -> tuple[int, int]:
    """Upload due items; returns (uploaded, acknowledged)."""
    uploaded = acknowledged = 0
    while True:
        item = queue.next_due()
        if item is None:
            break
        queue.mark_syncing(item["id"])
        body = Path(item["file_path"]).read_bytes()
        ts = str(int(time.time()))
        sha = item["file_sha256"]
        signature = compute_signature(secret, lab_id, source_id, ts, sha, filename, body)
        request = urllib.request.Request(
            intake_url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "text/csv",
                "X-Ngabo-Lab-Id": lab_id,
                "X-Ngabo-Source-Id": source_id,
                "X-Ngabo-Timestamp": ts,
                "X-Ngabo-Content-SHA256": sha,
                "X-Ngabo-Signature": signature,
                "X-Ngabo-Filename": filename,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if 200 <= response.status < 300:
                    queue.mark_acknowledged(item["id"], "batch-from-response")
                    acknowledged += 1
                else:
                    queue.mark_retry(item["id"], f"HTTP {response.status}")
        except Exception as exc:  # noqa: BLE001
            queue.mark_retry(item["id"], str(exc))
        uploaded += 1
    return uploaded, acknowledged
