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


class EvidenceTests(unittest.TestCase):
    def test_fetch_run_evidence_parses_jobs_and_duration(self):
        run_data = {
            "id": 12345,
            "html_url": "https://github.com/owner/repo/actions/runs/12345",
            "head_sha": "abcdef123456",
            "event": "pull_request",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2026-08-29T10:00:00Z",
            "updated_at": "2026-08-29T10:00:45Z",
        }
        jobs_data = {
            "jobs": [
                {
                    "id": 999,
                    "name": "PR Quality Gate",
                    "status": "completed",
                    "conclusion": "success",
                    "started_at": "2026-08-29T10:00:40Z",
                    "completed_at": "2026-08-29T10:00:45Z",
                }
            ]
        }

        responses = [
            FakeProcess(0, json.dumps(run_data)),
            FakeProcess(0, json.dumps(jobs_data)),
        ]

        def runner(args):
            return responses.pop(0)

        ev = ci_quality_evidence.fetch_run_evidence("owner/repo", 12345, runner=runner)
        self.assertEqual(ev["run_id"], 12345)
        self.assertEqual(ev["head_sha"], "abcdef123456")
        self.assertEqual(ev["duration_seconds"], 45)
        self.assertIn("PR Quality Gate", ev["jobs"])
        self.assertEqual(ev["jobs"]["PR Quality Gate"]["conclusion"], "success")

    def test_build_ci_evidence_structure(self):
        run_data = {
            "id": 54321,
            "html_url": "https://github.com/owner/repo/actions/runs/54321",
            "head_sha": "fedcba654321",
            "event": "pull_request",
            "status": "completed",
            "conclusion": "success",
            "created_at": "2026-08-29T10:00:00Z",
            "updated_at": "2026-08-29T10:00:30Z",
        }
        jobs_data = {"jobs": []}
        responses = [
            FakeProcess(0, json.dumps(run_data)),
            FakeProcess(0, json.dumps(jobs_data)),
        ]

        def runner(args):
            return responses.pop(0)

        evidence = ci_quality_evidence.build_ci_evidence(
            repo="owner/repo",
            pr_number=103,
            run_id=54321,
            importfrom_bypass_negative_run="33245699999",
            high_severity_negative_run="33245799999",
            advisory_id="GHSA-test-1234",
            runner=runner,
        )

        self.assertEqual(evidence["issue"], 88)
        self.assertEqual(evidence["pr_number"], 103)
        self.assertEqual(evidence["baseline_run_id"], 54321)
        self.assertEqual(evidence["head_sha"], "fedcba654321")
        self.assertEqual(evidence["classification_contract"]["pnpm_lock_only"], True)
        self.assertEqual(evidence["classification_contract"]["unknown_non_doc_fail_closed"], True)
        self.assertEqual(evidence["security"]["advisory_id"], "GHSA-test-1234")
        self.assertEqual(evidence["ruleset"]["github_actions_integration_id"], 15368)
        self.assertEqual(evidence["ruleset"]["allowed_merge_methods"], ["merge"])
        self.assertEqual(evidence["ruleset"]["activation_status"], "PENDING_POST_MERGE")


if __name__ == "__main__":
    unittest.main()
