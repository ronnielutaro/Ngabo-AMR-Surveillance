"""Tests for infra/github/ci_quality_evidence.py — evidence attribution and adversarial validation."""

import json
import pathlib
import sys
import unittest

MODULE_DIR = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(MODULE_DIR))
import ci_quality_evidence  # noqa: E402


class FakeProcess:
    def __init__(self, returncode: int, stdout: str, stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


# ---------------------------------------------------------------------------
# Helpers — build realistic fake API responses
# ---------------------------------------------------------------------------

def _make_pr_data(pr_number: int = 103, head_sha: str = "abcdef123456") -> dict:
    return {
        "number": pr_number,
        "head": {"sha": head_sha},
        "state": "open",
    }


def _make_run_data(
    run_id: int = 12345,
    head_sha: str = "abcdef123456",
    name: str = "PR Quality",
    path: str = ".github/workflows/pr-quality.yml",
    event: str = "pull_request",
    status: str = "completed",
    conclusion: str = "success",
    pr_number: int = 103,
) -> dict:
    return {
        "id": run_id,
        "html_url": f"https://github.com/owner/repo/actions/runs/{run_id}",
        "head_sha": head_sha,
        "name": name,
        "path": path,
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "created_at": "2026-08-29T10:00:00Z",
        "updated_at": "2026-08-29T10:00:45Z",
        "pull_requests": [{"number": pr_number}],
    }


def _make_jobs_data(
    gate_conclusion: str = "success",
    include_optional: bool = True,
) -> dict:
    jobs = [
        {"id": 1, "name": "Changed Paths", "status": "completed", "conclusion": "success",
         "started_at": "2026-08-29T10:00:01Z", "completed_at": "2026-08-29T10:00:10Z"},
        {"id": 2, "name": "CI Policy", "status": "completed", "conclusion": "success",
         "started_at": "2026-08-29T10:00:01Z", "completed_at": "2026-08-29T10:00:15Z"},
        {"id": 3, "name": "Dependency Review", "status": "completed", "conclusion": "success",
         "started_at": "2026-08-29T10:00:01Z", "completed_at": "2026-08-29T10:00:12Z"},
        {"id": 4, "name": "Dependency Security", "status": "completed", "conclusion": "success",
         "started_at": "2026-08-29T10:00:01Z", "completed_at": "2026-08-29T10:00:20Z"},
        {"id": 5, "name": "PR Quality Gate", "status": "completed", "conclusion": gate_conclusion,
         "started_at": "2026-08-29T10:00:40Z", "completed_at": "2026-08-29T10:00:45Z"},
    ]
    if include_optional:
        jobs.extend([
            {"id": 6, "name": "Core Quality", "status": "completed", "conclusion": "success",
             "started_at": "2026-08-29T10:00:01Z", "completed_at": "2026-08-29T10:00:35Z"},
            {"id": 7, "name": "Web Quality", "status": "completed", "conclusion": "success",
             "started_at": "2026-08-29T10:00:01Z", "completed_at": "2026-08-29T10:00:30Z"},
            {"id": 8, "name": "Infrastructure Regression", "status": "completed",
             "conclusion": "success",
             "started_at": "2026-08-29T10:00:01Z", "completed_at": "2026-08-29T10:00:25Z"},
        ])
    return {"jobs": jobs}


def _make_runner(*responses):
    """Create a mock runner that returns responses in order."""
    queue = list(responses)

    def runner(args):
        if not queue:
            return FakeProcess(1, "", "No more mock responses")
        return queue.pop(0)

    return runner


# ---------------------------------------------------------------------------
# Valid case
# ---------------------------------------------------------------------------

class ValidEvidenceTests(unittest.TestCase):
    """Test that valid inputs produce correct evidence."""

    def test_valid_evidence_structure(self):
        pr = _make_pr_data()
        run = _make_run_data()
        jobs = _make_jobs_data()
        neg_run = _make_run_data(run_id=99999, head_sha="c1c9aa18", conclusion="failure")
        neg_jobs = _make_jobs_data()
        neg_jobs["jobs"][5]["conclusion"] = "failure"  # Core Quality failed
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),       # fetch PR
            FakeProcess(0, json.dumps(run)),       # fetch run
            FakeProcess(0, json.dumps(jobs)),      # fetch jobs
            FakeProcess(0, json.dumps(neg_run)),   # validate direct import neg run
            FakeProcess(0, json.dumps(neg_jobs)),  # validate direct import neg jobs
        )
        evidence = ci_quality_evidence.build_ci_evidence(
            repo="owner/repo",
            pr_number=103,
            run_id=12345,
            direct_import_negative_run="99999",
            importfrom_bypass_negative_run=None,
            high_severity_negative_run=None,
            runner=runner,
        )
        self.assertIn("observed", evidence)
        self.assertIn("contract", evidence)
        self.assertIn("historical_negative_proofs", evidence)
        self.assertEqual(evidence["observed"]["pr_number"], 103)
        self.assertEqual(evidence["observed"]["run_id"], 12345)
        self.assertEqual(evidence["observed"]["run_head_sha"], "abcdef123456")
        self.assertEqual(evidence["observed"]["run_conclusion"], "success")
        self.assertEqual(evidence["issue"], 88)
        self.assertEqual(
            evidence["issue_title"],
            "Cloud Foundation 1A.4: Enforce monorepo PR quality gates in GitHub Actions",
        )
        self.assertIn("direct_import_bypass", evidence["historical_negative_proofs"])
        self.assertNotIn("importfrom_bypass", evidence["historical_negative_proofs"])

    def test_valid_evidence_jobs_observed(self):
        pr = _make_pr_data()
        run = _make_run_data()
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        evidence = ci_quality_evidence.build_ci_evidence(
            repo="owner/repo",
            pr_number=103,
            run_id=12345,
            validate_negative_proofs=False,
            runner=runner,
        )
        observed_jobs = evidence["observed"]["jobs"]
        self.assertIn("PR Quality Gate", observed_jobs)
        self.assertIn("Changed Paths", observed_jobs)
        self.assertEqual(observed_jobs["PR Quality Gate"]["conclusion"], "success")

    def test_valid_evidence_duration(self):
        pr = _make_pr_data()
        run = _make_run_data()
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        evidence = ci_quality_evidence.build_ci_evidence(
            repo="owner/repo",
            pr_number=103,
            run_id=12345,
            validate_negative_proofs=False,
            runner=runner,
        )
        self.assertEqual(evidence["observed"]["duration_seconds"], 45)

    def test_contract_has_privacy_review_status(self):
        pr = _make_pr_data()
        run = _make_run_data()
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        evidence = ci_quality_evidence.build_ci_evidence(
            repo="owner/repo",
            pr_number=103,
            run_id=12345,
            validate_negative_proofs=False,
            runner=runner,
        )
        self.assertEqual(
            evidence["contract"]["privacy_review_status"],
            "EXTERNAL_REVIEW_REQUIRED",
        )

    def test_optional_lanes_skipped_is_valid(self):
        pr = _make_pr_data()
        run = _make_run_data()
        jobs = _make_jobs_data(include_optional=False)
        # Add skipped optional lanes
        jobs["jobs"].extend([
            {"id": 6, "name": "Core Quality", "status": "completed",
             "conclusion": "skipped", "started_at": None, "completed_at": None},
            {"id": 7, "name": "Web Quality", "status": "completed",
             "conclusion": "skipped", "started_at": None, "completed_at": None},
        ])
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        evidence = ci_quality_evidence.build_ci_evidence(
            repo="owner/repo",
            pr_number=103,
            run_id=12345,
            validate_negative_proofs=False,
            runner=runner,
        )
        self.assertEqual(evidence["observed"]["run_conclusion"], "success")

    def test_known_high_severity_proof_binds_fixture_advisory_id(self):
        pr = _make_pr_data()
        run = _make_run_data()
        jobs = _make_jobs_data()
        neg_run = _make_run_data(run_id=33247203439, head_sha="7afe3882", conclusion="failure")
        neg_jobs = _make_jobs_data()
        neg_jobs["jobs"][3]["conclusion"] = "failure"  # Dependency Security failed
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
            FakeProcess(0, json.dumps(neg_run)),
            FakeProcess(0, json.dumps(neg_jobs)),
        )
        evidence = ci_quality_evidence.build_ci_evidence(
            repo="owner/repo",
            pr_number=103,
            run_id=12345,
            direct_import_negative_run=None,
            importfrom_bypass_negative_run=None,
            high_severity_negative_run="33247203439",
            runner=runner,
        )
        proof = evidence["historical_negative_proofs"]["high_severity_dependency"]
        self.assertEqual(proof["run_id"], "33247203439")
        self.assertEqual(proof["advisory_id"], "GHSA-cpwx-vrp4-4pq7")

    def test_unknown_high_severity_proof_omits_advisory_id(self):
        pr = _make_pr_data()
        run = _make_run_data()
        jobs = _make_jobs_data()
        neg_run = _make_run_data(run_id=88888, head_sha="7afe3882", conclusion="failure")
        neg_jobs = _make_jobs_data()
        neg_jobs["jobs"][3]["conclusion"] = "failure"  # Dependency Security failed
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
            FakeProcess(0, json.dumps(neg_run)),
            FakeProcess(0, json.dumps(neg_jobs)),
        )
        evidence = ci_quality_evidence.build_ci_evidence(
            repo="owner/repo",
            pr_number=103,
            run_id=12345,
            direct_import_negative_run=None,
            importfrom_bypass_negative_run=None,
            high_severity_negative_run="88888",
            runner=runner,
        )
        proof = evidence["historical_negative_proofs"]["high_severity_dependency"]
        self.assertEqual(proof["run_id"], "88888")
        self.assertNotIn("advisory_id", proof)

    def test_cli_rejects_arbitrary_advisory_argument(self):
        import argparse
        # Verify parser raises error when caller attempts --advisory-id
        with self.assertRaises(SystemExit):
            parser = argparse.ArgumentParser()
            # Calling main with arbitrary --advisory-id will fail argument parsing
            sys_argv = ["ci_quality_evidence.py", "--advisory-id", "GHSA-FAKE-1234"]
            orig_argv = sys.argv
            sys.argv = sys_argv
            try:
                ci_quality_evidence.main()
            finally:
                sys.argv = orig_argv


