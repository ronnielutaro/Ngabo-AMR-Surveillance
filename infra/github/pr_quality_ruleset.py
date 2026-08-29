"""Plan/apply/validate the repository ruleset for Issue #88.

The manager is intentionally local/maintainer-operated. Normal PR CI never receives
GitHub write authority.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from typing import Callable, Sequence

RULESET_NAME = "Ngabo Required PR Quality"
TARGET_BRANCHES = ("refs/heads/develop", "refs/heads/main")
REQUIRED_CHECKS = ("PR Quality Gate", "CI Control Plane")
API_VERSION = "2026-03-10"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[Sequence[str], str | None], CommandResult]


def run_gh(args: Sequence[str], input_text: str | None = None) -> CommandResult:
    command = [
        "gh", "api",
        "-H", "Accept: application/vnd.github+json",
        "-H", f"X-GitHub-Api-Version: {API_VERSION}",
        *args,
    ]
    proc = subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)


def required_check_entries(integration_id: int | None) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for context in REQUIRED_CHECKS:
        item: dict[str, object] = {"context": context}
        if integration_id is not None:
            item["integration_id"] = integration_id
        entries.append(item)
    return entries


def desired_ruleset(integration_id: int | None = None) -> dict[str, object]:
    return {
        "name": RULESET_NAME,
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {
            "ref_name": {
                "include": list(TARGET_BRANCHES),
                "exclude": [],
            }
        },
        "rules": [
            {
                "type": "pull_request",
                "parameters": {
                    "allowed_merge_methods": ["merge", "squash", "rebase"],
                    "dismiss_stale_reviews_on_push": False,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_approving_review_count": 0,
                    "required_review_thread_resolution": True,
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "do_not_enforce_on_create": False,
                    "required_status_checks": required_check_entries(integration_id),
                    "strict_required_status_checks_policy": True,
                },
            },
            {"type": "non_fast_forward"},
        ],
    }


def _rule_map(ruleset: dict[str, object]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for raw in ruleset.get("rules", []):
        if isinstance(raw, dict) and isinstance(raw.get("type"), str):
            result[str(raw["type"])] = raw
    return result


def canonical_contract(
    ruleset: dict[str, object],
    integration_id: int | None = None,
) -> dict[str, object]:
    rules = _rule_map(ruleset)
    pull = rules.get("pull_request", {}).get("parameters", {})
    checks = rules.get("required_status_checks", {}).get("parameters", {})
    return {
        "name": ruleset.get("name"),
        "target": ruleset.get("target"),
        "enforcement": ruleset.get("enforcement"),
        "bypass_actors": ruleset.get("bypass_actors", []),
        "conditions": ruleset.get("conditions"),
        "pull_request": pull,
        "required_status_checks": checks,
        "non_fast_forward": "non_fast_forward" in rules,
        "expected_check_entries": required_check_entries(integration_id),
    }


class RulesetManager:
    def __init__(
        self,
        repo: str,
        integration_id: int | None = None,
        runner: Runner = run_gh,
    ) -> None:
        self.repo = repo
        self.integration_id = integration_id
        self.runner = runner

    def _call_json(
        self,
        args: Sequence[str],
        input_text: str | None = None,
    ) -> object:
        result = self.runner(args, input_text)
        if result.returncode != 0:
            raise RuntimeError(
                "INSPECTION_FAILED: gh api command failed: "
                + (result.stderr.strip() or result.stdout.strip())
            )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("INSPECTION_FAILED: invalid GitHub JSON") from exc

    def inspect(self) -> dict[str, object] | None:
        collection = self._call_json([f"repos/{self.repo}/rulesets?per_page=100"])
        if not isinstance(collection, list):
            raise RuntimeError("INSPECTION_FAILED: ruleset collection is not a list")
        matches = [
            item for item in collection
            if isinstance(item, dict) and item.get("name") == RULESET_NAME
        ]
        if len(matches) > 1:
            raise RuntimeError("INSPECTION_FAILED: duplicate governed rulesets")
        if not matches:
            return None
        ruleset_id = matches[0].get("id")
        if not isinstance(ruleset_id, int):
            raise RuntimeError("INSPECTION_FAILED: governed ruleset has no numeric id")
        detail = self._call_json([f"repos/{self.repo}/rulesets/{ruleset_id}"])
        if not isinstance(detail, dict):
            raise RuntimeError("INSPECTION_FAILED: ruleset detail is not an object")
        return detail

    def validate_state(self, observed: dict[str, object] | None) -> bool:
        if observed is None:
            return False
        desired = desired_ruleset(self.integration_id)
        return canonical_contract(
            observed, self.integration_id
        ) == canonical_contract(desired, self.integration_id)

    def plan(self) -> dict[str, object]:
        observed = self.inspect()
        if observed is None:
            return {
                "converged": False,
                "action": "CREATE",
                "desired": desired_ruleset(self.integration_id),
            }
        if self.validate_state(observed):
            return {"converged": True, "action": "NONE"}
        return {
            "converged": False,
            "action": "UPDATE",
            "ruleset_id": observed.get("id"),
            "desired": desired_ruleset(self.integration_id),
        }

    def apply(self) -> dict[str, object]:
        plan = self.plan()
        action = plan["action"]
        payload = json.dumps(desired_ruleset(self.integration_id))
        if action == "CREATE":
            result = self.runner(
                ["--method", "POST", f"repos/{self.repo}/rulesets", "--input", "-"],
                payload,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "APPLY_FAILED: " + (result.stderr.strip() or result.stdout.strip())
                )
        elif action == "UPDATE":
            ruleset_id = plan["ruleset_id"]
            result = self.runner(
                [
                    "--method", "PUT",
                    f"repos/{self.repo}/rulesets/{ruleset_id}",
                    "--input", "-",
                ],
                payload,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "APPLY_FAILED: " + (result.stderr.strip() or result.stdout.strip())
                )

        observed = self.inspect()
        if not self.validate_state(observed):
            raise RuntimeError("APPLY_FAILED: post-apply ruleset validation failed")
        return {"success": True, "operations": [] if action == "NONE" else [action]}

    def validate(self) -> dict[str, object]:
        observed = self.inspect()
        valid = self.validate_state(observed)
        return {"success": valid, "observed": observed}

    def teardown_rehearsal(self) -> dict[str, object]:
        observed = self.inspect()
        return {
            "teardown_mode": "PLAN_ONLY",
            "destructive_actions_executed": False,
            "ruleset_present": observed is not None,
            "planned_action": (
                f"DELETE ruleset id={observed.get('id')}" if observed else "NONE"
            ),
        }


def _integration_id(value: str | None) -> int | None:
    return int(value) if value else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo",
        default=os.environ.get(
            "NGABO_GITHUB_REPOSITORY",
            "ronnielutaro/Ngabo-AMR-Surveillance",
        ),
    )
    parser.add_argument(
        "--integration-id",
        type=int,
        default=_integration_id(os.environ.get("NGABO_GITHUB_ACTIONS_INTEGRATION_ID")),
        help="Optional observed GitHub Actions integration ID for required checks.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    sub.add_parser("apply")
    sub.add_parser("validate")
    teardown = sub.add_parser("teardown")
    teardown.add_argument("--dry-run", action="store_true", required=True)
    args = parser.parse_args()

    manager = RulesetManager(args.repo, args.integration_id)
    if args.command == "plan":
        result = manager.plan()
    elif args.command == "apply":
        result = manager.apply()
    elif args.command == "validate":
        result = manager.validate()
        if not result["success"]:
            print(json.dumps(result, indent=2, sort_keys=True))
            return 1
    else:
        result = manager.teardown_rehearsal()

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
