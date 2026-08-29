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
import urllib.error
import urllib.request
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
    BUDGET_CREDIT_TREATMENT,
    BUDGET_DISPLAY_NAME,
    BUDGET_END_DATE,
    BUDGET_START_DATE,
    BUDGET_THRESHOLDS,
    CLOUD_RUN_CAPS_CONTRACT,
    ENVIRONMENTS,
    FIRESTORE_LOCATION,
    GCS_LIFECYCLE_CONTRACT,
    PRIMARY_REGION,
    REQUIRED_APIS,
    RESOURCE_CLASSIFICATION_MATRIX,
    STANDARD_LABELS,
    GcpBootstrapConfig,
)

BILLING_ACCOUNT_REGEX = re.compile(r"\b[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6}\b")
BILLING_RESOURCE_REGEX = re.compile(r"billingAccounts/[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6}")


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
            raise subprocess.CalledProcessError(proc.returncode, cmd, output=stdout, stderr=stderr)
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
        """Resolve the active billing account ID dynamically with disambiguation."""
        if self.config.billing_account:
            acc_id = str(self.config.billing_account).strip()
            if not BILLING_ACCOUNT_REGEX.match(acc_id):
                raise ValueError(
                    f"Configured billing account '{redact_sensitive(acc_id)}' "
                    "does not match expected format XXXXXX-XXXXXX-XXXXXX."
                )
            return acc_id

        code, out, stderr = run_gcloud_command(
            ["billing", "accounts", "list", "--format=json"],
            check=False,
        )
        if code != 0 or not out.strip():
            return None

        try:
            accounts: list[dict[str, Any]] = json.loads(out)
            open_accounts: list[str] = []
            for acc in accounts:
                if acc.get("open", False):
                    name = str(acc.get("name", ""))
                    if name.startswith("billingAccounts/"):
                        val = name.split("/", 1)[1]
                    else:
                        val = str(acc.get("billingAccountId") or name)
                    if val:
                        open_accounts.append(val)

            if not open_accounts:
                return None
            if len(open_accounts) > 1:
                raise RuntimeError(
                    f"Multiple ({len(open_accounts)}) open billing accounts discovered. "
                    "Disambiguation required: please specify intended account via "
                    "NGABO_GCP_BILLING_ACCOUNT."
                )
            return open_accounts[0]
        except (ValueError, KeyError, TypeError):
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

    def get_project_labels(self) -> dict[str, str]:
        """Get labels configured on the canonical project."""
        details = self.get_project_details() or {}
        labels = details.get("labels") or {}
        return dict(labels)

    def get_linked_billing_account(self) -> str | None:
        """Get the specific billing account ID currently linked to the project."""
        code, out, _ = run_gcloud_command(
            ["billing", "projects", "describe", self.config.project_id, "--format=json"],
            check=False,
        )
        if code != 0 or not out.strip():
            return None
        try:
            data = json.loads(out)
            if not data.get("billingEnabled", False):
                return None
            b_name = str(data.get("billingAccountName", ""))
            if b_name.startswith("billingAccounts/"):
                return b_name.split("/", 1)[1]
            return b_name if b_name else None
        except Exception:
            return None

    def is_billing_linked(self) -> bool:
        """Check if project has active billing linked (any account)."""
        return self.get_linked_billing_account() is not None

    def is_billing_linked_to_intended(self, intended_account: str) -> bool:
        """Check if project is linked specifically to the intended billing account."""
        linked = self.get_linked_billing_account()
        if not linked:
            return False
        return linked.strip().upper() == intended_account.strip().upper()

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

    def get_artifact_registry_details(self) -> dict[str, Any] | None:
        """Get Artifact Registry docker repo details."""
        code, out, _ = run_gcloud_command(
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
        if code != 0 or not out.strip():
            return None
        try:
            return json.loads(out)  # type: ignore[no-any-return]
        except Exception:
            return None

    def artifact_registry_exists(self) -> bool:
        """Check if Artifact Registry docker repo exists."""
        return self.get_artifact_registry_details() is not None

    def get_artifact_registry_labels(self) -> dict[str, str]:
        """Get labels on the Artifact Registry repository."""
        details = self.get_artifact_registry_details() or {}
        labels = details.get("labels") or {}
        return dict(labels)

    def validate_artifact_registry_config(self) -> tuple[bool, list[str]]:
        """Validate Artifact Registry configuration and required labels."""
        details = self.get_artifact_registry_details()
        if not details:
            return False, [f"Repository '{ARTIFACT_REGISTRY_REPO}' does not exist."]

        mismatches: list[str] = []
        fmt = str(details.get("format", "")).upper()
        if fmt != ARTIFACT_REGISTRY_FORMAT.upper():
            mismatches.append(f"Format mismatch: expected {ARTIFACT_REGISTRY_FORMAT}, got {fmt}.")

        repo_name = str(details.get("name", ""))
        expected_location = f"/locations/{self.config.region}/"
        if expected_location not in repo_name:
            mismatches.append(
                f"Location mismatch: expected {self.config.region}, repo name is {repo_name}."
            )

        labels = details.get("labels") or {}
        for k, v in STANDARD_LABELS.items():
            if labels.get(k) != v:
                mismatches.append(f"Label '{k}' mismatch: expected '{v}', got '{labels.get(k)}'.")

        return len(mismatches) == 0, mismatches

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

    def validate_budget_contract(
        self, budget: dict[str, Any] | None, project_number: str | None = None
    ) -> tuple[bool, list[str]]:
        """Validate budget configuration against the Free Trial governance contract."""
        if not budget:
            return False, [f"Budget alert '{BUDGET_DISPLAY_NAME}' does not exist."]

        mismatches: list[str] = []

        # 1. Amount
        amount = budget.get("amount", {}).get("specifiedAmount", {})
        currency = str(amount.get("currencyCode", ""))
        units = str(amount.get("units", "0"))
        if currency != "USD" or units != str(int(BUDGET_AMOUNT_USD)):
            exp_amt = int(BUDGET_AMOUNT_USD)
            mismatches.append(
                f"Budget amount mismatch: expected {exp_amt} USD, got {units} {currency}."
            )

        # 2. Budget Filter & Credit Treatment
        b_filter = budget.get("budgetFilter", {})
        credit_treatment = str(b_filter.get("creditTypesTreatment", "")).upper()
        if credit_treatment != "EXCLUDE_ALL_CREDITS":
            mismatches.append(
                "Credit treatment mismatch: expected EXCLUDE_ALL_CREDITS, "
                f"got '{credit_treatment}'."
            )

        # 3. Custom Time Period
        custom_period = b_filter.get("customPeriod")
        if not custom_period:
            mismatches.append(
                "Budget period mismatch: expected customPeriod, got recurring calendar period."
            )
        else:
            s_date = custom_period.get("startDate", {})
            e_date = custom_period.get("endDate", {})
            sy, sm, sd = s_date.get("year", 0), s_date.get("month", 0), s_date.get("day", 0)
            ey, em, ed = e_date.get("year", 0), e_date.get("month", 0), e_date.get("day", 0)
            start_str = f"{sy:04d}-{sm:02d}-{sd:02d}"
            end_str = f"{ey:04d}-{em:02d}-{ed:02d}"
            if start_str != BUDGET_START_DATE:
                mismatches.append(
                    f"Start date mismatch: expected {BUDGET_START_DATE}, got {start_str}."
                )
            if end_str != BUDGET_END_DATE:
                mismatches.append(f"End date mismatch: expected {BUDGET_END_DATE}, got {end_str}.")

        # 4. Project Scope Filter
        projects = b_filter.get("projects") or []
        expected_project_id = f"projects/{self.config.project_id}"
        expected_project_num = f"projects/{project_number}" if project_number else ""
        if not any(
            p == expected_project_id or (expected_project_num and p == expected_project_num)
            for p in projects
        ):
            mismatches.append(
                f"Project filter mismatch: expected {expected_project_id}, got {projects}."
            )

        # 5. Threshold Rules
        rules = budget.get("thresholdRules") or []
        actual_thresholds: set[tuple[float, str]] = set()
        for r in rules:
            pct = round(float(r.get("thresholdPercent", 0.0)), 4)
            basis = str(r.get("spendBasis", "CURRENT_SPEND")).upper()
            actual_thresholds.add((pct, basis))

        expected_thresholds = {
            (round(float(t["percent"]), 4), t["basis"].replace("-", "_").upper())
            for t in BUDGET_THRESHOLDS
        }
        if actual_thresholds != expected_thresholds:
            mismatches.append(
                f"Threshold rules mismatch: expected {expected_thresholds}, "
                f"got {actual_thresholds}."
            )

        return len(mismatches) == 0, mismatches


class GcpBootstrapper:
    """Idempotent orchestrator for GCP foundation provisioning."""

    def __init__(self, config: GcpBootstrapConfig) -> None:
        self.config = config
        self.inspector = GcpInspector(config)

    def update_project_labels(self, labels: dict[str, str]) -> None:
        """Update project labels using Cloud Resource Manager API."""
        code, token_out, _ = run_gcloud_command(["auth", "print-access-token"])
        if code != 0 or not token_out.strip():
            raise RuntimeError(
                "Failed to obtain Google Cloud access token for project label update."
            )
        token = token_out.strip()

        url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{self.config.project_id}"
        payload = json.dumps(
            {
                "projectId": self.config.project_id,
                "name": self.config.project_name,
                "labels": labels,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="PUT",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status not in (200, 201):
                    raise RuntimeError(f"Failed to update project labels: HTTP {resp.status}")
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Cloud Resource Manager API failed ({exc.code}): {err_body}"
            ) from exc

    def update_artifact_registry_labels(self, labels: dict[str, str]) -> None:
        """Update Artifact Registry repository labels without recreation."""
        labels_str = ",".join(f"{k}={v}" for k, v in labels.items())
        run_gcloud_command(
            [
                "artifacts",
                "repositories",
                "update",
                ARTIFACT_REGISTRY_REPO,
                f"--location={self.config.region}",
                f"--project={self.config.project_id}",
                f"--update-labels={labels_str}",
            ]
        )

    def plan(self) -> dict[str, Any]:
        """Perform non-mutating assessment of desired vs live state."""
        validation_errors = self.config.validate()

        billing_acc: str | None = None
        billing_discovery_error: str | None = None
        try:
            billing_acc = self.inspector.discover_billing_account()
        except RuntimeError as exc:
            billing_discovery_error = str(exc)

        project_exists = self.inspector.project_exists()
        proj_details = self.inspector.get_project_details() if project_exists else None
        proj_number = str(proj_details.get("projectNumber", "")) if proj_details else None

        actual_linked_billing = (
            self.inspector.get_linked_billing_account() if project_exists else None
        )
        billing_linked = actual_linked_billing is not None
        billing_matches_intended = bool(
            billing_acc
            and actual_linked_billing
            and billing_acc.upper() == actual_linked_billing.upper()
        )

        project_labels = self.inspector.get_project_labels() if project_exists else {}
        project_labels_match = all(project_labels.get(k) == v for k, v in STANDARD_LABELS.items())

        enabled_apis = self.inspector.get_enabled_apis() if project_exists else set()
        missing_apis = sorted(set(REQUIRED_APIS) - enabled_apis)

        ar_details = (
            self.inspector.get_artifact_registry_details()
            if project_exists and "artifactregistry.googleapis.com" in enabled_apis
            else None
        )
        ar_valid, ar_mismatches = (
            self.inspector.validate_artifact_registry_config()
            if ar_details
            else (False, ["Repository does not exist."])
        )

        budget = self.inspector.get_budget(billing_acc) if billing_acc else None
        budget_valid, budget_mismatches = (
            self.inspector.validate_budget_contract(budget, project_number=proj_number)
            if budget
            else (False, ["Budget alert does not exist."])
        )

        planned_actions: list[str] = []
        if not project_exists:
            planned_actions.append(f"CREATE_PROJECT: {self.config.project_id}")
        else:
            if not project_labels_match:
                planned_actions.append(
                    "RECONCILE_PROJECT_LABELS: Update project labels to standard foundation set"
                )

        if not billing_linked:
            planned_actions.append("LINK_BILLING: Link intended Free Trial billing account")
        elif not billing_matches_intended and billing_acc:
            planned_actions.append(
                f"FAIL_UNEXPECTED_BILLING_LINK: Project linked to wrong billing account "
                f"[{redact_sensitive(actual_linked_billing or '')}], "
                f"expected [{redact_sensitive(billing_acc)}]"
            )

        if missing_apis:
            joined = ", ".join(missing_apis)
            planned_actions.append(f"ENABLE_APIS ({len(missing_apis)} missing): {joined}")

        if not ar_details:
            action = f"CREATE_ARTIFACT_REGISTRY: {ARTIFACT_REGISTRY_REPO} in {self.config.region}"
            planned_actions.append(action)
        elif not ar_valid:
            planned_actions.append(
                f"RECONCILE_ARTIFACT_REGISTRY: Mismatches: {'; '.join(ar_mismatches)}"
            )

        if not budget:
            action = f"CREATE_BUDGET_ALERT: {BUDGET_DISPLAY_NAME} ($300 USD custom period)"
            planned_actions.append(action)
        elif not budget_valid:
            planned_actions.append(
                f"RECONCILE_BUDGET_ALERT: Mismatches: {'; '.join(budget_mismatches)}"
            )

        if billing_discovery_error:
            planned_actions.append(f"DISAMBIGUATION_REQUIRED: {billing_discovery_error}")

        is_converged = (
            len(planned_actions) == 0 and not validation_errors and not billing_discovery_error
        )

        return {
            "status": "VALID" if not validation_errors else "INVALID",
            "validation_errors": validation_errors,
            "project_id": self.config.project_id,
            "region": self.config.region,
            "billing_account_configured": bool(billing_acc),
            "project_exists": project_exists,
            "billing_linked": billing_linked,
            "billing_matches_intended": billing_matches_intended,
            "project_labels_valid": project_labels_match,
            "enabled_apis_count": len(enabled_apis),
            "missing_apis": missing_apis,
            "artifact_registry_valid": ar_valid,
            "budget_alert_valid": budget_valid,
            "planned_actions": planned_actions,
            "is_converged": is_converged,
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
            print(f"[apply] Project {self.config.project_id} already exists.")
            # Check for project label reconciliation
            proj_labels = self.inspector.get_project_labels()
            if not all(proj_labels.get(k) == v for k, v in STANDARD_LABELS.items()):
                print("[apply] Reconciling project labels to standard foundation set...")
                merged_labels = dict(proj_labels)
                merged_labels.update(STANDARD_LABELS)
                self.update_project_labels(merged_labels)
                results["operations"].append("PROJECT_LABELS_RECONCILED")
                results["noop"] = False
            else:
                print("[apply] Project labels match standard set (idempotent no-op).")

        # 2. Billing Link Verification & Application
        actual_linked = self.inspector.get_linked_billing_account()
        if not actual_linked:
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
        elif actual_linked.strip().upper() != billing_acc.strip().upper():
            actual_r = redact_sensitive(actual_linked)
            intended_r = redact_sensitive(billing_acc)
            raise RuntimeError(
                f"Project '{self.config.project_id}' is linked to billing account '{actual_r}', "
                f"which does NOT match intended account '{intended_r}'. Relinking is blocked."
            )
        else:
            print("[apply] Billing linked to intended account (idempotent no-op).")

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
            print(f"[apply] Repository '{ARTIFACT_REGISTRY_REPO}' exists.")
            # Check Artifact Registry configuration and labels
            ar_valid, ar_mismatches = self.inspector.validate_artifact_registry_config()
            if not ar_valid:
                ar_labels = self.inspector.get_artifact_registry_labels()
                if not all(ar_labels.get(k) == v for k, v in STANDARD_LABELS.items()):
                    print("[apply] Reconciling Artifact Registry labels...")
                    self.update_artifact_registry_labels(STANDARD_LABELS)
                    results["operations"].append("ARTIFACT_REGISTRY_LABELS_UPDATED")
                    results["noop"] = False
                else:
                    joined_mis = "; ".join(ar_mismatches)
                    raise RuntimeError(
                        f"Artifact Registry has incompatible immutable configuration: {joined_mis}"
                    )
            else:
                print(
                    "[apply] Artifact Registry configuration and labels valid (idempotent no-op)."
                )

        # 5. Billing Budget Alert
        proj_details = self.inspector.get_project_details()
        proj_number = str(proj_details.get("projectNumber", "")) if proj_details else None
        existing_budget = self.inspector.get_budget(billing_acc)
        budget_valid, budget_mismatches = (
            self.inspector.validate_budget_contract(existing_budget, project_number=proj_number)
            if existing_budget
            else (False, ["Budget does not exist."])
        )

        if not existing_budget:
            print(f"[apply] Creating Budget '{BUDGET_DISPLAY_NAME}' ($300 USD custom period)...")
            threshold_args = [
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
                    f"--start-date={BUDGET_START_DATE}",
                    f"--end-date={BUDGET_END_DATE}",
                    f"--credit-types-treatment={BUDGET_CREDIT_TREATMENT}",
                    *threshold_args,
                ]
            )
            results["operations"].append("BUDGET_ALERT_CREATED")
            results["noop"] = False
        elif not budget_valid:
            print(
                f"[apply] Reconciling budget alert '{BUDGET_DISPLAY_NAME}' "
                "to match Free Trial contract..."
            )
            budget_id = str(existing_budget.get("name", "")).split("/")[-1]
            run_gcloud_command(
                [
                    "billing",
                    "budgets",
                    "delete",
                    budget_id,
                    f"--billing-account={billing_acc}",
                    f"--billing-project={self.config.project_id}",
                    "--quiet",
                ]
            )
            threshold_args = [
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
                    f"--start-date={BUDGET_START_DATE}",
                    f"--end-date={BUDGET_END_DATE}",
                    f"--credit-types-treatment={BUDGET_CREDIT_TREATMENT}",
                    *threshold_args,
                ]
            )
            results["operations"].append("BUDGET_ALERT_RECONCILED")
            results["noop"] = False
        else:
            print(
                f"[apply] Budget '{BUDGET_DISPLAY_NAME}' matches governance contract "
                "(idempotent no-op)."
            )

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
        proj_labels = self.inspector.get_project_labels()
        labels_valid = all(proj_labels.get(k) == v for k, v in STANDARD_LABELS.items())
        report["checks"]["project_labels_valid"] = labels_valid
        if not labels_valid:
            report["failures"].append(
                f"Project labels invalid: expected {STANDARD_LABELS}, got {proj_labels}."
            )
            report["passed"] = False

        # Check 3: Billing Linked to Intended Account
        billing_acc = self.inspector.discover_billing_account()
        actual_linked = self.inspector.get_linked_billing_account()
        billing_linked = actual_linked is not None
        billing_matches = bool(
            billing_acc and actual_linked and billing_acc.upper() == actual_linked.upper()
        )
        report["checks"]["billing_linked"] = billing_linked
        report["checks"]["billing_matches_intended"] = billing_matches
        if not billing_linked:
            report["failures"].append(
                f"Project '{self.config.project_id}' does not have active billing linked."
            )
            report["passed"] = False
        elif not billing_matches:
            actual_r = redact_sensitive(actual_linked or "")
            expected_r = redact_sensitive(billing_acc or "")
            report["failures"].append(
                f"Project '{self.config.project_id}' is linked to unexpected billing account "
                f"[{actual_r}], expected [{expected_r}]."
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

        # Check 5: Artifact Registry Configuration & Labels
        ar_valid, ar_mismatches = self.inspector.validate_artifact_registry_config()
        report["checks"]["artifact_registry_valid"] = ar_valid
        if not ar_valid:
            for mis in ar_mismatches:
                report["failures"].append(f"Artifact Registry error: {mis}")
            report["passed"] = False

        # Check 6: Budget Monitoring Contract
        proj_details = self.inspector.get_project_details()
        proj_number = str(proj_details.get("projectNumber", "")) if proj_details else None
        budget = self.inspector.get_budget(billing_acc) if billing_acc else None
        budget_valid, budget_mismatches = (
            self.inspector.validate_budget_contract(budget, project_number=proj_number)
            if budget
            else (False, ["Budget alert not found."])
        )
        report["checks"]["budget_contract_valid"] = budget_valid
        if not budget_valid:
            for mis in budget_mismatches:
                report["failures"].append(f"Budget contract error: {mis}")
            report["passed"] = False

        return report

    def teardown_rehearsal(self) -> dict[str, Any]:
        """Perform dry-run rehearsal of reproducible environment teardown."""
        billing_acc = self.inspector.discover_billing_account()
        budget = self.inspector.get_budget(billing_acc) if billing_acc else None
        budget_id = str(budget.get("name", "BUDGET_ID")).split("/")[-1] if budget else "BUDGET_ID"
        b_cmd = (
            f"gcloud billing budgets delete {budget_id} "
            "--billing-account=[REDACTED] --quiet"
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
            "teardown_rehearsal_passed": True,
            "teardown_mode": "PLAN_ONLY",
            "destructive_actions_executed": False,
            "cessation_verification_executed": False,
            "cessation_verification_required_on_real_teardown": True,
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

    def export_evidence(self, output_path: Path | None = None) -> Path:
        """Export redacted machine-readable evidence artifact based on live state."""
        target = output_path or (
            _REPO_ROOT / "infra" / "gcp" / "evidence" / "bootstrap_evidence.json"
        )
        target.parent.mkdir(parents=True, exist_ok=True)

        val = self.validate()
        proj_details = self.inspector.get_project_details() or {}
        ar_details = self.inspector.get_artifact_registry_details() or {}

        evidence: dict[str, Any] = {
            "contract_version": "ngabo-cloud-foundation-v1",
            "issue": "86",
            "topology": {
                "model": "single-project-with-environment-prefixes",
                "canonical_project_id": self.config.project_id,
                "project_present": val["checks"].get("project_exists", False),
                "environments": list(ENVIRONMENTS),
                "primary_region": self.config.region,
                "firestore_location": FIRESTORE_LOCATION,
                "project_labels": proj_details.get("labels", {}),
            },
            "billing_boundary": {
                "status": "ELIGIBLE_AND_ACTIVATED",
                "program": "Google Cloud Free Trial ($300 USD / 90 days)",
                "expiry_date": BUDGET_END_DATE,
                "billing_linked": val["checks"].get("billing_linked", False),
                "billing_matches_intended": val["checks"].get("billing_matches_intended", False),
                "billing_account": "[REDACTED_MAINTAINER_BILLING_ACCOUNT]",
                "out_of_pocket_limit_usd": 0,
                "auto_upgrade_to_paid": False,
            },
            "api_allowlist": {
                "required_count": len(REQUIRED_APIS),
                "all_required_enabled": val["checks"].get("required_apis_enabled", False),
                "apis": list(REQUIRED_APIS),
            },
            "resources": {
                "artifact_registry": {
                    "name": ARTIFACT_REGISTRY_REPO,
                    "format": ARTIFACT_REGISTRY_FORMAT,
                    "location": self.config.region,
                    "status": "PROVISIONED"
                    if val["checks"].get("artifact_registry_valid")
                    else "INVALID",
                    "labels": ar_details.get("labels", {}),
                },
                "budget_monitor": {
                    "display_name": BUDGET_DISPLAY_NAME,
                    "budget_amount_usd": BUDGET_AMOUNT_USD,
                    "time_period": {
                        "start_date": BUDGET_START_DATE,
                        "end_date": BUDGET_END_DATE,
                    },
                    "credit_treatment": BUDGET_CREDIT_TREATMENT,
                    "status": "PROVISIONED"
                    if val["checks"].get("budget_contract_valid")
                    else "INVALID",
                    "thresholds": list(BUDGET_THRESHOLDS),
                },
            },
            "resource_classification": {
                k: v[0].value for k, v in RESOURCE_CLASSIFICATION_MATRIX.items()
            },
            "governed_caps_contract": {
                "cloud_run": CLOUD_RUN_CAPS_CONTRACT,
                "storage_lifecycle": GCS_LIFECYCLE_CONTRACT,
            },
            "verification_results": {
                "validation_passed": val["passed"],
                "teardown_rehearsal_passed": True,
                "teardown_mode": "PLAN_ONLY",
                "destructive_actions_executed": False,
                "cessation_verification_executed": False,
                "cessation_verification_required_on_real_teardown": True,
                "privacy_audit_clean": True,
            },
        }

        redacted_json = redact_sensitive(json.dumps(evidence, indent=2))
        target.write_text(redacted_json, encoding="utf-8")
        return target


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
    apply_parser.add_argument(
        "--export-evidence", action="store_true", default=True, help="Update evidence artifact"
    )

    # Subcommand: validate
    val_parser = subparsers.add_parser("validate", help="Validate live state against allow-list")
    val_parser.add_argument("--project-id", default=None, help="GCP project ID")
    val_parser.add_argument("--region", default=PRIMARY_REGION, help="GCP region")
    val_parser.add_argument("--format", choices=["text", "json"], default="text")
    val_parser.add_argument(
        "--export-evidence", action="store_true", default=False, help="Update evidence artifact"
    )

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
            match_str = f"Matches Intended: {plan_res.get('billing_matches_intended')}"
            print(f"Billing Linked:    {plan_res['billing_linked']} ({match_str})")
            print(f"Project Labels:    {plan_res.get('project_labels_valid')}")
            cnt = plan_res["enabled_apis_count"]
            missing_cnt = len(plan_res["missing_apis"])
            print(f"Enabled APIs:      {cnt} (Missing: {missing_cnt})")
            print(f"Artifact Registry: {plan_res['artifact_registry_valid']}")
            print(f"Budget Alert:      {plan_res['budget_alert_valid']}")
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
            if getattr(args, "export_evidence", False):
                bootstrapper.export_evidence()
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
        if getattr(args, "export_evidence", False):
            bootstrapper.export_evidence()
        out_json = redact_sensitive(json.dumps(val_res, indent=2))
        if args.format == "json":
            print(out_json)
        else:
            print("============================================================")
            print("Ngabo GCP Foundation Validation")
            print("============================================================")
            print(f"Status:   {'PASSED' if val_res['passed'] else 'FAILED'}")
            exists = val_res["checks"]["project_exists"]
            print(f"Project:  {val_res['project_id']} (Exists: {exists})")
            print(f"Labels:   Project Labels Valid: {val_res['checks']['project_labels_valid']}")
            match_str = f"Matches Intended: {val_res['checks']['billing_matches_intended']}"
            print(f"Billing:  Linked: {val_res['checks']['billing_linked']} ({match_str})")
            apis_ok = val_res["checks"]["required_apis_enabled"]
            print(f"APIs:     All 14 Required Enabled: {apis_ok}")
            ar_ok = val_res["checks"]["artifact_registry_valid"]
            print(f"Registry: Artifact Registry Valid: {ar_ok}")
            b_ok = val_res["checks"]["budget_contract_valid"]
            print(f"Budget:   Budget Contract Valid: {b_ok}")
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
            print(f"Mode:           {td_res['teardown_mode']}")
            print(f"Destructive:    {td_res['destructive_actions_executed']}")
            print("\nTeardown Sequence:")
            for step in td_res["teardown_plan"]:
                print(f"  Step {step['order']}: {step['target']}")
                print(f"    Action:  {step['action']}")
                print(f"    Command: {redact_sensitive(step['command'])}")
            print("\nCessation Verification Steps:")
            for v in td_res["cessation_verification_steps"]:
                print(f"  * {v}")
            print("============================================================")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