# ---------------------------------------------------------------------------
# Adversarial tests
# ---------------------------------------------------------------------------

class AdversarialEvidenceTests(unittest.TestCase):
    """Prove the generator rejects invalid/mismatched inputs."""

    def test_rejects_wrong_pr_number(self):
        pr = _make_pr_data(pr_number=999)
        run = _make_run_data()
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("PR number mismatch", str(ctx.exception))

    def test_rejects_wrong_head_sha(self):
        pr = _make_pr_data(head_sha="pr_head_abc")
        run = _make_run_data(head_sha="different_sha")
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("run head does not match PR head", str(ctx.exception))

    def test_rejects_wrong_workflow_name(self):
        pr = _make_pr_data()
        run = _make_run_data(name="Some Other Workflow")
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("wrong workflow name", str(ctx.exception))

    def test_rejects_wrong_event(self):
        pr = _make_pr_data()
        run = _make_run_data(event="push")
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("wrong event", str(ctx.exception))

    def test_rejects_failed_run(self):
        pr = _make_pr_data()
        run = _make_run_data(conclusion="failure")
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("run did not succeed", str(ctx.exception))

    def test_rejects_cancelled_run(self):
        pr = _make_pr_data()
        run = _make_run_data(conclusion="cancelled")
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("run did not succeed", str(ctx.exception))

    def test_rejects_in_progress_run(self):
        pr = _make_pr_data()
        run = _make_run_data(status="in_progress", conclusion="")
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("run not completed", str(ctx.exception))

    def test_rejects_no_pr_association(self):
        pr = _make_pr_data()
        run = _make_run_data()
        run["pull_requests"] = []  # No PR association
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("not associated with PR #103", str(ctx.exception))

    def test_rejects_wrong_pr_association(self):
        pr = _make_pr_data()
        run = _make_run_data(pr_number=999)
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("not associated with PR #103", str(ctx.exception))

    def test_rejects_missing_pr_quality_gate_job(self):
        pr = _make_pr_data()
        run = _make_run_data()
        jobs = _make_jobs_data()
        # Remove PR Quality Gate
        jobs["jobs"] = [j for j in jobs["jobs"] if j["name"] != "PR Quality Gate"]
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("missing required jobs", str(ctx.exception))

    def test_rejects_failed_pr_quality_gate(self):
        pr = _make_pr_data()
        run = _make_run_data()
        jobs = _make_jobs_data(gate_conclusion="failure")
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("PR Quality Gate", str(ctx.exception))

    def test_rejects_malformed_json_response(self):
        runner = _make_runner(FakeProcess(0, "NOT JSON"))
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("invalid JSON", str(ctx.exception))

    def test_rejects_gh_api_failure(self):
        runner = _make_runner(FakeProcess(1, "", "API error"))
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("gh API call failed", str(ctx.exception))

    def test_rejects_optional_lane_failure(self):
        pr = _make_pr_data()
        run = _make_run_data()
        jobs = _make_jobs_data(include_optional=False)
        # Add a failed optional lane
        jobs["jobs"].append({
            "id": 6, "name": "Core Quality", "status": "completed",
            "conclusion": "failure",
            "started_at": "2026-08-29T10:00:01Z",
            "completed_at": "2026-08-29T10:00:35Z",
        })
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("Core Quality", str(ctx.exception))

    def test_rejects_workflow_dispatch_event(self):
        pr = _make_pr_data()
        run = _make_run_data(event="workflow_dispatch")
        jobs = _make_jobs_data()
        runner = _make_runner(
            FakeProcess(0, json.dumps(pr)),
            FakeProcess(0, json.dumps(run)),
            FakeProcess(0, json.dumps(jobs)),
        )
        with self.assertRaises(ci_quality_evidence.EvidenceValidationError) as ctx:
            ci_quality_evidence.build_ci_evidence(
                repo="owner/repo", pr_number=103, run_id=12345, runner=runner,
            )
        self.assertIn("wrong event", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
