"""Focused tests for the Ngabo Connect deadline slice (Epic #171)."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from ngabo.application.connect.contracts import (
    AcceptedRecord,
    QuarantinedRecord,
)
from ngabo.application.connect.source_profile import WHONET_DEMO_V1, clean_rows
from ngabo.infrastructure.connect.connect_queue import ConnectQueue
from ngabo.infrastructure.connect.hmac_auth import compute_signature, verify_upload

REPO_ROOT = Path(__file__).resolve().parents[3]
AST_CODES = ("AMK", "CAZ", "CIP", "CRO", "MEM", "SXT")


def _rows() -> list[dict[str, object]]:
    path = REPO_ROOT / "demo" / "connect" / "synthetic_gulu_surveillance_export.csv"
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            ast = {code: raw[code] for code in AST_CODES}
            rows.append(
                {
                    "row_index": len(rows),
                    "isolate_id": raw["ISOLATE_ID"],
                    "collection_date": raw["COLLECTION_DATE"],
                    "organism_code": raw["ORGANISM_CODE"],
                    "organism_name": raw["ORGANISM_NAME"],
                    "facility_id": raw["FACILITY_ID"],
                    "lab_id": raw["LAB_ID"],
                    "ward": raw["WARD"],
                    "specimen_type": raw["SPECIMEN_TYPE"],
                    "patient_token": raw["PATIENT_TOKEN"],
                    "source_import_id": raw["SOURCE_IMPORT_ID"],
                    "ast_results": ast,
                }
            )
    return rows


def test_fixture_receives_accepts_and_quarantines_real_counts() -> None:
    accepted, quarantined, report = clean_rows(_rows(), WHONET_DEMO_V1)
    assert report.received_count == 4
    assert report.accepted_count == 3
    assert report.quarantined_count == 1
    assert report.normalization_count == 3
    assert len(accepted) == 3
    assert all(isinstance(record, AcceptedRecord) for record in accepted)
    assert len(quarantined) == 1
    assert isinstance(quarantined[0], QuarantinedRecord)
    assert quarantined[0].reason_code == "UNKNOWN_ORGANISM_CODE"


def test_normalizer_maps_to_canonical_science() -> None:
    accepted, _, _ = clean_rows(_rows(), WHONET_DEMO_V1)
    accept_031 = next(r for r in accepted if r.isolate_id == "WHN-031")
    assert accept_031.organism_code == "kle"
    assert accept_031.organism_name == "Klebsiella pneumoniae"
    assert accept_031.collection_date == "2026-08-31"
    assert accept_031.ast_results == {
        "AMK": "S",
        "CAZ": "R",
        "CIP": "R",
        "CRO": "R",
        "MEM": "R",
        "SXT": "R",
    }
    assert accept_031.ward == "SYNTH-WARD-A"
    assert accept_031.specimen_type == "blood"


def test_queue_dedupes_and_acks(tmp_path: Path) -> None:
    queue = ConnectQueue(tmp_path / "connect.db")
    first = queue.add(
        file_path=str(tmp_path / "a.csv"),
        file_sha256="a" * 64,
        lab_id="synthetic-lab-gulu",
        source_id="whonet-demo",
    )
    # Same SHA-256 -> same logical upload (deduped).
    second = queue.add(
        file_path=str(tmp_path / "b.csv"),
        file_sha256="a" * 64,
        lab_id="synthetic-lab-gulu",
        source_id="whonet-demo",
    )
    assert first == second
    due = queue.next_due()
    assert due is not None and due["file_sha256"] == "a" * 64
    queue.mark_syncing(due["id"])
    queue.mark_acknowledged(due["id"], "batch-1")
    assert queue.next_due() is None  # acknowledged items are not re-queued
    queue.close()


def test_queue_bounded_retry(tmp_path: Path) -> None:
    queue = ConnectQueue(tmp_path / "connect2.db", max_attempts=3, backoff_base=2.0)
    queue.add(
        file_path=str(tmp_path / "c.csv"),
        file_sha256="b" * 64,
        lab_id="synthetic-lab-gulu",
        source_id="whonet-demo",
    )
    for _ in range(3):
        due = queue.next_due()
        assert due is not None
        queue.mark_syncing(due["id"])
        queue.mark_retry(due["id"], "transport error")
    assert queue.next_due() is None  # retry budget exhausted -> FAILED
    queue.close()


def test_hmac_auth_accepts_valid_and_rejects_tampered() -> None:
    secret = b"demo-secret"
    body = b"ISOLATE_ID,AMK\nWHN-001,R\n"
    ts = "1700000000"
    content_sha256 = hashlib.sha256(body).hexdigest()
    signature = compute_signature(
        secret, "synthetic-lab-gulu", "whonet-demo", ts, content_sha256, "export.csv", body
    )
    headers = {
        "X-Ngabo-Lab-Id": "synthetic-lab-gulu",
        "X-Ngabo-Source-Id": "whonet-demo",
        "X-Ngabo-Timestamp": ts,
        "X-Ngabo-Content-SHA256": content_sha256,
        "X-Ngabo-Signature": signature,
        "X-Ngabo-Filename": "export.csv",
    }
    ok, err = verify_upload(
        headers=headers,
        body=body,
        secret=secret,
        configured_lab_ids={"synthetic-lab-gulu"},
        configured_source_ids={"whonet-demo"},
        now=1700000000.0,
    )
    assert ok is True and err is None
    # Tampered body -> sha256 mismatch.
    ok, err = verify_upload(
        headers=headers,
        body=b"tampered",
        secret=secret,
        configured_lab_ids={"synthetic-lab-gulu"},
        configured_source_ids={"whonet-demo"},
        now=1700000000.0,
    )
    assert ok is False and err == "sha256 mismatch"
