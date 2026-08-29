"""Generate machine-readable evidence for Issue #88 (PR Quality Gates).

Queries GitHub API for observed run execution evidence with strict
validation of the PR/run relationship before emitting any evidence.

Evidence output separates:
  - ``observed``: values fetched from GitHub API
  - ``contract``: repository policy assertions verified by tests
  - ``historical_negative_proofs``: explicit run references for bypass proofs
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
DEFAULT_WORKFLOW_PATH = ".github/workflows/pr-quality.yml"
DEFAULT_INTEGRATION_ID = 15368

# Jobs that MUST complete successfully for valid baseline evidence
REQUIRED_JOBS = frozenset({
    "Changed Paths",
    "CI Policy",
    "Dependency Review",
    "Dependency Security",
    "PR Quality Gate",
})

# Jobs that may be skipped based on changed-paths classification
OPTIONAL_LANE_JOBS = frozenset({
    "Core Quality",
    "Web Quality",
    "Infrastructure Regression",
})


class EvidenceValidationError(Exception):
    """Raised when evidence validation fails."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"EVIDENCE_VALIDATION_FAILED: {reason}")
        self.reason = reason


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
        raise EvidenceValidationError(
            f"gh API call failed: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise EvidenceValidationError("invalid JSON returned by gh") from exc


def validate_run_against_pr(
    run_data: dict[str, Any],
    pr_data: dict[str, Any],
    pr_number: int,
    run_id: int,
) -> None:
    """Validate that the run is a successful PR Quality run for the given PR.

    Raises EvidenceValidationError on any mismatch.
    """
    # --- PR validation ---
    actual_pr_number = pr_data.get("number")
    if actual_pr_number != pr_number:
        raise EvidenceValidationError(
            f"PR number mismatch: requested {pr_number}, got {actual_pr_number}"
        )

    # --- Run ID validation ---
    actual_run_id = run_data.get("id")
    if actual_run_id != run_id:
        raise EvidenceValidationError(
            f"run ID mismatch: requested {run_id}, got {actual_run_id}"
        )

    # --- Workflow name ---
    run_name = run_data.get("name", "")
    if run_name != DEFAULT_WORKFLOW_NAME:
        raise EvidenceValidationError(
            f"wrong workflow name: expected '{DEFAULT_WORKFLOW_NAME}', got '{run_name}'"
        )

    # --- Workflow path (when available) ---
    run_path = run_data.get("path", "")
    if run_path and run_path != DEFAULT_WORKFLOW_PATH:
        raise EvidenceValidationError(
            f"wrong workflow path: expected '{DEFAULT_WORKFLOW_PATH}', got '{run_path}'"
        )

    # --- Event type ---
    event = run_data.get("event", "")
    if event != "pull_request":
        raise EvidenceValidationError(
            f"wrong event: expected 'pull_request', got '{event}'"
        )

    # --- Status ---
    status = run_data.get("status", "")
    if status != "completed":
        raise EvidenceValidationError(
            f"run not completed: status is '{status}'"
        )

    # --- Conclusion ---
    conclusion = run_data.get("conclusion", "")
    if conclusion != "success":
        raise EvidenceValidationError(
            f"run did not succeed: conclusion is '{conclusion}'"
        )

    # --- Head SHA match ---
    run_head_sha = run_data.get("head_sha", "")
    pr_head_sha = pr_data.get("head", {}).get("sha", "")
    if run_head_sha != pr_head_sha:
        raise EvidenceValidationError(
            f"run head does not match PR head: "
            f"run={run_head_sha}, PR={pr_head_sha}"
        )

    # --- PR association ---
    run_prs = run_data.get("pull_requests", [])
    associated_pr_numbers = {pr.get("number") for pr in run_prs}
    if pr_number not in associated_pr_numbers:
        raise EvidenceValidationError(
            f"run is not associated with PR #{pr_number}: "
            f"associated PRs = {sorted(associated_pr_numbers)}"
        )


def validate_jobs(
    jobs_data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Validate job-level requirements and return jobs summary.

    Raises EvidenceValidationError if required jobs are missing or failed.
    """
    jobs_summary: dict[str, dict[str, Any]] = {}
    for job in jobs_data.get("jobs", []):
        name = job.get("name")
        jobs_summary[name] = {
            "id": job.get("id"),
            "status": job.get("status"),
            "conclusion": job.get("conclusion"),
            "started_at": job.get("started_at"),
            "completed_at": job.get("completed_at"),
        }

    # Check required jobs
    found_job_names = set(jobs_summary.keys())
    missing_required = REQUIRED_JOBS - found_job_names
    if missing_required:
        raise EvidenceValidationError(
            f"missing required jobs: {sorted(missing_required)}"
        )

    # PR Quality Gate must be successful
    gate_conclusion = jobs_summary.get("PR Quality Gate", {}).get("conclusion")
    if gate_conclusion != "success":
        raise EvidenceValidationError(
            f"PR Quality Gate conclusion is '{gate_conclusion}', expected 'success'"
        )

    # Required jobs must all be successful
    for job_name in REQUIRED_JOBS:
        conclusion = jobs_summary.get(job_name, {}).get("conclusion")
        if conclusion != "success":
            raise EvidenceValidationError(
                f"required job '{job_name}' conclusion is '{conclusion}', "
                f"expected 'success'"
            )

    # Optional lanes must be either success or skipped
    for job_name in OPTIONAL_LANE_JOBS:
        if job_name in jobs_summary:
            conclusion = jobs_summary[job_name].get("conclusion")
            if conclusion not in ("success", "skipped"):
                raise EvidenceValidationError(
                    f"optional lane '{job_name}' conclusion is '{conclusion}', "
                    f"expected 'success' or 'skipped'"
                )

    return jobs_summary


def fetch_run_evidence(
    repo: str,
    run_id: int,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Fetch run and jobs data from GitHub API.

    Returns ``(run_data, jobs_data, jobs_summary)`` where jobs_summary is
    the validated job-level evidence.
    """
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

    run_data["_duration_seconds"] = duration_seconds
    return run_data, jobs_data, validate_jobs(jobs_data)


def validate_negative_run(
    repo: str,
    run_id: str | int,
    expected_failed_job: str | None = None,
    expected_head_sha: str | None = None,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    """Fetch and validate a negative proof run.

    Verifies workflow name, event type, completed status, failure conclusion,
    expected failed job, and expected head SHA if specified.
    """
    run_data = run_gh_json([f"repos/{repo}/actions/runs/{run_id}"], runner=runner)
    run_name = run_data.get("name", "")
    if run_name != DEFAULT_WORKFLOW_NAME:
        raise EvidenceValidationError(
            f"negative proof run {run_id} workflow is '{run_name}', expected '{DEFAULT_WORKFLOW_NAME}'"
        )
    event = run_data.get("event", "")
    if event != "pull_request":
        raise EvidenceValidationError(
            f"negative proof run {run_id} event is '{event}', expected 'pull_request'"
        )
    status = run_data.get("status", "")
    if status != "completed":
        raise EvidenceValidationError(
            f"negative proof run {run_id} status is '{status}', expected 'completed'"
        )
    conclusion = run_data.get("conclusion")
    if conclusion != "failure":
        raise EvidenceValidationError(
            f"negative proof run {run_id} conclusion is '{conclusion}', expected 'failure'"
        )

    if expected_head_sha:
        actual_sha = run_data.get("head_sha", "")
        if not actual_sha.startswith(expected_head_sha):
            raise EvidenceValidationError(
                f"negative proof run {run_id} head SHA is '{actual_sha}', expected '{expected_head_sha}'"
            )

    if expected_failed_job:
        jobs_data = run_gh_json([f"repos/{repo}/actions/runs/{run_id}/jobs"], runner=runner)
        job_map = {j.get("name"): j for j in jobs_data.get("jobs", [])}
        job_info = job_map.get(expected_failed_job)
        if not job_info:
            raise EvidenceValidationError(
                f"negative proof run {run_id} missing expected job '{expected_failed_job}'"
            )
        job_conclusion = job_info.get("conclusion")
        if job_conclusion != "failure":
            raise EvidenceValidationError(
                f"negative proof run {run_id} job '{expected_failed_job}' conclusion is '{job_conclusion}', expected 'failure'"
            )

    return run_data


def build_ci_evidence(
    repo: str = DEFAULT_REPO,
    pr_number: int = DEFAULT_PR,
    run_id: int | None = None,
    direct_import_negative_run: str | None = "33245608901",
    importfrom_bypass_negative_run: str | None = "33247122809",
    high_severity_negative_run: str | None = "33247203439",
    advisory_id: str | None = "GHSA-cpwx-vrp4-4pq7",
    rename_bypass_negative_run: str | None = None,
    validate_negative_proofs: bool = True,
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    """Build validated CI quality evidence.

    Fetches the PR and run, validates their relationship, and emits
    structured evidence with clear ``observed``/``contract``/
    ``historical_negative_proofs`` separation.
    """
    # Always fetch PR data for attribution validation
    pr_data = run_gh_json([f"repos/{repo}/pulls/{pr_number}"], runner=runner)

    if run_id is None:
        # Find latest PR Quality run for PR head
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
            raise EvidenceValidationError(
                f"no '{DEFAULT_WORKFLOW_NAME}' run found for commit {head_sha}"
            )
        run_id = pr_runs[0]["id"]

    run_data, jobs_data, jobs_summary = fetch_run_evidence(repo, run_id, runner=runner)

    # Strict validation of run/PR relationship
    validate_run_against_pr(run_data, pr_data, pr_number, run_id)

    # Build validated historical negative proofs (omit any null/absent proofs)
    historical_negative_proofs: dict[str, Any] = {}

    if direct_import_negative_run:
        if validate_negative_proofs:
            validate_negative_run(
                repo,
                direct_import_negative_run,
                expected_failed_job="Core Quality",
                expected_head_sha="c1c9aa18",
                runner=runner,
            )
        historical_negative_proofs["direct_import_bypass"] = {
            "run_id": str(direct_import_negative_run),
            "description": (
                "Direct 'import infrastructure' bypass — architecture "
                "checker correctly rejects"
            ),
        }

    if importfrom_bypass_negative_run:
        if validate_negative_proofs:
            validate_negative_run(
                repo,
                importfrom_bypass_negative_run,
                expected_failed_job="Core Quality",
                expected_head_sha="7afe3882",
                runner=runner,
            )
        historical_negative_proofs["importfrom_bypass"] = {
            "run_id": str(importfrom_bypass_negative_run),
            "description": (
                "'from ngabo import infrastructure' bypass — architecture "
                "checker correctly rejects via resolve_name"
            ),
        }

    if high_severity_negative_run:
        if validate_negative_proofs:
            validate_negative_run(
                repo,
                high_severity_negative_run,
                expected_failed_job="Dependency Security",
                expected_head_sha="7afe3882",
                runner=runner,
            )
        proof_obj: dict[str, Any] = {
            "run_id": str(high_severity_negative_run),
            "description": (
                "High-severity vulnerable dependency — uv audit + "
                "dependency review correctly reject"
            ),
        }
        if advisory_id:
            proof_obj["advisory_id"] = advisory_id
        historical_negative_proofs["high_severity_dependency"] = proof_obj

    if rename_bypass_negative_run:
        if validate_negative_proofs:
            validate_negative_run(
                repo, rename_bypass_negative_run, expected_failed_job=None, runner=runner
            )
        historical_negative_proofs["rename_bypass"] = {
            "run_id": str(rename_bypass_negative_run),
            "description": (
                "Core-to-docs rename bypass — rename-aware collector "
                "correctly retains source path"
            ),
        }

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "generated_at": datetime.now(UTC).isoformat(),
        "issue": 88,
        "issue_title": (
            "Cloud Foundation 1A.4: Enforce monorepo PR quality gates in GitHub Actions"
        ),
        "observed": {
            "pr_number": pr_data.get("number"),
            "pr_head_sha": pr_data.get("head", {}).get("sha"),
            "run_id": run_data.get("id"),
            "run_url": run_data.get("html_url"),
            "run_head_sha": run_data.get("head_sha"),
            "run_event": run_data.get("event"),
            "run_status": run_data.get("status"),
            "run_conclusion": run_data.get("conclusion"),
            "run_name": run_data.get("name"),
            "run_path": run_data.get("path", ""),
            "duration_seconds": run_data.get("_duration_seconds"),
            "jobs": jobs_summary,
        },
        "contract": {
            "classification": {
                "docs_only": "VERIFIED_BY_TESTS",
                "core_only": "VERIFIED_BY_TESTS",
                "web_only": "VERIFIED_BY_TESTS",
                "pnpm_lock_only": "VERIFIED_BY_TESTS",
                "unknown_non_doc_fail_closed": "VERIFIED_BY_TESTS",
                "conservative_fallback": "VERIFIED_BY_TESTS",
                "rename_aware_collector": "VERIFIED_BY_TESTS",
            },
            "architecture": {
                "checker_present": True,
                "checker_script": "scripts/ci/check_architecture.py",
                "effective_target_resolution": (
                    "ast.ImportFrom + importlib.util.resolve_name"
                ),
            },
            "security": {
                "python_audit": "uv --preview audit --frozen",
                "pnpm_audit": "pnpm audit --audit-level=high",
                "native_dependency_review_status": "ACTIVE",
                "native_dependency_review_action": (
                    "actions/dependency-review-action"
                    "@a1d282b36b6f3519aa1f3fc636f609c47dddb294"
                ),
                "vulnerability_alerts_enabled": True,
                "vulnerability_alerts_note": (
                    "Repository vulnerability alerts were enabled during #88 "
                    "as a one-time security-setting mutation to activate the "
                    "dependency graph comparison API. This is a free feature "
                    "on public GitHub repositories."
                ),
            },
            "ci_control_plane": {
                "rename_protection": "previous_filename extracted",
                "protected_path_evaluation": "VERIFIED_BY_TESTS",
            },
            "evidence_attribution": {
                "pr_run_binding": "VALIDATED",
                "workflow_name_check": "VALIDATED",
                "event_check": "VALIDATED",
                "head_sha_check": "VALIDATED",
                "conclusion_check": "VALIDATED",
                "pr_association_check": "VALIDATED",
                "job_level_check": "VALIDATED",
            },
            "merge_method": "merge",
            "privacy_review_status": "EXTERNAL_REVIEW_REQUIRED",
            "ruleset": {
                "name": "Ngabo Required PR Quality",
                "target_branches": ["refs/heads/develop", "refs/heads/main"],
                "required_checks": [
                    {
                        "context": "PR Quality Gate",
                        "integration_id": DEFAULT_INTEGRATION_ID,
                    },
                    {
                        "context": "CI Control Plane",
                        "integration_id": DEFAULT_INTEGRATION_ID,
                    },
                ],
                "allowed_merge_methods": ["merge"],
                "github_actions_integration_id": DEFAULT_INTEGRATION_ID,
                "activation_status": "PENDING_POST_MERGE",
            },
        },
        "historical_negative_proofs": historical_negative_proofs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate CI Quality Gates Evidence — "
            "Cloud Foundation 1A.4: Enforce monorepo PR quality gates in GitHub Actions"
        )
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("NGABO_GITHUB_REPOSITORY", DEFAULT_REPO),
    )
    parser.add_argument("--pr", type=int, default=DEFAULT_PR)
    parser.add_argument("--run-id", type=int, default=None)
    parser.add_argument("--direct-import-negative-run", default="33245608901")
    parser.add_argument("--importfrom-negative-run", default="33247122809")
    parser.add_argument("--security-negative-run", default="33247203439")
    parser.add_argument("--advisory-id", default="GHSA-cpwx-vrp4-4pq7")
    parser.add_argument("--rename-negative-run", default=None)
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
            rename_bypass_negative_run=args.rename_negative_run,
        )
    except EvidenceValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
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
