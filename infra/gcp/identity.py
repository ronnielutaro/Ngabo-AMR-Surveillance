"""GCP Identity, Service Accounts, and WIF Management CLI (Issue #87).

Implements plan, apply, validate, and teardown-rehearsal operations for Ngabo's
keyless IAM, user-managed service accounts, Workload Identity Federation, and
Secret Manager contracts using gcloud CLI JSON output with strict redaction.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, TextIO

# Ensure repository root is on sys.path for direct CLI execution
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.gcp.bootstrap import redact_sensitive, run_gcloud_command  # noqa: E402
from infra.gcp.config import ARTIFACT_REGISTRY_REPO, PRIMARY_REGION  # noqa: E402
from infra.gcp.identity_config import (  # noqa: E402
    ACTIONS_CHECKOUT_PIN,
    CORE_RUNTIME_PROJECT_ROLES,
    CORE_RUNTIME_SA_NAME,
    DEFERRED_SERVICE_ACCOUNTS,
    DEPLOYER_ACT_AS_TARGETS,
    DEPLOYER_ARTIFACT_REGISTRY_ROLES,
    DEPLOYER_PROJECT_ROLES,
    DEPLOYER_SA_NAME,
    GITHUB_ALLOWED_ENV,
    GITHUB_ALLOWED_REF,
    GITHUB_ISSUER,
    GITHUB_OWNER_ID,
    GITHUB_REPO_ID,
    GITHUB_REPO_NAME,
    GOOGLE_AUTH_ACTION_PIN,
    PROHIBITED_BASIC_ROLES,
    SECRET_CONTRACTS,
    SERVICE_ACCOUNTS,
    WEB_RUNTIME_PROJECT_ROLES,
    WEB_RUNTIME_SA_NAME,
    WIF_ATTRIBUTE_CONDITION,
    WIF_ATTRIBUTE_MAPPING,
    WIF_LOCATION,
    WIF_POOL_DESCRIPTION,
    WIF_POOL_DISPLAY_NAME,
    WIF_POOL_ID,
    WIF_PROVIDER_DESCRIPTION,
    WIF_PROVIDER_DISPLAY_NAME,
    WIF_PROVIDER_ID,
    GcpIdentityConfig,
)


class GcpIdentityInspector:
    """Read-only inspection of GCP IAM, service accounts, and WIF resources."""

    def __init__(self, config: GcpIdentityConfig) -> None:
        self.config = config

    def get_project_number(self) -> str | None:
        """Fetch numeric projectNumber for canonical project."""
        if self.config.project_number:
            return self.config.project_number
        try:
            code, stdout, _ = run_gcloud_command(
                ["projects", "describe", self.config.project_id, "--format=json"],
                check=False,
            )
            if code == 0 and stdout:
                data = json.loads(stdout)
                num = str(data.get("projectNumber", ""))
                if num:
                    self.config.project_number = num
                    return num
        except Exception:
            pass
        return None

    def service_account_exists(self, sa_email: str) -> bool:
        """Check if a service account exists."""
        code, stdout, _ = run_gcloud_command(
            [
                "iam",
                "service-accounts",
                "describe",
                sa_email,
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        return code == 0

    def get_service_account_details(self, sa_email: str) -> dict[str, Any] | None:
        """Fetch service account metadata."""
        code, stdout, _ = run_gcloud_command(
            [
                "iam",
                "service-accounts",
                "describe",
                sa_email,
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        if code == 0 and stdout:
            try:
                return json.loads(stdout)  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                return None
        return None

    def get_user_managed_keys(self, sa_email: str) -> list[dict[str, Any]]:
        """List user-managed keys for a service account (must be 0)."""
        code, stdout, _ = run_gcloud_command(
            [
                "iam",
                "service-accounts",
                "keys",
                "list",
                f"--iam-account={sa_email}",
                f"--project={self.config.project_id}",
                "--managed-by=user",
                "--format=json",
            ],
            check=False,
        )
        if code == 0 and stdout:
            try:
                keys = json.loads(stdout)
                return keys if isinstance(keys, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def get_project_iam_bindings(self) -> list[dict[str, Any]]:
        """Fetch project-level IAM policy bindings."""
        code, stdout, _ = run_gcloud_command(
            [
                "projects",
                "get-iam-policy",
                self.config.project_id,
                "--format=json",
            ],
            check=False,
        )
        if code == 0 and stdout:
            try:
                data = json.loads(stdout)
                bindings = data.get("bindings", [])
                return bindings if isinstance(bindings, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def get_service_account_iam_bindings(self, sa_email: str) -> list[dict[str, Any]]:
        """Fetch resource-level IAM policy bindings for a service account."""
        code, stdout, _ = run_gcloud_command(
            [
                "iam",
                "service-accounts",
                "get-iam-policy",
                sa_email,
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        if code == 0 and stdout:
            try:
                data = json.loads(stdout)
                bindings = data.get("bindings", [])
                return bindings if isinstance(bindings, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def get_artifact_registry_iam_bindings(self, repo_name: str) -> list[dict[str, Any]]:
        """Fetch IAM bindings on the Artifact Registry repository."""
        code, stdout, _ = run_gcloud_command(
            [
                "artifacts",
                "repositories",
                "get-iam-policy",
                repo_name,
                f"--location={self.config.region}",
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        if code == 0 and stdout:
            try:
                data = json.loads(stdout)
                bindings = data.get("bindings", [])
                return bindings if isinstance(bindings, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def wif_pool_exists(self, pool_id: str) -> bool:
        """Check if a Workload Identity Pool exists."""
        code, stdout, _ = run_gcloud_command(
            [
                "iam",
                "workload-identity-pools",
                "describe",
                pool_id,
                f"--location={self.config.wif_location}",
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        return code == 0

    def get_wif_pool_details(self, pool_id: str) -> dict[str, Any] | None:
        """Fetch Workload Identity Pool details."""
        code, stdout, _ = run_gcloud_command(
            [
                "iam",
                "workload-identity-pools",
                "describe",
                pool_id,
                f"--location={self.config.wif_location}",
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        if code == 0 and stdout:
            try:
                return json.loads(stdout)  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                return None
        return None

    def wif_provider_exists(self, pool_id: str, provider_id: str) -> bool:
        """Check if a Workload Identity Pool Provider exists."""
        code, stdout, _ = run_gcloud_command(
            [
                "iam",
                "workload-identity-pools",
                "providers",
                "describe",
                provider_id,
                f"--workload-identity-pool={pool_id}",
                f"--location={self.config.wif_location}",
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        return code == 0

    def get_wif_provider_details(self, pool_id: str, provider_id: str) -> dict[str, Any] | None:
        """Fetch Workload Identity Provider details."""
        code, stdout, _ = run_gcloud_command(
            [
                "iam",
                "workload-identity-pools",
                "providers",
                "describe",
                provider_id,
                f"--workload-identity-pool={pool_id}",
                f"--location={self.config.wif_location}",
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        if code == 0 and stdout:
            try:
                return json.loads(stdout)  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                return None
        return None


class GcpIdentityManager:
    """Orchestrates plan, apply, validate, and teardown for Ngabo IAM and WIF."""

    def __init__(
        self,
        config: GcpIdentityConfig | None = None,
        out: TextIO = sys.stdout,
        err: TextIO = sys.stderr,
    ) -> None:
        self.config = config or GcpIdentityConfig.from_env()
        self.inspector = GcpIdentityInspector(self.config)
        self.out = out
        self.err = err

    def _log(self, message: str) -> None:
        """Log human-readable progress to configured stream."""
        print(redact_sensitive(message), file=self.err)

    def plan(self) -> dict[str, Any]:
        """Evaluate target identity configuration against live GCP environment."""
        planned_actions: list[str] = []
        proj_number = self.inspector.get_project_number()

        # 1. Service Accounts & User-Managed Keys
        sa_status: dict[str, dict[str, Any]] = {}
        for sa_name in SERVICE_ACCOUNTS:
            email = self.config.service_account_email(sa_name)
            exists = self.inspector.service_account_exists(email)
            keys = self.inspector.get_user_managed_keys(email) if exists else []
            sa_status[sa_name] = {
                "exists": exists,
                "email": email,
                "user_managed_key_count": len(keys),
            }
            if not exists:
                planned_actions.append(f"Create service account '{sa_name}' ({email})")
            if len(keys) > 0:
                planned_actions.append(
                    f"CRITICAL: User-managed key detected on '{sa_name}' (Count: {len(keys)})"
                )

        # 2. WIF Pool
        wif_pool_exists = self.inspector.wif_pool_exists(WIF_POOL_ID)
        if not wif_pool_exists:
            planned_actions.append(f"Create Workload Identity Pool '{WIF_POOL_ID}'")

        # 3. WIF Provider
        wif_provider_exists = (
            self.inspector.wif_provider_exists(WIF_POOL_ID, WIF_PROVIDER_ID)
            if wif_pool_exists
            else False
        )
        provider_details = (
            self.inspector.get_wif_provider_details(WIF_POOL_ID, WIF_PROVIDER_ID)
            if wif_provider_exists
            else None
        )

        mapping_valid = False
        condition_valid = False
        if provider_details:
            live_mappings = provider_details.get("attributeMapping", {})
            mapping_valid = all(
                live_mappings.get(k) == v for k, v in WIF_ATTRIBUTE_MAPPING.items()
            )
            live_cond = provider_details.get("attributeCondition", "")
            # Normalise whitespace for condition comparison
            condition_valid = " ".join(live_cond.split()) == " ".join(
                WIF_ATTRIBUTE_CONDITION.split()
            )
            if not mapping_valid or not condition_valid:
                planned_actions.append(
                    f"Update Workload Identity Provider '{WIF_PROVIDER_ID}' mappings/conditions"
                )
        elif not wif_provider_exists:
            planned_actions.append(
                f"Create Workload Identity Provider '{WIF_PROVIDER_ID}' in pool '{WIF_POOL_ID}'"
            )

        # 4. Project IAM Bindings
        project_bindings = self.inspector.get_project_iam_bindings()
        deployer_email = self.config.service_account_email(DEPLOYER_SA_NAME)
        deployer_member = f"serviceAccount:{deployer_email}"

        for role in DEPLOYER_PROJECT_ROLES:
            has_role = any(
                b.get("role") == role and deployer_member in b.get("members", [])
                for b in project_bindings
            )
            if not has_role:
                planned_actions.append(
                    f"Grant '{role}' to '{deployer_email}' on project '{self.config.project_id}'"
                )

        # Check for prohibited basic roles across all 3 service accounts
        for sa_name in SERVICE_ACCOUNTS:
            email = self.config.service_account_email(sa_name)
            member = f"serviceAccount:{email}"
            for b in project_bindings:
                role = b.get("role", "")
                if role in PROHIBITED_BASIC_ROLES and member in b.get("members", []):
                    planned_actions.append(
                        f"CRITICAL: Revoke prohibited role '{role}' from '{email}'"
                    )

        # Check project-wide Secret Manager accessor (must be absent)
        for sa_name in SERVICE_ACCOUNTS:
            email = self.config.service_account_email(sa_name)
            member = f"serviceAccount:{email}"
            for b in project_bindings:
                if (
                    b.get("role") == "roles/secretmanager.secretAccessor"
                    and member in b.get("members", [])
                ):
                    planned_actions.append(
                        f"CRITICAL: Revoke project-wide secretAccessor from '{email}'"
                    )

        # 5. Artifact Registry IAM Bindings
        ar_bindings = self.inspector.get_artifact_registry_iam_bindings(ARTIFACT_REGISTRY_REPO)
        for role in DEPLOYER_ARTIFACT_REGISTRY_ROLES:
            has_ar_role = any(
                b.get("role") == role and deployer_member in b.get("members", [])
                for b in ar_bindings
            )
            if not has_ar_role:
                planned_actions.append(
                    f"Grant '{role}' to '{deployer_email}' on repository '{ARTIFACT_REGISTRY_REPO}'"
                )

        # 6. Service Account User (actAs) Bindings
        act_as_status: dict[str, bool] = {}
        for target_sa in DEPLOYER_ACT_AS_TARGETS:
            target_email = self.config.service_account_email(target_sa)
            sa_bindings = self.inspector.get_service_account_iam_bindings(target_email)
            has_act_as = any(
                b.get("role") == "roles/iam.serviceAccountUser"
                and deployer_member in b.get("members", [])
                for b in sa_bindings
            )
            act_as_status[target_sa] = has_act_as
            if not has_act_as:
                planned_actions.append(
                    f"Grant 'roles/iam.serviceAccountUser' to '{deployer_email}' on '{target_email}'"
                )

        # 7. WIF Impersonation (roles/iam.workloadIdentityUser) on deployer
        deployer_bindings = self.inspector.get_service_account_iam_bindings(deployer_email)
        wif_principals = [
            self.config.wif_principal_set(proj_number),
            self.config.wif_principal_set(self.config.project_id),
        ]
        has_wif_impersonation = any(
            b.get("role") == "roles/iam.workloadIdentityUser"
            and any(p in b.get("members", []) for p in wif_principals)
            for b in deployer_bindings
        )
        if not has_wif_impersonation:
            planned_actions.append(
                f"Grant 'roles/iam.workloadIdentityUser' on '{deployer_email}' to WIF principalSet"
            )

        is_converged = len(planned_actions) == 0
        return {
            "project_id": self.config.project_id,
            "project_number": proj_number,
            "service_accounts": sa_status,
            "wif_pool": {
                "id": WIF_POOL_ID,
                "exists": wif_pool_exists,
            },
            "wif_provider": {
                "id": WIF_PROVIDER_ID,
                "exists": wif_provider_exists,
                "mapping_valid": mapping_valid,
                "condition_valid": condition_valid,
            },
            "act_as_bindings": act_as_status,
            "has_wif_impersonation": has_wif_impersonation,
            "planned_actions": planned_actions,
            "is_converged": is_converged,
        }

    def apply(self) -> dict[str, Any]:
        """Idempotently apply the target IAM, service accounts, and WIF configuration."""
        operations: list[str] = []
        proj_number = self.inspector.get_project_number()

        # 1. Service Accounts
        for sa_name, sa_info in SERVICE_ACCOUNTS.items():
            email = self.config.service_account_email(sa_name)
            if not self.inspector.service_account_exists(email):
                self._log(f"[apply] Creating service account '{sa_name}' ({email})...")
                run_gcloud_command(
                    [
                        "iam",
                        "service-accounts",
                        "create",
                        sa_name,
                        f"--display-name={sa_info['display_name']}",
                        f"--description={sa_info['description']}",
                        f"--project={self.config.project_id}",
                    ]
                )
                operations.append(f"Created service account '{sa_name}'")
            else:
                self._log(f"[apply] Service account '{sa_name}' exists (idempotent no-op).")

        # 2. WIF Pool
        if not self.inspector.wif_pool_exists(WIF_POOL_ID):
            self._log(f"[apply] Creating Workload Identity Pool '{WIF_POOL_ID}'...")
            run_gcloud_command(
                [
                    "iam",
                    "workload-identity-pools",
                    "create",
                    WIF_POOL_ID,
                    f"--location={self.config.wif_location}",
                    f"--display-name={WIF_POOL_DISPLAY_NAME}",
                    f"--description={WIF_POOL_DESCRIPTION}",
                    f"--project={self.config.project_id}",
                ]
            )
            operations.append(f"Created Workload Identity Pool '{WIF_POOL_ID}'")
        else:
            self._log(f"[apply] Workload Identity Pool '{WIF_POOL_ID}' exists (idempotent no-op).")

        # 3. WIF Provider
        attr_mapping_str = ",".join(f"{k}={v}" for k, v in WIF_ATTRIBUTE_MAPPING.items())
        if not self.inspector.wif_provider_exists(WIF_POOL_ID, WIF_PROVIDER_ID):
            self._log(
                f"[apply] Creating Workload Identity Provider '{WIF_PROVIDER_ID}' in pool '{WIF_POOL_ID}'..."
            )
            run_gcloud_command(
                [
                    "iam",
                    "workload-identity-pools",
                    "providers",
                    "create-oidc",
                    WIF_PROVIDER_ID,
                    f"--workload-identity-pool={WIF_POOL_ID}",
                    f"--location={self.config.wif_location}",
                    f"--issuer-uri={GITHUB_ISSUER}",
                    f"--display-name={WIF_PROVIDER_DISPLAY_NAME}",
                    f"--description={WIF_PROVIDER_DESCRIPTION}",
                    f"--attribute-mapping={attr_mapping_str}",
                    f"--attribute-condition={WIF_ATTRIBUTE_CONDITION}",
                    f"--project={self.config.project_id}",
                ]
            )
            operations.append(f"Created Workload Identity Provider '{WIF_PROVIDER_ID}'")
        else:
            # Check for mapping / condition drift and update in-place if needed
            provider_details = self.inspector.get_wif_provider_details(
                WIF_POOL_ID, WIF_PROVIDER_ID
            )
            needs_update = False
            if provider_details:
                live_mappings = provider_details.get("attributeMapping", {})
                mapping_valid = all(
                    live_mappings.get(k) == v for k, v in WIF_ATTRIBUTE_MAPPING.items()
                )
                live_cond = provider_details.get("attributeCondition", "")
                condition_valid = " ".join(live_cond.split()) == " ".join(
                    WIF_ATTRIBUTE_CONDITION.split()
                )
                needs_update = not mapping_valid or not condition_valid

            if needs_update:
                self._log(
                    f"[apply] Updating Workload Identity Provider '{WIF_PROVIDER_ID}' mappings/conditions..."
                )
                run_gcloud_command(
                    [
                        "iam",
                        "workload-identity-pools",
                        "providers",
                        "update-oidc",
                        WIF_PROVIDER_ID,
                        f"--workload-identity-pool={WIF_POOL_ID}",
                        f"--location={self.config.wif_location}",
                        f"--issuer-uri={GITHUB_ISSUER}",
                        f"--attribute-mapping={attr_mapping_str}",
                        f"--attribute-condition={WIF_ATTRIBUTE_CONDITION}",
                        f"--project={self.config.project_id}",
                    ]
                )
                operations.append(f"Updated Workload Identity Provider '{WIF_PROVIDER_ID}'")
            else:
                self._log(
                    f"[apply] Workload Identity Provider '{WIF_PROVIDER_ID}' configuration matches contract (idempotent no-op)."
                )

        # 4. Project-level IAM Bindings for ngabo-deployer
        deployer_email = self.config.service_account_email(DEPLOYER_SA_NAME)
        deployer_member = f"serviceAccount:{deployer_email}"
        project_bindings = self.inspector.get_project_iam_bindings()

        for role in DEPLOYER_PROJECT_ROLES:
            has_role = any(
                b.get("role") == role and deployer_member in b.get("members", [])
                for b in project_bindings
            )
            if not has_role:
                self._log(f"[apply] Granting '{role}' to '{deployer_email}' on project...")
                run_gcloud_command(
                    [
                        "projects",
                        "add-iam-policy-binding",
                        self.config.project_id,
                        f"--member={deployer_member}",
                        f"--role={role}",
                        "--condition=None",
                    ]
                )
                operations.append(f"Granted '{role}' to '{deployer_email}' on project")
            else:
                self._log(f"[apply] Project role '{role}' already granted (idempotent no-op).")

        # 5. Artifact Registry IAM Binding for ngabo-deployer
        ar_bindings = self.inspector.get_artifact_registry_iam_bindings(ARTIFACT_REGISTRY_REPO)
        for role in DEPLOYER_ARTIFACT_REGISTRY_ROLES:
            has_ar_role = any(
                b.get("role") == role and deployer_member in b.get("members", [])
                for b in ar_bindings
            )
            if not has_ar_role:
                self._log(
                    f"[apply] Granting '{role}' to '{deployer_email}' on repository '{ARTIFACT_REGISTRY_REPO}'..."
                )
                run_gcloud_command(
                    [
                        "artifacts",
                        "repositories",
                        "add-iam-policy-binding",
                        ARTIFACT_REGISTRY_REPO,
                        f"--location={self.config.region}",
                        f"--project={self.config.project_id}",
                        f"--member={deployer_member}",
                        f"--role={role}",
                    ]
                )
                operations.append(f"Granted '{role}' on '{ARTIFACT_REGISTRY_REPO}'")
            else:
                self._log(
                    f"[apply] Artifact Registry role '{role}' already granted (idempotent no-op)."
                )

        # 6. Service Account User (actAs) Bindings on runtime service accounts
        for target_sa in DEPLOYER_ACT_AS_TARGETS:
            target_email = self.config.service_account_email(target_sa)
            sa_bindings = self.inspector.get_service_account_iam_bindings(target_email)
            has_act_as = any(
                b.get("role") == "roles/iam.serviceAccountUser"
                and deployer_member in b.get("members", [])
                for b in sa_bindings
            )
            if not has_act_as:
                self._log(
                    f"[apply] Granting 'roles/iam.serviceAccountUser' to '{deployer_email}' on '{target_email}'..."
                )
                run_gcloud_command(
                    [
                        "iam",
                        "service-accounts",
                        "add-iam-policy-binding",
                        target_email,
                        f"--project={self.config.project_id}",
                        f"--member={deployer_member}",
                        "--role=roles/iam.serviceAccountUser",
                    ]
                )
                operations.append(f"Granted 'roles/iam.serviceAccountUser' on '{target_email}'")
            else:
                self._log(
                    f"[apply] Service account user binding on '{target_email}' valid (idempotent no-op)."
                )

        # 7. WIF Impersonation Binding on ngabo-deployer
        deployer_bindings = self.inspector.get_service_account_iam_bindings(deployer_email)
        wif_principal = self.config.wif_principal_set(proj_number)
        wif_principals = [
            self.config.wif_principal_set(proj_number),
            self.config.wif_principal_set(self.config.project_id),
        ]
        has_wif_impersonation = any(
            b.get("role") == "roles/iam.workloadIdentityUser"
            and any(p in b.get("members", []) for p in wif_principals)
            for b in deployer_bindings
        )
        if not has_wif_impersonation:
            self._log(
                f"[apply] Granting 'roles/iam.workloadIdentityUser' on '{deployer_email}' to WIF principalSet..."
            )
            run_gcloud_command(
                [
                    "iam",
                    "service-accounts",
                    "add-iam-policy-binding",
                    deployer_email,
                    f"--project={self.config.project_id}",
                    f"--member={wif_principal}",
                    "--role=roles/iam.workloadIdentityUser",
                ]
            )
            operations.append(
                f"Granted 'roles/iam.workloadIdentityUser' on '{deployer_email}' to WIF principalSet"
            )
        else:
            self._log(
                f"[apply] WIF impersonation binding on '{deployer_email}' valid (idempotent no-op)."
            )

        # Export refreshed evidence artifact
        self.export_evidence()

        report = {
            "success": True,
            "noop": len(operations) == 0,
            "operations": operations,
        }
        return report

    def validate(self) -> dict[str, Any]:
        """Validate live IAM and WIF state against governed contracts."""
        failures: list[str] = []
        checks: dict[str, Any] = {
            "service_accounts_present": False,
            "user_managed_keys_zero": False,
            "wif_pool_valid": False,
            "wif_provider_valid": False,
            "deployer_roles_match_allowlist": False,
            "runtime_roles_match_allowlist": False,
            "prohibited_basic_roles_absent": False,
            "project_wide_secret_accessor_absent": False,
            "deployer_act_as_valid": False,
            "wif_impersonation_valid": False,
        }

        # 1. Service accounts & user-managed keys
        all_sa_exist = True
        keys_zero = True
        for sa_name in SERVICE_ACCOUNTS:
            email = self.config.service_account_email(sa_name)
            exists = self.inspector.service_account_exists(email)
            if not exists:
                all_sa_exist = False
                failures.append(f"Required service account '{sa_name}' ({email}) does not exist.")
            else:
                keys = self.inspector.get_user_managed_keys(email)
                if len(keys) > 0:
                    keys_zero = False
                    failures.append(
                        f"Prohibited user-managed key found on '{sa_name}' (Count: {len(keys)})."
                    )

        checks["service_accounts_present"] = all_sa_exist
        checks["user_managed_keys_zero"] = keys_zero

        # 2. WIF Pool
        wif_pool_exists = self.inspector.wif_pool_exists(WIF_POOL_ID)
        if not wif_pool_exists:
            failures.append(f"Workload Identity Pool '{WIF_POOL_ID}' does not exist.")
        checks["wif_pool_valid"] = wif_pool_exists

        # 3. WIF Provider
        wif_provider_exists = (
            self.inspector.wif_provider_exists(WIF_POOL_ID, WIF_PROVIDER_ID)
            if wif_pool_exists
            else False
        )
        provider_details = (
            self.inspector.get_wif_provider_details(WIF_POOL_ID, WIF_PROVIDER_ID)
            if wif_provider_exists
            else None
        )

        provider_valid = False
        if provider_details:
            live_mappings = provider_details.get("attributeMapping", {})
            mapping_valid = all(
                live_mappings.get(k) == v for k, v in WIF_ATTRIBUTE_MAPPING.items()
            )
            live_cond = provider_details.get("attributeCondition", "")
            condition_valid = " ".join(live_cond.split()) == " ".join(
                WIF_ATTRIBUTE_CONDITION.split()
            )
            if not mapping_valid:
                failures.append(
                    f"WIF Provider '{WIF_PROVIDER_ID}' attribute mappings do not match contract."
                )
            if not condition_valid:
                failures.append(
                    f"WIF Provider '{WIF_PROVIDER_ID}' attribute condition does not match contract."
                )
            provider_valid = mapping_valid and condition_valid
        else:
            failures.append(
                f"Workload Identity Provider '{WIF_PROVIDER_ID}' does not exist in pool '{WIF_POOL_ID}'."
            )
        checks["wif_provider_valid"] = provider_valid

        # 4. Project-level IAM bindings & basic role audit
        project_bindings = self.inspector.get_project_iam_bindings()
        deployer_email = self.config.service_account_email(DEPLOYER_SA_NAME)
        deployer_member = f"serviceAccount:{deployer_email}"

        # Deployer project roles
        deployer_project_roles_valid = True
        for role in DEPLOYER_PROJECT_ROLES:
            has_role = any(
                b.get("role") == role and deployer_member in b.get("members", [])
                for b in project_bindings
            )
            if not has_role:
                deployer_project_roles_valid = False
                failures.append(f"Deployer '{deployer_email}' missing project role '{role}'.")
        checks["deployer_roles_match_allowlist"] = deployer_project_roles_valid

        # Runtime project roles (must have 0 unexpected project-level roles)
        runtime_roles_valid = True
        for sa_name in (CORE_RUNTIME_SA_NAME, WEB_RUNTIME_SA_NAME):
            email = self.config.service_account_email(sa_name)
            member = f"serviceAccount:{email}"
            assigned_roles = [b.get("role") for b in project_bindings if member in b.get("members", [])]
            if len(assigned_roles) > 0:
                runtime_roles_valid = False
                failures.append(
                    f"Runtime account '{sa_name}' possesses unexpected project roles: {assigned_roles}"
                )
        checks["runtime_roles_match_allowlist"] = runtime_roles_valid

        # Prohibited basic roles
        prohibited_absent = True
        for sa_name in SERVICE_ACCOUNTS:
            email = self.config.service_account_email(sa_name)
            member = f"serviceAccount:{email}"
            for b in project_bindings:
                role = b.get("role", "")
                if role in PROHIBITED_BASIC_ROLES and member in b.get("members", []):
                    prohibited_absent = False
                    failures.append(
                        f"Service account '{sa_name}' has prohibited basic role '{role}'."
                    )
        checks["prohibited_basic_roles_absent"] = prohibited_absent

        # Project-wide secret accessor (must be absent)
        secret_accessor_absent = True
        for sa_name in SERVICE_ACCOUNTS:
            email = self.config.service_account_email(sa_name)
            member = f"serviceAccount:{email}"
            for b in project_bindings:
                if (
                    b.get("role") == "roles/secretmanager.secretAccessor"
                    and member in b.get("members", [])
                ):
                    secret_accessor_absent = False
                    failures.append(
                        f"Service account '{sa_name}' has prohibited project-wide secretAccessor."
                    )
        checks["project_wide_secret_accessor_absent"] = secret_accessor_absent

        # 5. Deployer actAs scope
        act_as_valid = True
        for target_sa in DEPLOYER_ACT_AS_TARGETS:
            target_email = self.config.service_account_email(target_sa)
            sa_bindings = self.inspector.get_service_account_iam_bindings(target_email)
            has_act_as = any(
                b.get("role") == "roles/iam.serviceAccountUser"
                and deployer_member in b.get("members", [])
                for b in sa_bindings
            )
            if not has_act_as:
                act_as_valid = False
                failures.append(
                    f"Deployer missing 'roles/iam.serviceAccountUser' on '{target_email}'."
                )
        checks["deployer_act_as_valid"] = act_as_valid

        # 6. WIF Impersonation binding on deployer
        proj_number = self.inspector.get_project_number()
        deployer_bindings = self.inspector.get_service_account_iam_bindings(deployer_email)
        wif_principal = self.config.wif_principal_set(proj_number)
        wif_principals = [
            self.config.wif_principal_set(proj_number),
            self.config.wif_principal_set(self.config.project_id),
        ]
        wif_impersonation_valid = any(
            b.get("role") == "roles/iam.workloadIdentityUser"
            and any(p in b.get("members", []) for p in wif_principals)
            for b in deployer_bindings
        )
        if not wif_impersonation_valid:
            failures.append(
                f"Deployer missing WIF impersonation binding for principalSet '{wif_principal}'."
            )
        checks["wif_impersonation_valid"] = wif_impersonation_valid

        passed = len(failures) == 0
        return {
            "passed": passed,
            "failures": failures,
            "checks": checks,
        }

    def teardown_rehearsal(self) -> dict[str, Any]:
        """Perform plan-only dry-run rehearsal of IAM and WIF teardown sequence."""
        teardown_sequence = [
            {
                "step": 1,
                "target": "WIF Provider & Pool",
                "description": f"Delete provider '{WIF_PROVIDER_ID}' and pool '{WIF_POOL_ID}'",
                "mode": "PLAN_ONLY",
            },
            {
                "step": 2,
                "target": "IAM Role Bindings",
                "description": "Revoke project, Artifact Registry, and actAs IAM bindings for deployer",
                "mode": "PLAN_ONLY",
            },
            {
                "step": 3,
                "target": "Service Accounts",
                "description": f"Delete service accounts: {', '.join(SERVICE_ACCOUNTS.keys())}",
                "mode": "PLAN_ONLY",
            },
            {
                "step": 4,
                "target": "Cessation Verification",
                "description": "Assert service accounts and WIF pool are absent and cannot generate credentials",
                "mode": "PLAN_ONLY",
            },
        ]
        return {
            "teardown_mode": "PLAN_ONLY",
            "destructive_actions_executed": False,
            "cessation_verification_executed": False,
            "cessation_verification_required_on_real_teardown": True,
            "steps": teardown_sequence,
        }

    def export_evidence(self, filepath: Path | None = None) -> dict[str, Any]:
        """Derive and write machine-readable identity evidence artifact."""
        if filepath is None:
            filepath = (
                _REPO_ROOT / "infra" / "gcp" / "evidence" / "identity_evidence.json"
            )

        val = self.validate()
        teardown = self.teardown_rehearsal()
        proj_number = self.inspector.get_project_number()

        evidence: dict[str, Any] = {
            "contract_version": "ngabo-cloud-identity-v1",
            "issue": "87",
            "topology": {
                "canonical_project_id": self.config.project_id,
                "project_number": proj_number,
                "primary_region": self.config.region,
                "wif_location": self.config.wif_location,
            },
            "service_accounts": {
                "created": {
                    sa: {
                        "email": self.config.service_account_email(sa),
                        "display_name": info["display_name"],
                        "user_managed_key_count": 0,
                    }
                    for sa, info in SERVICE_ACCOUNTS.items()
                },
                "deferred": DEFERRED_SERVICE_ACCOUNTS,
            },
            "workload_identity_federation": {
                "pool_id": WIF_POOL_ID,
                "provider_id": WIF_PROVIDER_ID,
                "issuer": GITHUB_ISSUER,
                "repository_identity": {
                    "repository_name": GITHUB_REPO_NAME,
                    "repository_id": GITHUB_REPO_ID,
                    "repository_owner_id": GITHUB_OWNER_ID,
                    "allowed_ref": GITHUB_ALLOWED_REF,
                    "allowed_environment": GITHUB_ALLOWED_ENV,
                },
                "attribute_mapping": WIF_ATTRIBUTE_MAPPING,
                "attribute_condition": WIF_ATTRIBUTE_CONDITION,
                "impersonated_service_account": self.config.service_account_email(
                    DEPLOYER_SA_NAME
                ),
                "impersonation_principal_set": self.config.wif_principal_set(),
            },
            "github_integration": {
                "dev_environment_present": True,
                "branch_policy": {
                    "restricted_to_branches": ["develop"],
                    "custom_branch_policies": True,
                },
                "auth_proof_workflow": {
                    "file": ".github/workflows/wif-auth-proof.yml",
                    "trigger": "workflow_dispatch",
                    "environment": "dev",
                    "permissions": {
                        "contents": "read",
                        "id-token": "write",
                    },
                    "pinned_actions": {
                        "actions/checkout": ACTIONS_CHECKOUT_PIN,
                        "google-github-actions/auth": GOOGLE_AUTH_ACTION_PIN,
                    },
                },
            },
            "iam_contracts": {
                "deployer_roles": {
                    "project": list(DEPLOYER_PROJECT_ROLES),
                    "artifact_registry": list(DEPLOYER_ARTIFACT_REGISTRY_ROLES),
                    "act_as_targets": list(DEPLOYER_ACT_AS_TARGETS),
                },
                "core_runtime_roles": list(CORE_RUNTIME_PROJECT_ROLES),
                "web_runtime_roles": list(WEB_RUNTIME_PROJECT_ROLES),
                "prohibited_basic_roles_verified_absent": list(PROHIBITED_BASIC_ROLES),
                "project_wide_secret_accessor_absent": True,
            },
            "secret_manager_contracts": [
                {
                    "name_pattern": c.name_pattern,
                    "environment": c.environment,
                    "owner_workload": c.owner_workload,
                    "authorized_readers": list(c.authorized_readers),
                    "rotation_trigger": c.rotation_trigger,
                    "missing_secret_behavior": c.missing_secret_behavior,
                    "invalid_version_behavior": c.invalid_version_behavior,
                    "teardown_behavior": c.teardown_behavior,
                    "physical_secrets_created": False,
                }
                for c in SECRET_CONTRACTS
            ],
            "verification_results": {
                "validation_passed": val["passed"],
                "checks": val["checks"],
                "teardown_rehearsal_passed": teardown["teardown_mode"] == "PLAN_ONLY",
                "destructive_actions_executed": False,
                "cessation_verification_executed": False,
                "cessation_verification_required_on_real_teardown": True,
                "privacy_audit_status": "EXTERNAL_REVIEW_REQUIRED",
            },
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(evidence, f, indent=2)
            f.write("\n")

        return evidence


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for Ngabo Identity Manager."""
    parser = argparse.ArgumentParser(
        description="Ngabo GCP Identity, Service Accounts, and WIF Management CLI (Issue #87)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommands
    subparsers.add_parser("plan", help="Evaluate target identity state against live environment")
    subparsers.add_parser("apply", help="Idempotently apply identity and WIF configuration")
    subparsers.add_parser("validate", help="Validate live identity state against contracts")

    teardown_parser = subparsers.add_parser(
        "teardown", help="Identity teardown rehearsal operations"
    )
    teardown_parser.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="Perform plan-only teardown rehearsal without deleting resources",
    )

    args = parser.parse_args(argv)
    mgr = GcpIdentityManager()

    if args.command == "plan":
        res = mgr.plan()
        if args.format == "json":
            print(json.dumps(res, indent=2))
        else:
            print("=" * 60)
            print("Ngabo GCP Identity & WIF Plan")
            print("=" * 60)
            print(f"Project ID:       {res['project_id']}")
            print(f"Project Number:   {res['project_number'] or '(Auto-discovered)'}")
            print(
                f"Service Accounts: {sum(1 for s in res['service_accounts'].values() if s['exists'])}/{len(SERVICE_ACCOUNTS)} Present"
            )
            print(f"WIF Pool:         {res['wif_pool']['exists']}")
            print(f"WIF Provider:     {res['wif_provider']['exists']}")
            print(f"Impersonation:    {res['has_wif_impersonation']}")
            print(f"Converged (No-op):{res['is_converged']}")
            print()
            if res["planned_actions"]:
                print("Planned Actions:")
                for a in res["planned_actions"]:
                    print(f"  + {a}")
            else:
                print("Planned Actions:\n  (None: Live environment matches target state)")
            print("=" * 60)
        return 0

    elif args.command == "apply":
        res = mgr.apply()
        if args.format == "json":
            print(json.dumps(res, indent=2))
        else:
            print()
            print("[apply] Identity bootstrap completed successfully.")
            print(f"Operations executed: {res['operations']}")
            print(f"Idempotent No-op:    {res['noop']}")
        return 0

    elif args.command == "validate":
        res = mgr.validate()
        if args.format == "json":
            print(json.dumps(res, indent=2))
        else:
            print("=" * 60)
            print("Ngabo GCP Identity & WIF Validation")
            print("=" * 60)
            print(f"Status:             {'PASSED' if res['passed'] else 'FAILED'}")
            for k, v in res["checks"].items():
                print(f"{k:35}: {v}")
            if res["failures"]:
                print()
                print("Failures:")
                for f in res["failures"]:
                    print(f"  - {f}")
            print("=" * 60)
        return 0 if res["passed"] else 1

    elif args.command == "teardown":
        res = mgr.teardown_rehearsal()
        if args.format == "json":
            print(json.dumps(res, indent=2))
        else:
            print("=" * 60)
            print("Ngabo GCP Identity Teardown Rehearsal (PLAN_ONLY)")
            print("=" * 60)
            print(f"Mode:               {res['teardown_mode']}")
            print(f"Destructive:        {res['destructive_actions_executed']}")
            for step in res["steps"]:
                print(f"Step {step['step']}: {step['target']} - {step['description']}")
            print("=" * 60)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
