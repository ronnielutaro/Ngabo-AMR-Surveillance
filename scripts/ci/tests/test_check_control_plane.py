from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import unittest
from unittest import mock
from typing import Any

CI_DIR = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(CI_DIR))
import check_control_plane  # noqa: E402


class FakeProcess:
    def __init__(self, returncode: int, stdout: str, stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _make_runner(*responses: FakeProcess):
    call_index = 0

    def runner(cmd: Any) -> FakeProcess:
        nonlocal call_index
        if call_index >= len(responses):
            return FakeProcess(1, "", "no more fake responses")
        resp = responses[call_index]
        call_index += 1
        return resp

    return runner


def _make_pr_data(
    number: int = 103,
    head_sha: str = "b950ba3ed4126fcf0138c6b101bda34d3f9ad8df",
    user_login: str = "contributor",
    body: str = "CI-Control-Plane-Approval: b950ba3ed4126fcf0138c6b101bda34d3f9ad8df",
    changed_files: int = 2,
    updated_at: str = "2026-08-29T12:00:00Z",
) -> dict[str, Any]:
    return {
        "number": number,
        "head": {"sha": head_sha},
        "user": {"login": user_login},
        "body": body,
        "changed_files": changed_files,
        "updated_at": updated_at,
    }


class ControlPlaneRaceTests(unittest.TestCase):
    def test_old_event_has_valid_marker_but_live_body_marker_removed_fails(self):
        # Event payload was valid, but GET /repos/{repo}/pulls/{number} returns body with no approval marker
        live_pr_no_marker = _make_pr_data(
            user_login="owner",
            body="No approval marker here!",
        )
        runner = _make_runner(
            FakeProcess(0, json.dumps(live_pr_no_marker)),  # fetch live PR
            FakeProcess(0, ""),                             # post status pending
            FakeProcess(0, ".github/workflows/ci.yml"),      # fetch PR files list
        )
        with self.assertRaises(check_control_plane.ControlPlaneValidationError) as ctx:
            check_control_plane.validate_control_plane("owner/repo", 103, "owner", runner=runner)
        self.assertIn("lacks valid approval marker", str(ctx.exception))

    def test_non_owner_author_modifying_protected_paths_fails(self):
        live_pr_non_owner = _make_pr_data(
            user_login="contributor",
            body="CI-Control-Plane-Approval: b950ba3ed4126fcf0138c6b101bda34d3f9ad8df",
        )
        runner = _make_runner(
            FakeProcess(0, json.dumps(live_pr_non_owner)),
            FakeProcess(0, ""),
            FakeProcess(0, ".github/workflows/ci.yml"),
        )
        with self.assertRaises(check_control_plane.ControlPlaneValidationError) as ctx:
            check_control_plane.validate_control_plane("owner/repo", 103, "owner", runner=runner)
        self.assertIn("is not repository owner", str(ctx.exception))

    def test_old_event_invalid_marker_live_body_valid_marker_evaluates_live(self):
        # Event payload had no marker, but LIVE PR body contains valid approval marker
        live_pr_valid = _make_pr_data(
            user_login="owner",
            body="CI-Control-Plane-Approval: b950ba3ed4126fcf0138c6b101bda34d3f9ad8df",
        )
        runner = _make_runner(
            FakeProcess(0, json.dumps(live_pr_valid)),     # fetch live PR
            FakeProcess(0, ""),                             # post status pending
            FakeProcess(0, ".github/workflows/ci.yml"),      # fetch PR files list
        )
        meta, protected = check_control_plane.validate_control_plane("owner/repo", 103, "owner", runner=runner)
        self.assertEqual(meta.head_sha, "b950ba3ed4126fcf0138c6b101bda34d3f9ad8df")
        self.assertEqual(protected, [".github/workflows/ci.yml"])

    def test_live_head_differs_from_event_head_binds_to_live_head(self):
        # Live head SHA is new_head_sha, approval marker matches new_head_sha
        live_pr = _make_pr_data(
            user_login="owner",
            head_sha="1111222233334444555566667777888899990000",
            body="CI-Control-Plane-Approval: 1111222233334444555566667777888899990000",
        )
        runner = _make_runner(
            FakeProcess(0, json.dumps(live_pr)),        # fetch live PR
            FakeProcess(0, ""),                        # post status pending to live head!
            FakeProcess(0, ".github/workflows/ci.yml"), # fetch PR files
        )
        meta, _ = check_control_plane.validate_control_plane("owner/repo", 103, "owner", runner=runner)
        self.assertEqual(meta.head_sha, "1111222233334444555566667777888899990000")

    def test_head_sha_changes_between_initial_and_final_revalidation_fails_closed(self):
        # Initial live fetch has sha1, but re-fetch immediately before final status has sha2 -> RACE DETECTED
        initial_meta = check_control_plane.LivePrMetadata(
            number=103,
            head_sha="b950ba3ed4126fcf0138c6b101bda34d3f9ad8df",
            user_login="contributor",
            body="CI-Control-Plane-Approval: b950ba3ed4126fcf0138c6b101bda34d3f9ad8df",
            changed_files=1,
            updated_at="2026-08-29T12:00:00Z",
        )
        raced_pr = _make_pr_data(
            head_sha="9999999999999999999999999999999999999999",
            updated_at="2026-08-29T12:00:05Z",
        )
        runner = _make_runner(
            FakeProcess(0, json.dumps(raced_pr)),  # final revalidation fetch
        )
        with self.assertRaises(check_control_plane.ControlPlaneValidationError) as ctx:
            check_control_plane.verify_final_race(
                "owner/repo", 103, initial_meta, "owner", [".github/workflows/ci.yml"], runner=runner
            )
        self.assertIn("RACE DETECTED", str(ctx.exception))

    def test_approval_removed_between_initial_and_final_revalidation_fails_closed(self):
        initial_meta = check_control_plane.LivePrMetadata(
            number=103,
            head_sha="b950ba3ed4126fcf0138c6b101bda34d3f9ad8df",
            user_login="contributor",
            body="CI-Control-Plane-Approval: b950ba3ed4126fcf0138c6b101bda34d3f9ad8df",
            changed_files=1,
            updated_at="2026-08-29T12:00:00Z",
        )
        body_updated_pr = _make_pr_data(
            head_sha="b950ba3ed4126fcf0138c6b101bda34d3f9ad8df",
            body="Approval removed during validation run!",
            updated_at="2026-08-29T12:00:02Z",
        )
        runner = _make_runner(
            FakeProcess(0, json.dumps(body_updated_pr)),  # final revalidation fetch
        )
        with self.assertRaises(check_control_plane.ControlPlaneValidationError) as ctx:
            check_control_plane.verify_final_race(
                "owner/repo", 103, initial_meta, "owner", [".github/workflows/ci.yml"], runner=runner
            )
        self.assertIn("RACE DETECTED", str(ctx.exception))

    def test_pnpm_lock_and_uv_lock_are_protected_paths(self):
        self.assertTrue(check_control_plane.is_protected_path("pnpm-lock.yaml"))
        self.assertTrue(check_control_plane.is_protected_path("services/core/uv.lock"))
        self.assertTrue(check_control_plane.is_protected_path("package.json"))
        self.assertTrue(check_control_plane.is_protected_path("services/core/pyproject.toml"))
        self.assertFalse(check_control_plane.is_protected_path("docs/README.md"))

    def test_stale_failure_not_posted_to_new_live_head(self):
        # When validation fails because the head advanced mid-run, the failure
        # status must be attached only to the head that was validated; the
        # live PR must never be re-fetched to attach a stale failure to the
        # new head (which would race with the newer run's own status).
        posted: list[tuple[str, str]] = []

        def fake_post(repo, head_sha, state, description, **kwargs):
            posted.append((head_sha, state))

        def fake_validate(repo, pr_number, repo_owner, runner=None):
            meta = check_control_plane.LivePrMetadata(
                number=pr_number,
                head_sha="validatedsha00000000000000000000000000000000",
                user_login="owner",
                body="CI-Control-Plane-Approval: validatedsha00000000000000000000000000000000",
                changed_files=1,
                updated_at="2026-08-29T12:00:00Z",
            )
            return meta, [".github/workflows/ci.yml"]

        def fake_verify(repo, pr_number, initial_meta, repo_owner, protected_paths, runner=None):
            raise check_control_plane.ControlPlaneValidationError(
                "RACE DETECTED: PR head changed during validation"
            )

        env = dict(os.environ)
        try:
            os.environ["GITHUB_REPOSITORY"] = "owner/repo"
            os.environ["PR_NUMBER"] = "103"
            os.environ["REPOSITORY_OWNER"] = "owner"
            with mock.patch.object(
                check_control_plane, "validate_control_plane", fake_validate
            ), mock.patch.object(
                check_control_plane, "verify_final_race", fake_verify
            ), mock.patch.object(
                check_control_plane, "post_commit_status", fake_post
            ), mock.patch.object(
                check_control_plane,
                "fetch_live_pr",
                side_effect=AssertionError(
                    "fetch_live_pr must not run in the failure path"
                ),
            ) as mock_fetch:
                rc = check_control_plane.main()
                self.assertEqual(rc, 1)
                mock_fetch.assert_not_called()
        finally:
            os.environ.clear()
            os.environ.update(env)

        self.assertEqual(
            posted, [("validatedsha00000000000000000000000000000000", "failure")]
        )

    def test_local_action_subtree_is_protected(self):
        # Entire .github/actions/** subtree is CI control-plane code: manifests
        # and any helper scripts they invoke are executable in the runner.
        self.assertTrue(check_control_plane.is_protected_path(".github/actions/build/action.yml"))
        self.assertTrue(check_control_plane.is_protected_path(".github/actions/build/action.yaml"))
        self.assertTrue(check_control_plane.is_protected_path(".github/actions/build/build.sh"))
        self.assertTrue(check_control_plane.is_protected_path(".github/actions/build/nested/bar.py"))


if __name__ == "__main__":
    unittest.main()
