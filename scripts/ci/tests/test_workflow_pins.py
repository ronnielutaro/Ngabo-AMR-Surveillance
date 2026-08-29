import pathlib
import sys
import tempfile
import unittest

CI_DIR = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(CI_DIR))
import check_workflow_pins  # noqa: E402


class WorkflowPinTests(unittest.TestCase):
    def test_full_sha_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n"
                "  - uses: actions/checkout@"
                "3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1\n",
                encoding="utf-8",
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])

    def test_mutable_tag_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n  - uses: actions/checkout@v7\n", encoding="utf-8"
            )
            self.assertEqual(len(check_workflow_pins.scan_file(path)), 1)

    def test_local_action_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n  - uses: ./.github/actions/local\n", encoding="utf-8"
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])


if __name__ == "__main__":
    unittest.main()
