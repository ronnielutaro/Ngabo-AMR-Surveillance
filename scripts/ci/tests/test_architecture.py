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

    def test_domain_cannot_import_package_level_infrastructure(self):
        temp, root = self._tree(
            {"domain/service.py": "from ngabo import infrastructure\n"}
        )
        self.addCleanup(temp.cleanup)
        violations = check_architecture.check_tree(root)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].imported, "ngabo.infrastructure")
        self.assertIn("outer Ngabo layer", violations[0].reason)

    def test_domain_cannot_relative_import_infrastructure(self):
        temp, root = self._tree(
            {"domain/service.py": "from ..infrastructure import repository\n"}
        )
        self.addCleanup(temp.cleanup)
        violations = check_architecture.check_tree(root)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].imported, "ngabo.infrastructure")

    def test_domain_cannot_relative_import_infrastructure_alias(self):
        temp, root = self._tree(
            {"domain/service.py": "from .. import infrastructure\n"}
        )
        self.addCleanup(temp.cleanup)
        violations = check_architecture.check_tree(root)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].imported, "ngabo.infrastructure")

    def test_domain_cannot_plain_import_infrastructure(self):
        temp, root = self._tree(
            {"domain/service.py": "import ngabo.infrastructure\n"}
        )
        self.addCleanup(temp.cleanup)
        violations = check_architecture.check_tree(root)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].imported, "ngabo.infrastructure")

    def test_domain_cannot_plain_import_infrastructure_submodule(self):
        temp, root = self._tree(
            {"domain/service.py": "import ngabo.infrastructure.repository\n"}
        )
        self.addCleanup(temp.cleanup)
        violations = check_architecture.check_tree(root)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].imported, "ngabo.infrastructure.repository")

    def test_domain_can_relative_import_sibling(self):
        temp, root = self._tree(
            {
                "domain/models.py": "class Model: pass\n",
                "domain/service.py": "from .models import Model\nfrom . import models\n",
            }
        )
        self.addCleanup(temp.cleanup)
        self.assertEqual(check_architecture.check_tree(root), [])

    def test_domain_subpackage_can_relative_import_parent_domain(self):
        temp, root = self._tree(
            {
                "domain/models.py": "class Model: pass\n",
                "domain/sub/service.py": "from ..models import Model\nfrom .. import models\n",
            }
        )
        self.addCleanup(temp.cleanup)
        self.assertEqual(check_architecture.check_tree(root), [])

    def test_application_cannot_import_interfaces(self):
        temp, root = self._tree(
            {"application/use_case.py": "from ngabo.interfaces.api import route\n"}
        )
        self.addCleanup(temp.cleanup)
        self.assertEqual(len(check_architecture.check_tree(root)), 1)

    def test_application_cannot_relative_import_interfaces(self):
        temp, root = self._tree(
            {"application/use_case.py": "from ..interfaces import api\n"}
        )
        self.addCleanup(temp.cleanup)
        violations = check_architecture.check_tree(root)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].imported, "ngabo.interfaces")

    def test_application_cannot_relative_import_bootstrap(self):
        temp, root = self._tree(
            {"application/use_case.py": "from ..bootstrap import container\n"}
        )
        self.addCleanup(temp.cleanup)
        violations = check_architecture.check_tree(root)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].imported, "ngabo.bootstrap")

    def test_application_can_import_domain_relative_and_absolute(self):
        temp, root = self._tree(
            {
                "domain/entities.py": "class Entity: pass\n",
                "application/use_case.py": (
                    "from ngabo.domain.entities import Entity\n"
                    "from ..domain.entities import Entity as E2\n"
                ),
            }
        )
        self.addCleanup(temp.cleanup)
        self.assertEqual(check_architecture.check_tree(root), [])

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

