"""Tests for scripts/ci/collect_pr_files.py — rename-aware CI control-plane protection."""

import pathlib
import sys
import unittest

CI_DIR = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(CI_DIR))
import collect_pr_files  # noqa: E402


class ExtractAllPathsTests(unittest.TestCase):
    """Verify previous_filename extraction."""

    def test_simple_modification_yields_filename_only(self):
        files = [{"filename": "README.md", "status": "modified"}]
        paths = collect_pr_files.extract_all_paths(files)
        self.assertEqual(paths, {"README.md"})

    def test_rename_yields_both_paths(self):
        files = [{
            "filename": "docs/wif-auth-proof.yml",
            "previous_filename": ".github/workflows/wif-auth-proof.yml",
            "status": "renamed",
        }]
        paths = collect_pr_files.extract_all_paths(files)
        self.assertIn("docs/wif-auth-proof.yml", paths)
        self.assertIn(".github/workflows/wif-auth-proof.yml", paths)

    def test_no_previous_filename_field(self):
        files = [{"filename": "apps/web/src/page.tsx"}]
        paths = collect_pr_files.extract_all_paths(files)
        self.assertEqual(paths, {"apps/web/src/page.tsx"})

    def test_deduplicates_paths(self):
        files = [
            {"filename": "README.md"},
            {"filename": "README.md"},
        ]
        paths = collect_pr_files.extract_all_paths(files)
        self.assertEqual(len(paths), 1)


class IsProtectedPathTests(unittest.TestCase):
    """Verify protected path classification."""

    def test_github_workflow(self):
        self.assertTrue(collect_pr_files.is_protected_path(".github/workflows/pr-quality.yml"))

    def test_scripts_ci(self):
        self.assertTrue(collect_pr_files.is_protected_path("scripts/ci/check_architecture.py"))

    def test_infra_github(self):
        self.assertTrue(collect_pr_files.is_protected_path("infra/github/pr_quality_ruleset.py"))

    def test_package_json(self):
        self.assertTrue(collect_pr_files.is_protected_path("package.json"))

    def test_web_tsconfig(self):
        self.assertTrue(collect_pr_files.is_protected_path("apps/web/tsconfig.json"))

    def test_ordinary_docs(self):
        self.assertFalse(collect_pr_files.is_protected_path("docs/README.md"))

    def test_ordinary_core(self):
        self.assertFalse(collect_pr_files.is_protected_path("services/core/ngabo/domain/model.py"))


class ClassifyPrFilesRenameTests(unittest.TestCase):
    """Verify rename-aware classification for CI control-plane protection."""

    def test_protected_source_to_unprotected_destination(self):
        """Renaming a workflow out of .github/workflows/ must be protected."""
        files = [{
            "filename": "docs/wif-auth-proof.yml",
            "previous_filename": ".github/workflows/wif-auth-proof.yml",
            "status": "renamed",
        }]
        protected, _all = collect_pr_files.classify_pr_files(files)
        self.assertIn(".github/workflows/wif-auth-proof.yml", protected)

    def test_unprotected_source_to_protected_destination(self):
        """Moving a docs file into .github/workflows/ must be protected."""
        files = [{
            "filename": ".github/workflows/new-workflow.yml",
            "previous_filename": "docs/new-workflow.yml",
            "status": "renamed",
        }]
        protected, _all = collect_pr_files.classify_pr_files(files)
        self.assertIn(".github/workflows/new-workflow.yml", protected)

    def test_protected_to_protected_rename(self):
        """Renaming within protected paths must detect both."""
        files = [{
            "filename": "scripts/ci/new_name.py",
            "previous_filename": "scripts/ci/old_name.py",
            "status": "renamed",
        }]
        protected, _all = collect_pr_files.classify_pr_files(files)
        self.assertIn("scripts/ci/new_name.py", protected)
        self.assertIn("scripts/ci/old_name.py", protected)

    def test_ordinary_unprotected_modification(self):
        """An ordinary modification of a non-protected path yields no protected paths."""
        files = [{"filename": "services/core/ngabo/domain/model.py", "status": "modified"}]
        protected, _all = collect_pr_files.classify_pr_files(files)
        self.assertEqual(protected, [])

    def test_scripts_ci_to_docs_rename(self):
        """Renaming scripts/ci/foo.py -> docs/foo.py must be protected."""
        files = [{
            "filename": "docs/foo.py",
            "previous_filename": "scripts/ci/foo.py",
            "status": "renamed",
        }]
        protected, _all = collect_pr_files.classify_pr_files(files)
        self.assertIn("scripts/ci/foo.py", protected)

    def test_infra_github_to_docs_rename(self):
        """Renaming infra/github/foo.py -> docs/foo.py must be protected."""
        files = [{
            "filename": "docs/foo.py",
            "previous_filename": "infra/github/foo.py",
            "status": "renamed",
        }]
        protected, _all = collect_pr_files.classify_pr_files(files)
        self.assertIn("infra/github/foo.py", protected)

    def test_package_json_to_docs_rename(self):
        """Renaming package.json -> docs/package.json must be protected."""
        files = [{
            "filename": "docs/package.json",
            "previous_filename": "package.json",
            "status": "renamed",
        }]
        protected, _all = collect_pr_files.classify_pr_files(files)
        self.assertIn("package.json", protected)


if __name__ == "__main__":
    unittest.main()
