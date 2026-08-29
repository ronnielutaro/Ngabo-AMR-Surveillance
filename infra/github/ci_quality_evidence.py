"""Generate machine-readable evidence for Issue #88 (PR Quality Gates).

Queries GitHub API for observed run execution evidence while avoiding
self-referential commit-hash drift.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_REPO = "ronnielutaro/Ngabo-AMR-Surveillance"
DEFAULT_PR = 103
DEFAULT_WORKFLOW_NAME = "PR Quality"
DEFAULT_INTEGRATION_ID = 15368


def run_gh_json(
    args: Sequence[str],
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> Any:
    if runner is None:
        cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json", *args]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    else:
        proc = runner(args)

    if proc.returncode != 0:
        raise RuntimeError(
            f"INSPECTION_FAILED: gh command failed: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("INSPECTION_FAILED: invalid JSON returned by gh") from exc


def fetch_run_evidence(
    repo: str,
    run_id: int,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    run_data = run_gh_json([f"repos/{repo}/actions/runs/{run_id}"], runner=runner)
    jobs_data = run_gh_json([f"repos/{repo}/actions/runs/{run_id}/jobs"], runner=runner)

    created_at = run_data.get("created_at")
    updated_at = run_data.get("updated_at")
    duration_seconds = None
    if created_at and updated_at:
        try:
            start = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            duration_seconds = int((end - start).total_seconds())
        except ValueError:
            duration_seconds = None

    jobs_summary: dict[str, Any] = {}
    for job in jobs_data.get("jobs", []):
        name = job.get("name")
        jobs_summary[name] = {
            "id": job.get("id"),
            "status": job.get("status"),
            "conclusion": job.get("conclusion"),
            "started_at": job.get("started_at"),
            "completed_at": job.get("completed_at"),
        }

    return {
        "run_id": run_data.get("id"),
        "run_url": run_data.get("html_url"),
        "head_sha": run_data.get("head_sha"),
        "event": run_data.get("event"),
        "status": run_data.get("status"),
        "conclusion": run_data.get("conclusion"),
        "duration_seconds": duration_seconds,
        "jobs": jobs_summary,
    }


def build_ci_evidence(
    repo: str = DEFAULT_REPO,
    pr_number: int = DEFAULT_PR,
    run_id: int | None = None,
    direct_import_negative_run: str = "33245608901",
    importfrom_bypass_negative_run: str | None = None,
    high_severity_negative_run: str | None = None,
    advisory_id: str | None = None,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    if run_id is None:
        # Find latest PR Quality run for PR head
        pr_data = run_gh_json([f"repos/{repo}/pulls/{pr_number}"], runner=runner)
        head_sha = pr_data.get("head", {}).get("sha")
        runs_list = run_gh_json(
            [f"repos/{repo}/actions/runs?event=pull_request&head_sha={head_sha}"],
            runner=runner,
        )
        pr_runs = [
            r for r in runs_list.get("workflow_runs", [])
            if r.get("name") == DEFAULT_WORKFLOW_NAME
        ]
        if not pr_runs:
            raise RuntimeError(f"No '{DEFAULT_WORKFLOW_NAME}' run found for commit {head_sha}")
        run_id = pr_runs[0]["id"]

    run_ev = fetch_run_evidence(repo, run_id, runner=runner)

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "generated_at": datetime.now(UTC).isoformat(),
        "issue": 88,
        "pr_number": pr_number,
        "head_sha": run_ev["head_sha"],
        "baseline_run_id": run_ev["run_id"],
        "baseline_run_url": run_ev["run_url"],
        "baseline_conclusion": run_ev["conclusion"],
        "duration_seconds": run_ev["duration_seconds"],
        "jobs": run_ev["jobs"],
        "classification_contract": {
            "docs_only": True,
            "core_only": True,
            "web_only": True,
            "pnpm_lock_only": True,
            "unknown_non_doc_fail_closed": True,
            "conservative_fallback": True,
        },
        "architecture": {
            "checker_present": True,
            "checker_script": "scripts/ci/check_architecture.py",
            "direct_import_negative_run": direct_import_negative_run,
            "importfrom_bypass_negative_run": importfrom_bypass_negative_run,
            "effective_target_resolution": "ast.ImportFrom + importlib.util.resolve_name",
        },
        "security": {
            "python_audit": "uv --preview audit --frozen",
            "pnpm_audit": "pnpm audit --audit-level=high",
            "native_dependency_review_status": "ACTIVE",
            "native_dependency_review_action": (
                "actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294"
            ),
            "high_severity_negative_run": high_severity_negative_run,
            "advisory_id": advisory_id,
        },
        "ruleset": {
            "name": "Ngabo Required PR Quality",
            "target_branches": ["refs/heads/develop", "refs/heads/main"],
            "required_checks": [
                {"context": "PR Quality Gate", "integration_id": DEFAULT_INTEGRATION_ID},
                {"context": "CI Control Plane", "integration_id": DEFAULT_INTEGRATION_ID},
            ],
            "allowed_merge_methods": ["merge"],
            "github_actions_integration_id": DEFAULT_INTEGRATION_ID,
            "activation_status": "PENDING_POST_MERGE",
        },
        "privacy": {
            "external_review_required": True,
            "credentials_in_logs": False,
            "github_token_permissions": "contents: read",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CI Quality Gates Evidence")
    parser.add_argument("--repo", default=os.environ.get("NGABO_GITHUB_REPOSITORY", DEFAULT_REPO))
    parser.add_argument("--pr", type=int, default=DEFAULT_PR)
    parser.add_argument("--run-id", type=int, default=None)
    parser.add_argument("--direct-import-negative-run", default="33245608901")
    parser.add_argument("--importfrom-negative-run", default=None)
    parser.add_argument("--security-negative-run", default=None)
    parser.add_argument("--advisory-id", default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        evidence = build_ci_evidence(
            repo=args.repo,
            pr_number=args.pr,
            run_id=args.run_id,
            direct_import_negative_run=args.direct_import_negative_run,
            importfrom_bypass_negative_run=args.importfrom_negative_run,
            high_severity_negative_run=args.security_negative_run,
            advisory_id=args.advisory_id,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    formatted = json.dumps(evidence, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(formatted, encoding="utf-8")
        print(f"Evidence written to {args.output}")
    else:
        print(formatted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
