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

    def test_whitespace_colon_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n  - uses : actions/checkout@v7\n", encoding="utf-8"
            )
            self.assertEqual(len(check_workflow_pins.scan_file(path)), 1)

    def test_quoted_key_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                'steps:\n  - "uses": actions/checkout@v7\n', encoding="utf-8"
            )
            self.assertEqual(len(check_workflow_pins.scan_file(path)), 1)

    def test_inline_mapping_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n  - { uses: actions/checkout@v7 }\n", encoding="utf-8"
            )
            self.assertEqual(len(check_workflow_pins.scan_file(path)), 1)

    def test_reusable_workflow_job_uses_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "jobs:\n"
                "  call-reusable:\n"
                "    uses: owner/repo/.github/workflows/reuse.yml@main\n",
                encoding="utf-8",
            )
            self.assertEqual(len(check_workflow_pins.scan_file(path)), 1)

    def test_reusable_workflow_job_uses_sha_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "jobs:\n"
                "  call-reusable:\n"
                "    uses: owner/repo/.github/workflows/reuse.yml@3d3c42e5aac5ba805825da76410c181273ba90b1\n",
                encoding="utf-8",
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])

    def test_docker_mutable_tag_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n  - uses: docker://alpine:latest\n", encoding="utf-8"
            )
            self.assertEqual(len(check_workflow_pins.scan_file(path)), 1)

    def test_docker_sha256_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            sha64 = "a" * 64
            path.write_text(
                f"steps:\n  - uses: docker://alpine@sha256:{sha64}\n",
                encoding="utf-8",
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])

    def test_local_action_is_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n  - uses: ./.github/actions/local\n", encoding="utf-8"
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])

    def test_inline_mapping_second_key_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n  - { name: Checkout, uses: actions/checkout@v7 }\n",
                encoding="utf-8",
            )
            self.assertEqual(len(check_workflow_pins.scan_file(path)), 1)

    def test_inline_mapping_second_key_sha_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n  - { name: Checkout, uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 }\n",
                encoding="utf-8",
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])

    def test_semantic_parser_ignores_uses_in_run_script_block(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                'steps:\n  - name: Echo\n    run: |\n      echo "uses: actions/checkout@v7"\n',
                encoding="utf-8",
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])

    def test_pyyaml_missing_fails_closed_by_default(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n",
                encoding="utf-8",
            )
            orig_yaml = check_workflow_pins.yaml
            check_workflow_pins.yaml = None
            try:
                errors = check_workflow_pins.scan_file(path)
                self.assertEqual(len(errors), 1)
                self.assertIn("PyYAML is required", errors[0])
            finally:
                check_workflow_pins.yaml = orig_yaml

    def test_fallback_multiline_uses_fails_when_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "steps:\n  - uses:\n      actions/checkout@v7\n", encoding="utf-8"
            )
            orig_yaml = check_workflow_pins.yaml
            check_workflow_pins.yaml = None
            try:
                self.assertEqual(
                    len(check_workflow_pins.scan_file(path, allow_fallback=True)), 1
                )
            finally:
                check_workflow_pins.yaml = orig_yaml

    def test_fallback_ignores_uses_in_run_script_block_when_allowed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                'steps:\n  - run: echo "uses: documentation"\n', encoding="utf-8"
            )
            orig_yaml = check_workflow_pins.yaml
            check_workflow_pins.yaml = None
            try:
                self.assertEqual(
                    check_workflow_pins.scan_file(path, allow_fallback=True), []
                )
            finally:
                check_workflow_pins.yaml = orig_yaml

    def test_action_input_named_uses_in_with_block_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n"
                "        with:\n"
                "          uses: documentation\n",
                encoding="utf-8",
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])

    def test_workflow_call_input_named_uses_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "on:\n"
                "  workflow_call:\n"
                "    inputs:\n"
                "      uses:\n"
                "        type: string\n"
                "        default: value\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n",
                encoding="utf-8",
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])

    def test_job_level_reusable_workflow_unpinned_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "jobs:\n"
                "  caller:\n"
                "    uses: owner/repo/.github/workflows/reusable.yml@main\n",
                encoding="utf-8",
            )
            errors = check_workflow_pins.scan_file(path)
            self.assertEqual(len(errors), 1)
            self.assertIn("must be pinned to a full 40-hex commit SHA", errors[0])

    def test_job_level_reusable_workflow_sha_pinned_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "ci.yml"
            path.write_text(
                "jobs:\n"
                "  caller:\n"
                "    uses: owner/repo/.github/workflows/reusable.yml@3d3c42e5aac5ba805825da76410c181273ba90b1\n",
                encoding="utf-8",
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])

    def test_composite_action_step_unpinned_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "action.yml"
            path.write_text(
                "runs:\n"
                "  using: composite\n"
                "  steps:\n"
                "    - uses: actions/checkout@v4\n",
                encoding="utf-8",
            )
            errors = check_workflow_pins.scan_file(path)
            self.assertEqual(len(errors), 1)
            self.assertIn("must be pinned to a full 40-hex commit SHA", errors[0])

    def test_composite_action_step_sha_pinned_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "action.yml"
            path.write_text(
                "runs:\n"
                "  using: composite\n"
                "  steps:\n"
                "    - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n",
                encoding="utf-8",
            )
            self.assertEqual(check_workflow_pins.scan_file(path), [])


if __name__ == "__main__":
    unittest.main()
