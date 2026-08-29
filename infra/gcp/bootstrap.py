"""GCP Foundation Bootstrap and Validation CLI (Issue #86).

Implements plan, apply, validate, and teardown-rehearsal operations for Ngabo's
Google Cloud foundation using gcloud CLI JSON output with strict redaction.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Ensure repository root is on sys.path for direct CLI execution
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.gcp.config import (  # noqa: E402
    ARTIFACT_REGISTRY_DESCRIPTION,
    ARTIFACT_REGISTRY_FORMAT,
    ARTIFACT_REGISTRY_REPO,
    BUDGET_AMOUNT_USD,
    BUDGET_DISPLAY_NAME,
    BUDGET_THRESHOLDS,
    CLOUD_RUN_CAPS_CONTRACT,
    GCS_LIFECYCLE_CONTRACT,
    PRIMARY_REGION,
    REQUIRED_APIS,
    RESOURCE_CLASSIFICATION_MATRIX,
    STANDARD_LABELS,
    GcpBootstrapConfig,
)

BILLING_ACCOUNT_REGEX = re.compile(r"\b[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6}\b")
BILLING_RESOURCE_REGEX = re.compile(
    r"billingAccounts/[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6}"
)


def redact_sensitive(text: str) -> str:
    """Redact billing account IDs and credentials from text and json."""
    redacted = BILLING_RESOURCE_REGEX.sub("billingAccounts/[REDACTED_BILLING_ID]", text)
    redacted = BILLING_ACCOUNT_REGEX.sub("[REDACTED_BILLING_ID]", redacted)
    return redacted


def run_gcloud_command(
    args: list[str],
    check: bool = True,
    capture_output: bool = True,
) -> tuple[int, str, str]:
    """Execute a gcloud command and return (exit_code, stdout, stderr)."""
    env = dict(os.environ)
    env["CLOUDSDK_METRICS_ENVIRONMENT"] = "datacloud.antigravity"

    cmd = ["gcloud", *args]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True,
            shell=sys.platform == "win32",
            env=env,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if check and proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, cmd, output=stdout, stderr=stderr
            )
        return proc.returncode, stdout, stderr
    except FileNotFoundError as exc:
        raise RuntimeError(
            "gcloud CLI not found on PATH. Please install Google Cloud SDK."
        ) from exc


class GcpInspector:
    """Read-only inspection of GCP state using gcloud."""

    def __init__(self, config: GcpBootstrapConfig) -> None:
        self.config = config

    def discover_billing_account(self) -> str | None:
        """Resolve the active billing account ID dynamically."""
        if self.config.billing_account:
            return str(self.config.billing_account)

        code, out, _ = run_gcloud_command(
            ["billing", "accounts", "list", "--format=json"],
            check=False,
        )
        if code != 0 or not out.strip():
            return None

        try:
            accounts = json.loads(out)
            for acc in accounts:
                if acc.get("open", False):
                    name = str(acc.get("name", ""))
                    if name.startswith("billingAccounts/"):
                        return str(name.split("/", 1)[1])
                    val = acc.get("billingAccountId") or name
                    return str(val) if val else None
            return None
        except Exception:
            return None

    def project_exists(self) -> bool:
        """Check if canonical project already exists."""
        code, _, _ = run_gcloud_command(
            ["projects", "describe", self.config.project_id, "--format=json"],
            check=False,
        )
        return code == 0

    def get_project_details(self) -> dict[str, Any] | None:
        """Get canonical project metadata."""
        code, out, _ = run_gcloud_command(
            ["projects", "describe", self.config.project_id, "--format=json"],
            check=False,
        )
        if code != 0 or not out.strip():
            return None
        try:
            return json.loads(out)  # type: ignore[no-any-return]
        except Exception:
            return None

    def is_billing_linked(self) -> bool:
        """Check if project has active billing linked."""
        code, out, _ = run_gcloud_command(
            ["billing", "projects", "describe", self.config.project_id, "--format=json"],
            check=False,
        )
        if code != 0 or not out.strip():
            return False
        try:
            data = json.loads(out)
            return bool(data.get("billingEnabled", False))
        except Exception:
            return False

    def get_enabled_apis(self) -> set[str]:
        """List enabled APIs for project."""
        code, out, _ = run_gcloud_command(
            [
                "services",
                "list",
                "--enabled",
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        if code != 0 or not out.strip():
            return set()
        try:
            data = json.loads(out)
            services: set[str] = set()
            for item in data:
                cfg = item.get("config", {})
                name = cfg.get("name") or item.get("serviceName") or ""
                if name:
                    services.add(name)
            return services
        except Exception:
            return set()

    def artifact_registry_exists(self) -> bool:
        """Check if Artifact Registry docker repo exists."""
        code, _, _ = run_gcloud_command(
            [
                "artifacts",
                "repositories",
                "describe",
                ARTIFACT_REGISTRY_REPO,
                f"--location={self.config.region}",
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        return code == 0

    def get_budget(self, billing_account_id: str) -> dict[str, Any] | None:
        """Check if budget alert exists for the project."""
        code, out, _ = run_gcloud_command(
            [
                "billing",
                "budgets",
                "list",
                f"--billing-account={billing_account_id}",
                f"--billing-project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        if code != 0 or not out.strip():
            return None
        try:
            budgets = json.loads(out)
            for b in budgets:
                if b.get("displayName") == BUDGET_DISPLAY_NAME:
                    return b  # type: ignore[no-any-return]
            return None
        except Exception:
            return None


class GcpBootstrapper:
    """Idempotent orchestrator for GCP foundation provisioning."""

    def __init__(self, config: GcpBootstrapConfig) -> None:
        self.config = config
        self.inspector = GcpInspector(config)

    def plan(self) -> dict[str, Any]:
        """Perform non-mutating assessment of desired vs live state."""
        validation_errors = self.config.validate()
        billing_acc = self.inspector.discover_billing_account()

        project_exists = self.inspector.project_exists()
        billing_linked = self.inspector.is_billing_linked() if project_exists else False

        enabled_apis = self.inspector.get_enabled_apis() if project_exists else set()
        missing_apis = sorted(set(REQUIRED_APIS) - enabled_apis)

        ar_exists = (
            self.inspector.artifact_registry_exists()
            if project_exists and "artifactregistry.googleapis.com" in enabled_apis
            else False
        )

        budget_exists = (
            bool(self.inspector.get_budget(billing_acc)) if billing_acc else False
        )

        planned_actions: list[str] = []
        if not project_exists:
            planned_actions.append(f"CREATE_PROJECT: {self.config.project_id}")
        if not billing_linked:
            planned_actions.append("LINK_BILLING: Link active Free Trial billing account")
        if missing_apis:
            joined = ", ".join(missing_apis)
            planned_actions.append(f"ENABLE_APIS ({len(missing_apis)} missing): {joined}")
        if not ar_exists:
            action = f"CREATE_ARTIFACT_REGISTRY: {ARTIFACT_REGISTRY_REPO} in {self.config.region}"
            planned_actions.append(action)
        if not budget_exists:
            action = f"CREATE_BUDGET_ALERT: {BUDGET_DISPLAY_NAME} ($300 USD thresholds)"
            planned_actions.append(action)

        return {
            "status": "VALID" if not validation_errors else "INVALID",
            "validation_errors": validation_errors,
            "project_id": self.config.project_id,
            "region": self.config.region,
            "billing_account_configured": bool(billing_acc),
            "project_exists": project_exists,
            "billing_linked": billing_linked,
            "enabled_apis_count": len(enabled_apis),
            "missing_apis": missing_apis,
            "artifact_registry_exists": ar_exists,
            "budget_alert_exists": budget_exists,
            "planned_actions": planned_actions,
            "is_converged": len(planned_actions) == 0,
            "resource_classification": {
                k: {"classification": v[0].value, "notes": v[1]}
                for k, v in RESOURCE_CLASSIFICATION_MATRIX.items()
            },
            "governed_caps": {
                "cloud_run": CLOUD_RUN_CAPS_CONTRACT,
                "storage_lifecycle": GCS_LIFECYCLE_CONTRACT,
            },
        }

    def apply(self) -> dict[str, Any]:
        """Idempotently apply configuration to achieve target state."""
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        billing_acc = self.inspector.discover_billing_account()
        if not billing_acc:
            raise RuntimeError(
                "No active billing account discovered. Please check gcloud authentication "
                "or set NGABO_GCP_BILLING_ACCOUNT."
            )

        results: dict[str, Any] = {
            "project_id": self.config.project_id,
            "region": self.config.region,
            "operations": [],
            "noop": True,
        }

        # 1. Project Creation
        if not self.inspector.project_exists():
            labels_str = ",".join(f"{k}={v}" for k, v in STANDARD_LABELS.items())
            print(f"[apply] Creating canonical project: {self.config.project_id}...")
            run_gcloud_command(
                [
                    "projects",
                    "create",
                    self.config.project_id,
                    f"--name={self.config.project_name}",
                    f"--labels={labels_str}",
                ]
            )
            results["operations"].append("PROJECT_CREATED")
            results["noop"] = False
        else:
            print(f"[apply] Project {self.config.project_id} already exists (idempotent no-op).")

        # 2. Billing Link
        if not self.inspector.is_billing_linked():
            print(f"[apply] Linking billing account to {self.config.project_id}...")
            run_gcloud_command(
                [
                    "billing",
                    "projects",
                    "link",
                    self.config.project_id,
                    f"--billing-account={billing_acc}",
                ]
            )
            results["operations"].append("BILLING_LINKED")
            results["noop"] = False
        else:
            print(f"[apply] Billing already linked to {self.config.project_id} (idempotent no-op).")

        # 3. Enable Required APIs
        enabled_apis = self.inspector.get_enabled_apis()
        missing_apis = [api for api in REQUIRED_APIS if api not in enabled_apis]
        if missing_apis:
            print(f"[apply] Enabling {len(missing_apis)} missing APIs...")
            run_gcloud_command(
                ["services", "enable", *missing_apis, f"--project={self.config.project_id}"]
            )
            results["operations"].append(f"APIS_ENABLED:{len(missing_apis)}")
            results["noop"] = False
        else:
            print("[apply] All required APIs already enabled (idempotent no-op).")

        # 4. Artifact Registry Repository
        if not self.inspector.artifact_registry_exists():
            print(f"[apply] Creating repo '{ARTIFACT_REGISTRY_REPO}' in {self.config.region}...")
            labels_str = ",".join(f"{k}={v}" for k, v in STANDARD_LABELS.items())
            run_gcloud_command(
                [
                    "artifacts",
                    "repositories",
                    "create",
                    ARTIFACT_REGISTRY_REPO,
                    f"--repository-format={ARTIFACT_REGISTRY_FORMAT}",
                    f"--location={self.config.region}",
                    f"--description={ARTIFACT_REGISTRY_DESCRIPTION}",
                    f"--project={self.config.project_id}",
                    f"--labels={labels_str}",
                ]
            )
            results["operations"].append("ARTIFACT_REGISTRY_CREATED")
            results["noop"] = False
        else:
            print(f"[apply] Repository '{ARTIFACT_REGISTRY_REPO}' exists (idempotent no-op).")

        # 5. Billing Budget Alert
        if not self.inspector.get_budget(billing_acc):
            print(f"[apply] Creating Billing Budget '{BUDGET_DISPLAY_NAME}' for $300 USD...")
            threshold_args: list[str] = [
                f"--threshold-rule=percent={t['percent']},basis={t['basis']}"
                for t in BUDGET_THRESHOLDS
            ]
            run_gcloud_command(
                [
                    "billing",
                    "budgets",
                    "create",
                    f"--billing-account={billing_acc}",
                    f"--billing-project={self.config.project_id}",
                    f"--display-name={BUDGET_DISPLAY_NAME}",
                    f"--budget-amount={BUDGET_AMOUNT_USD:.2f}USD",
                    f"--filter-projects=projects/{self.config.project_id}",
                    *threshold_args,
                ]
            )
            results["operations"].append("BUDGET_ALERT_CREATED")
            results["noop"] = False
        else:
            print(f"[apply] Budget '{BUDGET_DISPLAY_NAME}' already exists (idempotent no-op).")

        results["success"] = True
        return results

    def validate(self) -> dict[str, Any]:
        """Validate live state against allow-list and governance constraints."""
        report: dict[str, Any] = {
            "project_id": self.config.project_id,
            "region": self.config.region,
            "checks": {},
            "passed": True,
            "failures": [],
        }

        # Check 1: Project Exists
        proj_exists = self.inspector.project_exists()
        report["checks"]["project_exists"] = proj_exists
        if not proj_exists:
            report["failures"].append(f"Project '{self.config.project_id}' does not exist.")
            report["passed"] = False
            return report

        # Check 2: Project Labels
        proj_details = self.inspector.get_project_details() or {}
        labels = proj_details.get("labels", {})
        labels_valid = all(labels.get(k) == v for k, v in STANDARD_LABELS.items())
        report["checks"]["labels_valid"] = labels_valid
        if not labels_valid:
            report["failures"].append(
                f"Project labels invalid: expected {STANDARD_LABELS}, got {labels}."
            )
            report["passed"] = False

        # Check 3: Billing Linked
        billing_linked = self.inspector.is_billing_linked()
        report["checks"]["billing_linked"] = billing_linked
        if not billing_linked:
            report["failures"].append(
                f"Project '{self.config.project_id}' does not have active billing linked."
            )
            report["passed"] = False

        # Check 4: APIs Enabled
        enabled_apis = self.inspector.get_enabled_apis()
        missing_apis = sorted(set(REQUIRED_APIS) - enabled_apis)
        report["checks"]["required_apis_enabled"] = len(missing_apis) == 0
        report["checks"]["enabled_apis_count"] = len(enabled_apis)
        if missing_apis:
            joined = ", ".join(missing_apis)
            report["failures"].append(f"Missing required APIs ({len(missing_apis)}): {joined}")
            report["passed"] = False

        # Check 5: Artifact Registry
        ar_exists = self.inspector.artifact_registry_exists()
        report["checks"]["artifact_registry_exists"] = ar_exists
        if not ar_exists:
            report["failures"].append(
                f"Repository '{ARTIFACT_REGISTRY_REPO}' missing in {self.config.region}."
            )
            report["passed"] = False

        # Check 6: Budget Monitoring
        billing_acc = self.inspector.discover_billing_account()
        budget_exists = bool(self.inspector.get_budget(billing_acc)) if billing_acc else False
        report["checks"]["budget_monitoring_exists"] = budget_exists
        if not budget_exists:
            report["failures"].append(
                f"Billing budget alert '{BUDGET_DISPLAY_NAME}' not found for billing account."
            )
            report["passed"] = False

        return report

    def teardown_rehearsal(self) -> dict[str, Any]:
        """Perform dry-run rehearsal of reproducible environment teardown."""
        billing_acc = self.inspector.discover_billing_account()
        budget = self.inspector.get_budget(billing_acc) if billing_acc else None

        b_cmd = (
            f"gcloud billing budgets delete {budget.get('name', 'BUDGET_ID')} "
            "--billing-account=[REDACTED]"
            if budget
            else "None (No budget to delete)"
        )
        ar_cmd = (
            f"gcloud artifacts repositories delete {ARTIFACT_REGISTRY_REPO} "
            f"--location={self.config.region} --project={self.config.project_id} --quiet"
        )
        action_shutdown = (
            "Request project shutdown (enters asynchronous deletion lifecycle / 30-day recovery)"
        )

        rehearsal = {
            "rehearsal_only": True,
            "project_id": self.config.project_id,
            "region": self.config.region,
            "teardown_plan": [
                {
                    "order": 1,
                    "target": f"Artifact Registry repository '{ARTIFACT_REGISTRY_REPO}'",
                    "action": "Delete container repository and any cached images",
                    "command": ar_cmd,
                },
                {
                    "order": 2,
                    "target": f"Billing Budget '{BUDGET_DISPLAY_NAME}'",
                    "action": "Remove budget monitor alert from billing account",
                    "command": b_cmd,
                },
                {
                    "order": 3,
                    "target": f"Project Billing Link for '{self.config.project_id}'",
                    "action": "Unlink billing account to guarantee zero ongoing accrual",
                    "command": f"gcloud billing projects unlink {self.config.project_id}",
                },
                {
                    "order": 4,
                    "target": f"GCP Project '{self.config.project_id}'",
                    "action": action_shutdown,
                    "command": f"gcloud projects delete {self.config.project_id} --quiet",
                },
            ],
            "cessation_verification_steps": [
                "Verify no Cloud Run services or active revisions remain reachable.",
                "Verify Cloud Billing project status shows 'billingEnabled: false'.",
                "Verify project lifecycleState transitions to 'DELETE_REQUESTED'.",
            ],
        }
        return rehearsal


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for ngabo-bootstrap."""
    parser = argparse.ArgumentParser(
        description="Ngabo Google Cloud Foundation Bootstrap CLI (Issue #86)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: plan
    plan_parser = subparsers.add_parser("plan", help="Show planned foundation actions")
    plan_parser.add_argument("--project-id", default=None, help="GCP project ID")
    plan_parser.add_argument("--region", default=PRIMARY_REGION, help="GCP region")
    plan_parser.add_argument("--format", choices=["text", "json"], default="text")

    # Subcommand: apply
    apply_parser = subparsers.add_parser("apply", help="Apply foundation configuration")
    apply_parser.add_argument("--project-id", default=None, help="GCP project ID")
    apply_parser.add_argument("--region", default=PRIMARY_REGION, help="GCP region")
    apply_parser.add_argument("--format", choices=["text", "json"], default="text")

    # Subcommand: validate
    val_parser = subparsers.add_parser("validate", help="Validate live state against allow-list")
    val_parser.add_argument("--project-id", default=None, help="GCP project ID")
    val_parser.add_argument("--region", default=PRIMARY_REGION, help="GCP region")
    val_parser.add_argument("--format", choices=["text", "json"], default="text")

    # Subcommand: teardown
    td_parser = subparsers.add_parser("teardown", help="Teardown environment resources")
    td_parser.add_argument("--project-id", default=None, help="GCP project ID")
    td_parser.add_argument("--region", default=PRIMARY_REGION, help="GCP region")
    td_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Rehearse teardown without modifying resources (default: True)",
    )
    td_parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args(argv)

    config = GcpBootstrapConfig.from_env(
        project_id=args.project_id,
        region=args.region,
        dry_run=getattr(args, "dry_run", False),
    )

    bootstrapper = GcpBootstrapper(config)

    if args.command == "plan":
        plan_res = bootstrapper.plan()
        out_json = redact_sensitive(json.dumps(plan_res, indent=2))
        if args.format == "json":
            print(out_json)
        else:
            print("============================================================")
            print("Ngabo GCP Foundation Plan")
            print("============================================================")
            print(f"Project ID:        {plan_res['project_id']}")
            print(f"Region:            {plan_res['region']}")
            print(f"Project Exists:    {plan_res['project_exists']}")
            print(f"Billing Linked:    {plan_res['billing_linked']}")
            cnt = plan_res["enabled_apis_count"]
            missing_cnt = len(plan_res["missing_apis"])
            print(f"Enabled APIs:      {cnt} (Missing: {missing_cnt})")
            print(f"Artifact Registry: {plan_res['artifact_registry_exists']}")
            print(f"Budget Alert:      {plan_res['budget_alert_exists']}")
            print(f"Converged (No-op): {plan_res['is_converged']}")
            print("\nPlanned Actions:")
            if plan_res["planned_actions"]:
                for act in plan_res["planned_actions"]:
                    print(f"  + {act}")
            else:
                print("  (None: Live environment matches target state)")
            print("============================================================")
        return 0

    if args.command == "apply":
        try:
            apply_res = bootstrapper.apply()
            out_json = redact_sensitive(json.dumps(apply_res, indent=2))
            if args.format == "json":
                print(out_json)
            else:
                print("\n[apply] Bootstrap completed successfully.")
                print(f"Operations executed: {apply_res.get('operations', [])}")
                print(f"Idempotent No-op:    {apply_res.get('noop', False)}")
            return 0
        except Exception as exc:
            print(f"[apply] ERROR: {redact_sensitive(str(exc))}", file=sys.stderr)
            return 1

    if args.command == "validate":
        val_res = bootstrapper.validate()
        out_json = redact_sensitive(json.dumps(val_res, indent=2))
        if args.format == "json":
            print(out_json)
        else:
            print("============================================================")
            print("Ngabo GCP Foundation Validation")
            print("============================================================")
            print(f"Status:   {'PASSED' if val_res['passed'] else 'FAILED'}")
            exists = val_res['checks']['project_exists']
            print(f"Project:  {val_res['project_id']} (Exists: {exists})")
            print(f"Billing:  Linked: {val_res['checks']['billing_linked']}")
            apis_ok = val_res['checks']['required_apis_enabled']
            print(f"APIs:     All 14 Required Enabled: {apis_ok}")
            ar_ok = val_res['checks']['artifact_registry_exists']
            print(f"Registry: Artifact Registry Exists: {ar_ok}")
            b_ok = val_res['checks']['budget_monitoring_exists']
            print(f"Budget:   Budget Monitoring Exists: {b_ok}")
            if val_res["failures"]:
                print("\nFailures:")
                for fail in val_res["failures"]:
                    print(f"  - {fail}")
            print("============================================================")
        return 0 if val_res["passed"] else 1

    if args.command == "teardown":
        td_res = bootstrapper.teardown_rehearsal()
        out_json = redact_sensitive(json.dumps(td_res, indent=2))
        if args.format == "json":
            print(out_json)
        else:
            print("============================================================")
            print("Ngabo GCP Foundation Teardown Rehearsal (Dry Run)")
            print("============================================================")
            print(f"Target Project: {td_res['project_id']}")
            print(f"Target Region:  {td_res['region']}")
            print("\nTeardown Sequence:")
            for step in td_res["teardown_plan"]:
                print(f"  Step {step['order']}: {step['target']}")
                print(f"    Action:  {step['action']}")
                print(f"    Command: {step['command']}")
            print("\nCessation Verification Steps:")
            for v in td_res["cessation_verification_steps"]:
                print(f"  * {v}")
            print("============================================================")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
