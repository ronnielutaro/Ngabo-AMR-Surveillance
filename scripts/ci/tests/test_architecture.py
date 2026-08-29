import pathlib
import sys
import tempfile
import unittest

CI_DIR = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(CI_DIR))
import check_architecture  # noqa: E402


class ArchitectureTests(unittest.TestCase):
    def _tree(self, file_map):
        temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(temp.name)
        for relative, content in file_map.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return temp, root

    def test_domain_can_import_domain(self):
        temp, root = self._tree(
            {"domain/service.py": "from ngabo.domain.entities import Incident\n"}
        )
        self.addCleanup(temp.cleanup)
        self.assertEqual(check_architecture.check_tree(root), [])

    def test_domain_cannot_import_infrastructure(self):
        temp, root = self._tree(
            {"domain/service.py": "from ngabo.infrastructure.db import Repo\n"}
        )
        self.addCleanup(temp.cleanup)
        violations = check_architecture.check_tree(root)
        self.assertEqual(len(violations), 1)
        self.assertIn("outer Ngabo layer", violations[0].reason)

    def test_application_cannot_import_interfaces(self):
        temp, root = self._tree(
            {"application/use_case.py": "from ngabo.interfaces.api import route\n"}
        )
        self.addCleanup(temp.cleanup)
        self.assertEqual(len(check_architecture.check_tree(root)), 1)

    def test_inner_layers_cannot_import_vendor_sdk(self):
        temp, root = self._tree(
            {"application/use_case.py": "from google.cloud import firestore\n"}
        )
        self.addCleanup(temp.cleanup)
        violations = check_architecture.check_tree(root)
        self.assertEqual(len(violations), 1)
        self.assertIn("framework/cloud/network", violations[0].reason)


if __name__ == "__main__":
    unittest.main()
