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
        self.assertTrue(result.conservative_fallback)

    def test_pnpm_lock_only_requires_web_and_dependency(self):
        result = classify_changes.classify(["pnpm-lock.yaml"])
        self.assertTrue(result.web_required)
        self.assertTrue(result.dependency_changed)
        self.assertFalse(result.core_required)
        self.assertFalse(result.infra_required)
        self.assertFalse(result.docs_only)
        self.assertFalse(result.conservative_fallback)

    def test_apps_web_package_json_requires_web_and_dependency(self):
        result = classify_changes.classify(["apps/web/package.json"])
        self.assertTrue(result.web_required)
        self.assertTrue(result.dependency_changed)
        self.assertFalse(result.core_required)
        self.assertFalse(result.infra_required)
        self.assertFalse(result.docs_only)

    def test_pnpm_lock_and_docs_requires_web_and_is_not_docs_only(self):
        result = classify_changes.classify(["pnpm-lock.yaml", "docs/CI_QUALITY_GATES.md"])
        self.assertTrue(result.web_required)
        self.assertTrue(result.dependency_changed)
        self.assertFalse(result.docs_only)
        self.assertFalse(result.conservative_fallback)

    def test_unknown_dockerfile_fails_closed(self):
        result = classify_changes.classify(["Dockerfile"])
        self.assertTrue(result.core_required)
        self.assertTrue(result.web_required)
        self.assertTrue(result.infra_required)
        self.assertTrue(result.shared_required)
        self.assertFalse(result.docs_only)
        self.assertTrue(result.conservative_fallback)

    def test_unknown_new_root_config_fails_closed(self):
        result = classify_changes.classify(["new-root-config.toml"])
        self.assertTrue(result.core_required)
        self.assertTrue(result.web_required)
        self.assertTrue(result.infra_required)
        self.assertTrue(result.conservative_fallback)

    def test_unknown_github_dependabot_fails_closed(self):
        result = classify_changes.classify([".github/dependabot.yml"])
        self.assertTrue(result.core_required)
        self.assertTrue(result.web_required)
        self.assertTrue(result.infra_required)
        self.assertTrue(result.conservative_fallback)

    def test_unknown_nested_config_fails_closed(self):
        result = classify_changes.classify(["unknown/path/config.xyz"])
        self.assertTrue(result.core_required)
        self.assertTrue(result.web_required)
        self.assertTrue(result.infra_required)
        self.assertTrue(result.conservative_fallback)

    def test_core_pyproject_toml_requires_core_infra_and_dependency(self):
        result = classify_changes.classify(["services/core/pyproject.toml"])
        self.assertTrue(result.core_required)
        self.assertTrue(result.infra_required)
        self.assertFalse(result.web_required)
        self.assertTrue(result.dependency_changed)
        self.assertFalse(result.docs_only)
        self.assertFalse(result.conservative_fallback)

    def test_core_uv_lock_requires_core_infra_and_dependency(self):
        result = classify_changes.classify(["services/core/uv.lock"])
        self.assertTrue(result.core_required)
        self.assertTrue(result.infra_required)
        self.assertFalse(result.web_required)
        self.assertTrue(result.dependency_changed)
        self.assertFalse(result.docs_only)
        self.assertFalse(result.conservative_fallback)

    def test_core_dependency_plus_docs_requires_core_infra(self):
        result = classify_changes.classify(["services/core/pyproject.toml", "docs/PRD.md"])
        self.assertTrue(result.core_required)
        self.assertTrue(result.infra_required)
        self.assertFalse(result.web_required)
        self.assertTrue(result.dependency_changed)
        self.assertFalse(result.docs_only)

    def test_core_dependency_plus_web_requires_core_web_infra(self):
        result = classify_changes.classify(["services/core/uv.lock", "apps/web/package.json"])
        self.assertTrue(result.core_required)
        self.assertTrue(result.infra_required)
        self.assertTrue(result.web_required)
        self.assertTrue(result.dependency_changed)
        self.assertFalse(result.docs_only)

    def test_ordinary_core_source_does_not_require_infra(self):
        result = classify_changes.classify(["services/core/ngabo/domain/models.py"])
        self.assertTrue(result.core_required)
        self.assertFalse(result.infra_required)
        self.assertFalse(result.web_required)
        self.assertFalse(result.dependency_changed)

    def test_ordinary_infra_does_not_require_core(self):
        result = classify_changes.classify(["infra/gcp/main.tf"])
        self.assertTrue(result.infra_required)
        self.assertFalse(result.core_required)
        self.assertFalse(result.web_required)
        self.assertFalse(result.dependency_changed)


if __name__ == "__main__":
    unittest.main()

