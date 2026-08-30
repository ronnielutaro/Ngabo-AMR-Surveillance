"""Tests for the #92 foundation certification evidence validator."""

from __future__ import annotations

import unittest
from pathlib import Path

from infra.github import foundation_evidence

REPO_ROOT = Path(__file__).resolve().parents[3]
BUNDLE = REPO_ROOT / "infra" / "github" / "foundation_certification_evidence.json"


class FoundationEvidenceTest(unittest.TestCase):
    def test_committed_bundle_valid(self) -> None:
        record = foundation_evidence.load_evidence(str(BUNDLE))
        self.assertEqual(record["ci"]["required_gates"][0], "CI Policy")
        self.assertTrue(record["identity"]["wif_keyless"])
        self.assertTrue(record["promotion"]["no_rebuild"])
        self.assertFalse(record["failure_recovery"]["broken_revision_promoted"])

    def test_rejects_missing_field(self) -> None:
        with self.assertRaises(foundation_evidence.FoundationEvidenceError):
            foundation_evidence.validate({"ci": {}})

    def test_rejects_bad_digest(self) -> None:
        record = foundation_evidence.load_evidence(str(BUNDLE))
        record["artifacts"]["core"]["digest"] = "latest"
        with self.assertRaises(foundation_evidence.FoundationEvidenceError):
            foundation_evidence.validate(record)

    def test_rejects_sensitive_value(self) -> None:
        record = foundation_evidence.load_evidence(str(BUNDLE))
        record["residual_risks"] = ["leaked @gmail.com address"]
        with self.assertRaises(foundation_evidence.FoundationEvidenceError):
            foundation_evidence.validate(record)

    def test_rejects_non_boolean_assertion(self) -> None:
        record = foundation_evidence.load_evidence(str(BUNDLE))
        record["promotion"]["no_rebuild"] = "yes"
        with self.assertRaises(foundation_evidence.FoundationEvidenceError):
            foundation_evidence.validate(record)


if __name__ == "__main__":
    unittest.main()
