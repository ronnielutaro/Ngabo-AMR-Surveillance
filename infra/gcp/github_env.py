"""Reproducible GitHub Environment and Deployment Branch Policy Automation (Issue #87).

Manages the 'dev' GitHub Environment and restricts its deployment branch policy
strictly to 'develop' using the GitHub REST API via the 'gh api' CLI.
Fails closed on any unexpected network or API error.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.gcp.identity_config import (  # noqa: E402
    GITHUB_ALLOWED_ENV,
    GITHUB_ALLOWED_REF,
    GITHUB_OWNER,
    GITHUB_REPO,
)

TARGET_BRANCH = GITHUB_ALLOWED_REF.removeprefix("refs/heads/")  # "develop"


def run_gh_command(args: list[str], *, capture_output: bool = True) -> subprocess.CompletedProcess[str]:
    """Execute a gh CLI command with failure handling."""
    cmd = ["gh"] + args
    result = subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        check=False,
    )
    return result


class GitHubEnvInspector:
    """Read-only inspector for GitHub environments and branch policies."""

    def __init__(self, owner: str = GITHUB_OWNER, repo: str = GITHUB_REPO) -> None:
        self.owner = owner
        self.repo = repo

    def get_environment(self, env_name: str = GITHUB_ALLOWED_ENV) -> dict[str, Any] | None:
        """Fetch environment metadata. Returns None if 404, raises on error."""
        endpoint = f"repos/{self.owner}/{self.repo}/environments/{env_name}"
        proc = run_gh_command(["api", endpoint])
        if proc.returncode != 0:
            if "404" in proc.stderr or "Not Found" in proc.stderr or "404" in proc.stdout:
                return None
            raise RuntimeError(f"INSPECTION_FAILED: Failed to fetch GitHub environment '{env_name}': {proc.stderr.strip()}")
        try:
            return json.loads(proc.stdout)  # type: ignore[no-any-return]
        except json.JSONDecodeError as err:
            raise RuntimeError(f"INSPECTION_FAILED: Unparsable JSON from GitHub API for environment '{env_name}': {err}") from err

    def get_branch_policies(self, env_name: str = GITHUB_ALLOWED_ENV) -> list[str]:
        """Fetch custom deployment branch policies for an environment."""
        endpoint = f"repos/{self.owner}/{self.repo}/environments/{env_name}/deployment-branch-policies"
        proc = run_gh_command(["api", endpoint])
        if proc.returncode != 0:
            if "404" in proc.stderr or "Not Found" in proc.stderr:
                return []
            raise RuntimeError(f"INSPECTION_FAILED: Failed to fetch deployment branch policies for '{env_name}': {proc.stderr.strip()}")
        try:
            data = json.loads(proc.stdout)
            policies = data.get("branch_policies", [])
            return [p.get("name", "") for p in policies if p.get("name")]
        except json.JSONDecodeError as err:
            raise RuntimeError(f"INSPECTION_FAILED: Unparsable JSON from GitHub API for branch policies: {err}") from err


class GitHubEnvManager:
    """Manages GitHub environment configuration and branch policies idempotently."""

    def __init__(self, inspector: GitHubEnvInspector | None = None) -> None:
        self.inspector = inspector or GitHubEnvInspector()
        self.target_env = GITHUB_ALLOWED_ENV
        self.target_branch = TARGET_BRANCH

    def plan(self) -> dict[str, Any]:
        """Evaluate planned changes for GitHub environment."""
        planned_actions: list[str] = []
        env = self.inspector.get_environment(self.target_env)
        if env is None:
            planned_actions.append(f"Create GitHub environment '{self.target_env}' with custom branch policy")
            planned_actions.append(f"Add deployment branch policy '{self.target_branch}' to '{self.target_env}'")
        else:
            branch_policy = env.get("deployment_branch_policy") or {}
            custom_enabled = branch_policy.get("custom_branch_policies", False)
            if not custom_enabled:
                planned_actions.append(f"Enable custom branch policies on '{self.target_env}'")
            policies = self.inspector.get_branch_policies(self.target_env)
            if self.target_branch not in policies:
                planned_actions.append(f"Add deployment branch policy '{self.target_branch}' to '{self.target_env}'")

        return {
            "environment": self.target_env,
            "target_branch": self.target_branch,
            "planned_actions": planned_actions,
            "is_converged": len(planned_actions) == 0,
        }

    def apply(self) -> dict[str, Any]:
        """Apply target GitHub environment and deployment branch policy."""
        operations: list[str] = []
        env = self.inspector.get_environment(self.target_env)

        if env is None:
            create_endpoint = f"repos/{self.inspector.owner}/{self.inspector.repo}/environments/{self.target_env}"
            payload = json.dumps({
                "deployment_branch_policy": {
                    "protected_branches": False,
                    "custom_branch_policies": True,
                }
            })
            proc = run_gh_command([
                "api",
                "--method", "PUT",
                "-H", "Accept: application/vnd.github+json",
                create_endpoint,
                "--input", "-",
            ])
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to create GitHub environment '{self.target_env}': {proc.stderr.strip()}")
            operations.append(f"Created GitHub environment '{self.target_env}'")
        else:
            branch_policy = env.get("deployment_branch_policy") or {}
            if not branch_policy.get("custom_branch_policies", False):
                update_endpoint = f"repos/{self.inspector.owner}/{self.inspector.repo}/environments/{self.target_env}"
                payload = json.dumps({
                    "deployment_branch_policy": {
                        "protected_branches": False,
                        "custom_branch_policies": True,
                    }
                })
                proc = run_gh_command([
                    "api",
                    "--method", "PUT",
                    "-H", "Accept: application/vnd.github+json",
                    update_endpoint,
                    "--input", "-",
                ])
                if proc.returncode != 0:
                    raise RuntimeError(f"Failed to update GitHub environment '{self.target_env}': {proc.stderr.strip()}")
                operations.append(f"Enabled custom branch policies on '{self.target_env}'")

        # Ensure target branch policy is present
        policies = self.inspector.get_branch_policies(self.target_env)
        if self.target_branch not in policies:
            policy_endpoint = f"repos/{self.inspector.owner}/{self.inspector.repo}/environments/{self.target_env}/deployment-branch-policies"
            proc = run_gh_command([
                "api",
                "--method", "POST",
                "-H", "Accept: application/vnd.github+json",
                policy_endpoint,
                "-f", f"name={self.target_branch}",
            ])
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to set branch policy '{self.target_branch}' on '{self.target_env}': {proc.stderr.strip()}")
            operations.append(f"Added branch policy '{self.target_branch}' to '{self.target_env}'")

        return {
            "success": True,
            "noop": len(operations) == 0,
            "operations": operations,
        }

    def validate(self) -> dict[str, Any]:
        """Validate live GitHub environment state against contract."""
        failures: list[str] = []
        checks: dict[str, bool] = {
            "environment_present": False,
            "custom_branch_policies_enabled": False,
            "exact_branch_policy_matches": False,
        }

        env = self.inspector.get_environment(self.target_env)
        if env is None:
            failures.append(f"GitHub environment '{self.target_env}' is absent.")
            return {"passed": False, "failures": failures, "checks": checks}

        checks["environment_present"] = True
        branch_policy = env.get("deployment_branch_policy") or {}
        custom_enabled = branch_policy.get("custom_branch_policies", False)
        checks["custom_branch_policies_enabled"] = custom_enabled
        if not custom_enabled:
            failures.append(f"GitHub environment '{self.target_env}' does not have custom_branch_policies enabled.")

        policies = self.inspector.get_branch_policies(self.target_env)
        if policies == [self.target_branch]:
            checks["exact_branch_policy_matches"] = True
        else:
            failures.append(
                f"GitHub environment '{self.target_env}' branch policies {policies} do not match expected [{self.target_branch}]."
            )

        return {
            "passed": len(failures) == 0,
            "failures": failures,
            "checks": checks,
            "observed": {
                "environment": self.target_env,
                "custom_branch_policies": custom_enabled,
                "branch_policies": policies,
            },
        }

    def teardown_rehearsal(self) -> dict[str, Any]:
        """Dry-run rehearsal for GitHub environment teardown."""
        return {
            "mode": "PLAN_ONLY",
            "destructive": False,
            "target_environment": self.target_env,
            "action": f"DELETE repos/{self.inspector.owner}/{self.inspector.repo}/environments/{self.target_env}",
        }
