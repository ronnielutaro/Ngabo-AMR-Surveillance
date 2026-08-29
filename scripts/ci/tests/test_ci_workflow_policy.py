import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
PR_QUALITY = ROOT / ".github" / "workflows" / "pr-quality.yml"
CONTROL_PLANE = ROOT / ".github" / "workflows" / "ci-control-plane.yml"


class WorkflowPolicyTests(unittest.TestCase):
    def test_pr_quality_is_pull_request_only_and_has_no_path_filter(self):
        text = PR_QUALITY.read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertNotIn("pull_request_target:", text)
        self.assertNotIn("workflow_dispatch:", text)
        self.assertIsNone(re.search(r"(?m)^\s{2,}paths(?:-ignore)?:\s*$", text))

    def test_pr_quality_has_read_only_permissions_and_stable_gate(self):
        text = PR_QUALITY.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", text)
        for forbidden in (
            "id-token: write",
            "contents: write",
            "packages: write",
            "actions: write",
            "deployments: write",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("name: PR Quality Gate", text)
        self.assertIn("if: always()", text)
        self.assertIn("persist-credentials: false", text)

    def test_control_plane_never_checks_out_or_executes_pr_head(self):
        text = CONTROL_PLANE.read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", text)
        self.assertIn("ref: ${{ github.base_ref }}", text)
        self.assertNotIn("id-token: write", text)
        self.assertNotIn("contents: write", text)
        self.assertIn("CI-Control-Plane-Approval:", text)
        self.assertIn("name: CI Control Plane", text)


if __name__ == "__main__":
    unittest.main()
