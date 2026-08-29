"""Repository-owned live PR control plane validation for Ngabo PR CI."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

DEFAULT_APPROVAL_PREFIX = "CI-Control-Plane-Approval:"


class ControlPlaneValidationError(Exception):
    """Raised when control plane validation fails or a race condition occurs."""


@dataclass(frozen=True)
class LivePrMetadata:
    number: int
    head_sha: str
    user_login: str
    body: str
    changed_files: int
    updated_at: str


def run_gh_json(
    endpoint: str,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    cmd = ["gh", "api", endpoint]
    if runner is None:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    else:
        proc = runner(cmd)

    if proc.returncode != 0:
        raise ControlPlaneValidationError(
            f"GitHub API call to {endpoint} failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )

    try:
        data = json.loads(proc.stdout)
    except Exception as exc:
        raise ControlPlaneValidationError(
            f"Failed to parse JSON from GitHub API endpoint {endpoint}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ControlPlaneValidationError(
            f"Expected dict JSON response from {endpoint}, got {type(data).__name__}"
        )

    return data


def fetch_live_pr(
    repo: str,
    pr_number: int,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> LivePrMetadata:
    endpoint = f"repos/{repo}/pulls/{pr_number}"
    data = run_gh_json(endpoint, runner=runner)

    head_sha = data.get("head", {}).get("sha", "")
    user_login = data.get("user", {}).get("login", "")
    body = data.get("body") or ""
    changed_files = data.get("changed_files", 0)
    updated_at = data.get("updated_at", "")

    if not head_sha or not user_login:
        raise ControlPlaneValidationError(
            f"PR #{pr_number} metadata from API missing head SHA or user login"
        )

    return LivePrMetadata(
        number=pr_number,
        head_sha=head_sha,
        user_login=user_login,
        body=body,
        changed_files=changed_files,
        updated_at=updated_at,
    )


def extract_approval_sha(body: str) -> str | None:
    for line in body.splitlines():
        line = line.strip()
        if line.startswith(DEFAULT_APPROVAL_PREFIX):
            return line[len(DEFAULT_APPROVAL_PREFIX):].strip()
    return None


def is_protected_path(path: str) -> bool:
    path = path.strip()
    if (
        path.startswith(".github/workflows/")
        or path.startswith("scripts/ci/")
        or path.startswith("infra/github/")
    ):
        return True
    if path in (
        "package.json",
        "pnpm-lock.yaml",
        "pnpm-workspace.yaml",
        "services/core/pyproject.toml",
        "services/core/uv.lock",
    ):
        return True
    if path.startswith("apps/web/"):
        rel = path[len("apps/web/"):]
        if rel in (
            "package.json",
            "tsconfig.json",
            "tsconfig.node.json",
            "eslint.config.js",
            "vitest.config.ts",
            "next.config.js",
            "postcss.config.js",
        ) or (
            rel.startswith("tsconfig")
            or rel.startswith("eslint.config")
            or rel.startswith("vitest.config")
            or rel.startswith("next.config")
            or rel.startswith("postcss.config")
        ):
            return True
    return False


def fetch_changed_files_list(
    repo: str,
    pr_number: int,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> list[str]:
    endpoint = f"repos/{repo}/pulls/{pr_number}/files?per_page=100"
    cmd = [
        "gh",
        "api",
        "--paginate",
        endpoint,
        "--jq",
        ".[] | .filename, (.previous_filename // empty)",
    ]
    if runner is None:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    else:
        proc = runner(cmd)

    if proc.returncode != 0:
        raise ControlPlaneValidationError(
            f"Failed to fetch PR #{pr_number} files (exit {proc.returncode}): {proc.stderr.strip()}"
        )

    paths = [p.strip() for p in proc.stdout.splitlines() if p.strip()]
    return sorted(list(set(paths)))


def post_commit_status(
    repo: str,
    head_sha: str,
    state: str,
    description: str,
    pr_number: int | None = None,
    repo_owner: str | None = None,
    protected_paths: list[str] | None = None,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> None:
    # Atomic re-check directly before posting final status to eliminate TOCTOU window
    if state == "success" and pr_number is not None and protected_paths and repo_owner:
        live = fetch_live_pr(repo, pr_number, runner=runner)
        if live.head_sha != head_sha:
            raise ControlPlaneValidationError(
                f"TOCTOU RACE DETECTED: PR #{pr_number} live head SHA changed to '{live.head_sha}' immediately before status post."
            )
        if live.user_login != repo_owner:
            raise ControlPlaneValidationError(
                f"TOCTOU RACE DETECTED: PR #{pr_number} author changed to '{live.user_login}' immediately before status post."
            )
        approval_sha = extract_approval_sha(live.body)
        if not approval_sha or approval_sha != head_sha:
            raise ControlPlaneValidationError(
                f"TOCTOU RACE DETECTED: PR #{pr_number} approval marker removed immediately before status post."
            )

    endpoint = f"repos/{repo}/statuses/{head_sha}"
    cmd = [
        "gh",
        "api",
        endpoint,
        "-f",
        f"state={state}",
        "-f",
        "context=CI Control Plane",
        "-f",
        f"description={description}",
    ]
    if runner is None:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    else:
        proc = runner(cmd)

    if proc.returncode != 0:
        raise ControlPlaneValidationError(
            f"Failed to post commit status to {head_sha} (exit {proc.returncode}): {proc.stderr.strip()}"
        )


def validate_control_plane(
    repo: str,
    pr_number: int,
    repo_owner: str,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> tuple[LivePrMetadata, list[str]]:
    """Perform initial live PR fetch, protection check, and approval verification."""
    meta = fetch_live_pr(repo, pr_number, runner=runner)

    if meta.changed_files > 3000:
        raise ControlPlaneValidationError(
            f"PR #{pr_number} changed file count ({meta.changed_files}) exceeds API limit of 3000 files."
        )

    post_commit_status(
        repo,
        meta.head_sha,
        "pending",
        "Evaluating CI Control Plane protection...",
        runner=runner,
    )

    all_paths = fetch_changed_files_list(repo, pr_number, runner=runner)
    protected_paths = [p for p in all_paths if is_protected_path(p)]

    if not protected_paths:
        return meta, protected_paths

    if meta.user_login != repo_owner:
        raise ControlPlaneValidationError(
            f"PR #{pr_number} modifies protected paths {protected_paths} but author '{meta.user_login}' "
            f"is not repository owner '{repo_owner}'."
        )

    approval_sha = extract_approval_sha(meta.body)
    if not approval_sha or approval_sha != meta.head_sha:
        raise ControlPlaneValidationError(
            f"PR #{pr_number} modifies protected paths {protected_paths} but live PR body "
            f"lacks valid approval marker for current live head SHA '{meta.head_sha}' "
            f"(found: {approval_sha!r})"
        )

    return meta, protected_paths


def verify_final_race(
    repo: str,
    pr_number: int,
    initial_meta: LivePrMetadata,
    repo_owner: str,
    protected_paths: list[str],
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> LivePrMetadata:
    """Re-fetch live PR metadata immediately before attaching final status to guarantee no race occurred."""
    final_meta = fetch_live_pr(repo, pr_number, runner=runner)

    if final_meta.head_sha != initial_meta.head_sha:
        raise ControlPlaneValidationError(
            f"RACE DETECTED: PR #{pr_number} live head SHA changed from '{initial_meta.head_sha}' "
            f"to '{final_meta.head_sha}' during validation."
        )

    if final_meta.updated_at != initial_meta.updated_at:
        if protected_paths:
            if final_meta.user_login != repo_owner:
                raise ControlPlaneValidationError(
                    "RACE DETECTED: PR author changed during validation and is no longer repository owner."
                )
            approval_sha = extract_approval_sha(final_meta.body)
            if not approval_sha or approval_sha != final_meta.head_sha:
                raise ControlPlaneValidationError(
                    "RACE DETECTED: PR body updated during validation and approval marker was removed."
                )

    return final_meta


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number_str = os.environ.get("PR_NUMBER")
    repo_owner = os.environ.get("REPOSITORY_OWNER")

    if not repo or not pr_number_str or not repo_owner:
        print("Missing required env vars: GITHUB_REPOSITORY, PR_NUMBER, REPOSITORY_OWNER", file=sys.stderr)
        return 1

    try:
        pr_number = int(pr_number_str)
    except ValueError:
        print(f"Invalid PR_NUMBER: {pr_number_str}", file=sys.stderr)
        return 1

    try:
        initial_meta, protected = validate_control_plane(repo, pr_number, repo_owner)
        final_meta = verify_final_race(repo, pr_number, initial_meta, repo_owner, protected)
        post_commit_status(
            repo,
            final_meta.head_sha,
            "success",
            "CI Control Plane checks passed against live PR metadata.",
            pr_number=pr_number,
            repo_owner=repo_owner,
            protected_paths=protected,
        )
        print(f"Control plane check passed for PR #{pr_number} (head SHA {final_meta.head_sha}).")
        return 0
    except ControlPlaneValidationError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        # Attempt to attach failure status if head SHA is known
        try:
            live = fetch_live_pr(repo, pr_number)
            post_commit_status(repo, live.head_sha, "failure", str(exc))
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
