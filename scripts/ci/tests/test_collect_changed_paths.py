"""Tests for scripts/ci/collect_changed_paths.py — rename-aware path parsing."""

import pathlib
import sys
import unittest

CI_DIR = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(CI_DIR))
import collect_changed_paths  # noqa: E402
import classify_changes  # noqa: E402


class ParseNameStatusZTests(unittest.TestCase):
    """Verify NUL-separated --name-status -z parsing."""

    # -------------------------------------------------------------------
    # Core semantics
    # -------------------------------------------------------------------

    def test_ordinary_modification(self):
        raw = "M\0services/core/ngabo/domain/model.py\0"
        paths = collect_changed_paths.parse_name_status_z(raw)
        self.assertEqual(paths, {"services/core/ngabo/domain/model.py"})

    def test_ordinary_addition(self):
        raw = "A\0services/core/ngabo/new_file.py\0"
        paths = collect_changed_paths.parse_name_status_z(raw)
        self.assertEqual(paths, {"services/core/ngabo/new_file.py"})

    def test_ordinary_deletion(self):
        raw = "D\0services/core/ngabo/old_file.py\0"
        paths = collect_changed_paths.parse_name_status_z(raw)
        self.assertEqual(paths, {"services/core/ngabo/old_file.py"})

    def test_rename_captures_both_source_and_destination(self):
        raw = "R100\0services/core/ngabo/domain/foo.py\0docs/foo.py\0"
        paths = collect_changed_paths.parse_name_status_z(raw)
        self.assertIn("services/core/ngabo/domain/foo.py", paths)
        self.assertIn("docs/foo.py", paths)
        self.assertEqual(len(paths), 2)

    def test_copy_captures_both_source_and_destination(self):
        raw = "C100\0services/core/ngabo/util.py\0apps/web/src/util.py\0"
        paths = collect_changed_paths.parse_name_status_z(raw)
        self.assertIn("services/core/ngabo/util.py", paths)
        self.assertIn("apps/web/src/util.py", paths)

    def test_rename_with_similarity_index(self):
        raw = "R087\0old_name.py\0new_name.py\0"
        paths = collect_changed_paths.parse_name_status_z(raw)
        self.assertEqual(paths, {"old_name.py", "new_name.py"})

    def test_mixed_statuses(self):
        raw = (
            "M\0README.md\0"
            "R100\0services/core/ngabo/domain/foo.py\0docs/foo.py\0"
            "A\0apps/web/src/new.tsx\0"
            "D\0old_config.toml\0"
        )
        paths = collect_changed_paths.parse_name_status_z(raw)
        expected = {
            "README.md",
            "services/core/ngabo/domain/foo.py",
            "docs/foo.py",
            "apps/web/src/new.tsx",
            "old_config.toml",
        }
        self.assertEqual(paths, expected)

    def test_empty_input(self):
        paths = collect_changed_paths.parse_name_status_z("")
        self.assertEqual(paths, set())

    def test_filename_with_spaces(self):
        raw = "M\0docs/my file with spaces.md\0"
        paths = collect_changed_paths.parse_name_status_z(raw)
        self.assertEqual(paths, {"docs/my file with spaces.md"})

    def test_rename_with_spaces_in_both_paths(self):
        raw = "R100\0services/core/ngabo/my module.py\0docs/my module.py\0"
        paths = collect_changed_paths.parse_name_status_z(raw)
        self.assertIn("services/core/ngabo/my module.py", paths)
        self.assertIn("docs/my module.py", paths)

    def test_type_change(self):
        raw = "T\0some/symlink\0"
        paths = collect_changed_paths.parse_name_status_z(raw)
        self.assertEqual(paths, {"some/symlink"})


class RenameClassificationIntegrationTests(unittest.TestCase):
    """Verify that rename-collected paths feed correctly into classify()."""

    def _classify_rename(self, old: str, new: str):
        """Helper: simulate a rename and classify the result set."""
        raw = f"R100\0{old}\0{new}\0"
        paths = collect_changed_paths.parse_name_status_z(raw)
        return classify_changes.classify(paths)

    def test_core_to_docs_rename_requires_core(self):
        result = self._classify_rename(
            "services/core/ngabo/domain/foo.py", "docs/foo.py"
        )
        self.assertTrue(result.core_required)
        self.assertFalse(result.docs_only)

    def test_docs_to_core_rename_requires_core(self):
        result = self._classify_rename(
            "docs/design.md", "services/core/ngabo/design.py"
        )
        self.assertTrue(result.core_required)
        self.assertFalse(result.docs_only)

    def test_web_to_docs_rename_requires_web(self):
        result = self._classify_rename(
            "apps/web/src/page.tsx", "docs/page.md"
        )
        self.assertTrue(result.web_required)
        self.assertFalse(result.docs_only)

    def test_infra_to_docs_rename_requires_infra(self):
        result = self._classify_rename(
            "infra/gcp/bootstrap.py", "docs/bootstrap.md"
        )
        self.assertTrue(result.infra_required)
        self.assertFalse(result.docs_only)

    def test_unknown_to_docs_rename_conservative_fallback(self):
        result = self._classify_rename(
            "something/unknown/file.xyz", "docs/file.md"
        )
        self.assertTrue(result.core_required)
        self.assertTrue(result.web_required)
        self.assertTrue(result.infra_required)
        self.assertTrue(result.conservative_fallback)
        self.assertFalse(result.docs_only)

    def test_ci_workflow_to_docs_rename_is_ci_control_plane(self):
        result = self._classify_rename(
            ".github/workflows/wif-auth-proof.yml", "docs/wif-auth-proof.yml"
        )
        self.assertTrue(result.ci_control_plane_changed)
        self.assertTrue(result.core_required)
        self.assertTrue(result.web_required)
        self.assertTrue(result.infra_required)
        self.assertFalse(result.docs_only)


if __name__ == "__main__":
    unittest.main()
