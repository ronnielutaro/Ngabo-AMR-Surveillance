import pathlib
import sys
import unittest

CI_DIR = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(CI_DIR))
import classify_changes  # noqa: E402


class ClassificationTests(unittest.TestCase):
    def test_core_only(self):
        result = classify_changes.classify(["services/core/ngabo/domain/model.py"])
        self.assertTrue(result.core_required)
        self.assertFalse(result.web_required)
        self.assertFalse(result.infra_required)

    def test_web_only(self):
        result = classify_changes.classify(["apps/web/src/app/page.tsx"])
        self.assertTrue(result.web_required)
        self.assertFalse(result.core_required)
        self.assertFalse(result.infra_required)

    def test_infra_only(self):
        result = classify_changes.classify(["infra/gcp/bootstrap.py"])
        self.assertTrue(result.infra_required)
        self.assertFalse(result.core_required)
        self.assertFalse(result.web_required)

    def test_shared_ci_change_runs_all_lanes(self):
        result = classify_changes.classify([".github/workflows/pr-quality.yml"])
        self.assertTrue(result.core_required)
        self.assertTrue(result.web_required)
        self.assertTrue(result.infra_required)
        self.assertTrue(result.ci_control_plane_changed)

    def test_root_package_change_runs_all_lanes(self):
        result = classify_changes.classify(["package.json"])
        self.assertTrue(result.core_required)
        self.assertTrue(result.web_required)
        self.assertTrue(result.infra_required)

    def test_docs_only_skips_expensive_lanes(self):
        result = classify_changes.classify(["docs/CI_QUALITY_GATES.md", "README.md"])
        self.assertTrue(result.docs_only)
        self.assertFalse(result.core_required)
        self.assertFalse(result.web_required)
        self.assertFalse(result.infra_required)

    def test_empty_diff_fails_safe(self):
        result = classify_changes.classify([])
        self.assertTrue(result.core_required)
        self.assertTrue(result.web_required)
        self.assertTrue(result.infra_required)
        self.assertTrue(result.ci_control_plane_changed)


if __name__ == "__main__":
    unittest.main()
