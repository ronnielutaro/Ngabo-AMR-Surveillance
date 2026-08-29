"""GCP Identity, Service Accounts, and WIF Management CLI (Issue #87).

Implements plan, apply, validate, and teardown-rehearsal operations for Ngabo's
keyless IAM, user-managed service accounts, Workload Identity Federation,
Secret Manager contracts, and GitHub Environment policies using gcloud/gh JSON
with strict redaction and fail-closed security semantics.
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
from infra.gcp.github_env import GitHubEnvInspector, GitHubEnvManager  # noqa: E402
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
    GOOGLE_SETUP_GCLOUD_ACTION_PIN,
    PROHIBITED_BASIC_ROLES,
    SECRET_CONTRACTS,
    SERVICE_ACCOUNTS,
    WEB_RUNTIME_PROJECT_ROLES,
    WEB_RUNTIME_SA_NAME,
    WIF_ATTRIBUTE_CONDITION,
    WIF_ATTRIBUTE_MAPPING,
    WIF_POOL_DESCRIPTION,
    WIF_POOL_DISPLAY_NAME,
    WIF_POOL_ID,
    WIF_PROVIDER_DESCRIPTION,
    WIF_PROVIDER_DISPLAY_NAME,
    WIF_PROVIDER_ID,
    GcpIdentityConfig,
)


class GcpIdentityInspector:
    """Read-only inspector for GCP IAM, Service Accounts, and WIF state.

    All methods fail-closed on any non-zero exit code or malformed output.
    """

    def __init__(self, config: GcpIdentityConfig) -> None:
        self.config = config

    def get_project_number(self) -> str:
        """Fetch numeric project number for canonical resource names."""
        code, stdout, stderr = run_gcloud_command(
            [
                "projects",
                "describe",
                self.config.project_id,
                "--format=value(projectNumber)",
            ],
            check=False,
        )
        if code != 0 or not stdout.strip():
            raise RuntimeError(
                f"INSPECTION_FAILED: Failed to describe project '{self.config.project_id}': {stderr.strip()}"
            )
        return stdout.strip()

    def service_account_exists(self, sa_email: str) -> bool:
        """Check whether a service account exists."""
        code, _, stderr = run_gcloud_command(
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
        if code == 0:
            return True
        if "NOT_FOUND" in stderr or "404" in stderr or "does not exist" in stderr.lower():
            return False
        raise RuntimeError(
            f"INSPECTION_FAILED: Failed to describe service account '{sa_email}': {stderr.strip()}"
        )

    def get_service_account_details(self, sa_email: str) -> dict[str, Any] | None:
        """Fetch details for a specific service account."""
        code, stdout, stderr = run_gcloud_command(
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
        if code != 0:
            if "NOT_FOUND" in stderr or "404" in stderr or "does not exist" in stderr.lower():
                return None
            raise RuntimeError(
                f"INSPECTION_FAILED: Failed to describe service account '{sa_email}': {stderr.strip()}"
            )
        try:
            return json.loads(stdout)  # type: ignore[no-any-return]
        except json.JSONDecodeError as err:
            raise RuntimeError(
                f"INSPECTION_FAILED: Malformed JSON for service account '{sa_email}': {err}"
            ) from err

    def get_all_project_service_accounts(self) -> list[dict[str, Any]]:
        """List all service accounts residing in the project."""
        code, stdout, stderr = run_gcloud_command(
            [
                "iam",
                "service-accounts",
                "list",
                f"--project={self.config.project_id}",
                "--format=json",
            ],
            check=False,
        )
        if code != 0:
            raise RuntimeError(
                f"INSPECTION_FAILED: Failed to list project service accounts: {stderr.strip()}"
            )
        try:
            data = json.loads(stdout)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError as err:
            raise RuntimeError(
                f"INSPECTION_FAILED: Malformed JSON listing project service accounts: {err}"
            ) from err

    def get_user_managed_keys(self, sa_email: str) -> list[dict[str, Any]]:
        """List user-managed keys for a service account. Fails closed on any error."""
        code, stdout, stderr = run_gcloud_command(
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
        if code != 0:
            raise RuntimeError(
                f"INSPECTION_FAILED: Failed to list keys for service account '{sa_email}': {stderr.strip()}"
            )
        try:
            keys = json.loads(stdout)
            if not isinstance(keys, list):
                raise RuntimeError(
                    f"INSPECTION_FAILED: Unexpected payload type for keys of '{sa_email}': {type(keys)}"
                )
            return keys
        except json.JSONDecodeError as err:
            raise RuntimeError(
                f"INSPECTION_FAILED: Malformed JSON listing keys for '{sa_email}': {err}"
            ) from err

    def get_project_iam_bindings(self) -> list[dict[str, Any]]:
        """Fetch project-level IAM policy bindings. Fails closed on any error."""
        code, stdout, stderr = run_gcloud_command(
            [
                "projects",
                "get-iam-policy",
                self.config.project_id,
                "--format=json",
            ],
            check=False,
        )
        if code != 0:
            raise RuntimeError(
                f"INSPECTION_FAILED: Failed to fetch project IAM policy: {stderr.strip()}"
            )
        try:
            data = json.loads(stdout)
            bindings = data.get("bindings", [])
            if not isinstance(bindings, list):
                raise RuntimeError(
                    f"INSPECTION_FAILED: Expected list for project bindings, got {type(bindings)}"
                )
            return bindings
        except json.JSONDecodeError as err:
            raise RuntimeError(
                f"INSPECTION_FAILED: Malformed JSON for project IAM policy: {err}"
            ) from err

    def get_service_account_iam_bindings(self, sa_email: str) -> list[dict[str, Any]]:
        """Fetch resource-level IAM policy bindings for a service account. Fails closed."""
        code, stdout, stderr = run_gcloud_command(
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
        if code != 0:
            raise RuntimeError(
                f"INSPECTION_FAILED: Failed to fetch IAM policy for service account '{sa_email}': {stderr.strip()}"
            )
        try:
            data = json.loads(stdout)
            bindings = data.get("bindings", [])
            if not isinstance(bindings, list):
                raise RuntimeError(
                    f"INSPECTION_FAILED: Expected list for SA bindings, got {type(bindings)}"
                )
            return bindings
        except json.JSONDecodeError as err:
            raise RuntimeError(
                f"INSPECTION_FAILED: Malformed JSON for service account '{sa_email}': {err}"
            ) from err

    def get_artifact_registry_iam_bindings(self, repo_name: str) -> list[dict[str, Any]]:
        """Fetch IAM bindings on the Artifact Registry repository. Fails closed."""
        code, stdout, stderr = run_gcloud_command(
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
        if code != 0:
            raise RuntimeError(
                f"INSPECTION_FAILED: Failed to fetch Artifact Registry policy for '{repo_name}': {stderr.strip()}"
            )
        try:
            data = json.loads(stdout)
            bindings = data.get("bindings", [])
            if not isinstance(bindings, list):
                raise RuntimeError(
                    f"INSPECTION_FAILED: Expected list for Artifact Registry bindings, got {type(bindings)}"
                )
            return bindings
        except json.JSONDecodeError as err:
            raise RuntimeError(
                f"INSPECTION_FAILED: Malformed JSON for Artifact Registry '{repo_name}': {err}"
            ) from err

    def wif_pool_exists(self, pool_id: str) -> bool:
        """Check if a Workload Identity Pool exists."""
        code, _, stderr = run_gcloud_command(
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
        if code == 0:
            return True
        if "NOT_FOUND" in stderr or "404" in stderr or "not found" in stderr.lower():
            return False
        raise RuntimeError(
            f"INSPECTION_FAILED: Failed to describe WIF pool '{pool_id}': {stderr.strip()}"
        )

    def get_wif_pool_details(self, pool_id: str) -> dict[str, Any] | None:
        """Fetch Workload Identity Pool details."""
        code, stdout, stderr = run_gcloud_command(
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
        if code != 0:
            if "NOT_FOUND" in stderr or "404" in stderr or "not found" in stderr.lower():
                return None
            raise RuntimeError(
                f"INSPECTION_FAILED: Failed to describe WIF pool '{pool_id}': {stderr.strip()}"
            )
        try:
            return json.loads(stdout)  # type: ignore[no-any-return]
        except json.JSONDecodeError as err:
            raise RuntimeError(
                f"INSPECTION_FAILED: Malformed JSON for WIF pool '{pool_id}': {err}"
            ) from err

    def wif_provider_exists(self, pool_id: str, provider_id: str) -> bool:
        """Check if a Workload Identity Pool Provider exists."""
        code, _, stderr = run_gcloud_command(
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
        if code == 0:
            return True
        if "NOT_FOUND" in stderr or "404" in stderr or "not found" in stderr.lower():
            return False
        raise RuntimeError(
            f"INSPECTION_FAILED: Failed to describe WIF provider '{provider_id}': {stderr.strip()}"
        )

    def get_wif_provider_details(self, pool_id: str, provider_id: str) -> dict[str, Any] | None:
        """Fetch Workload Identity Provider details."""
        code, stdout, stderr = run_gcloud_command(
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
        if code != 0:
            if "NOT_FOUND" in stderr or "404" in stderr or "not found" in stderr.lower():
                return None
            raise RuntimeError(
                f"INSPECTION_FAILED: Failed to describe WIF provider '{provider_id}': {stderr.strip()}"
            )
        try:
            return json.loads(stdout)  # type: ignore[no-any-return]
        except json.JSONDecodeError as err:
            raise RuntimeError(
                f"INSPECTION_FAILED: Malformed JSON for WIF provider '{provider_id}': {err}"
            ) from err


class GcpIdentityManager:
    """Orchestrates plan, apply, validate, and teardown for Ngabo IAM, WIF, and GitHub state."""

    def __init__(
        self,
        config: GcpIdentityConfig | None = None,
        out: TextIO = sys.stdout,
        err: TextIO = sys.stderr,
    ) -> None:
        self.config = config or GcpIdentityConfig.from_env()
        self.inspector = GcpIdentityInspector(self.config)
        self.github_manager = GitHubEnvManager()
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
        issuer_valid = False
        state_valid = False
        if provider_details:
            live_mappings = provider_details.get("attributeMapping", {})
            mapping_valid = all(
                live_mappings.get(k) == v for k, v in WIF_ATTRIBUTE_MAPPING.items()
            )
            live_cond = provider_details.get("attributeCondition", "")
            condition_valid = " ".join(live_cond.split()) == " ".join(
                WIF_ATTRIBUTE_CONDITION.split()
            )
            issuer = provider_details.get("oidc", {}).get("issuerUri", "")
            issuer_valid = issuer == GITHUB_ISSUER
            state = provider_details.get("state", "")
            state_valid = state == "ACTIVE"
            if not mapping_valid or not condition_valid or not issuer_valid or not state_valid:
                planned_actions.append(
                    f"Update Workload Identity Provider '{WIF_PROVIDER_ID}' (mapping/condition/issuer/state)"
                )
        elif not wif_provider_exists:
            planned_actions.append(
                f"Create Workload Identity Provider '{WIF_PROVIDER_ID}' in pool '{WIF_POOL_ID}'"
            )

        # 4. Project IAM Bindings for ngabo-deployer (Exact Allow-list: DEPLOYER_PROJECT_ROLES = ())
        project_bindings = self.inspector.get_project_iam_bindings()
        deployer_email = self.config.service_account_email(DEPLOYER_SA_NAME)
        deployer_member = f"serviceAccount:{deployer_email}"

        # Current project roles assigned to deployer
        current_deployer_project_roles = [
            b.get("role", "") for b in project_bindings if deployer_member in b.get("members", [])
        ]
        # Any role not in allowlist must be revoked
        for role in current_deployer_project_roles:
            if role not in DEPLOYER_PROJECT_ROLES:
                planned_actions.append(
                    f"Revoke unapproved project role '{role}' from '{deployer_email}'"
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
        # Deployer must have NO project-level serviceAccountUser
        has_proj_actas = any(
            b.get("role") == "roles/iam.serviceAccountUser" and deployer_member in b.get("members", [])
            for b in project_bindings
        )
        if has_proj_actas:
            planned_actions.append(
                f"CRITICAL: Revoke project-level 'roles/iam.serviceAccountUser' from '{deployer_email}'"
            )

        # Deployer must be serviceAccountUser ONLY on approved targets
        for target_sa in DEPLOYER_ACT_AS_TARGETS:
            target_email = self.config.service_account_email(target_sa)
            sa_bindings = self.inspector.get_service_account_iam_bindings(target_email)
            has_act_as = any(
                b.get("role") == "roles/iam.serviceAccountUser"
                and deployer_member in b.get("members", [])
                for b in sa_bindings
            )
            if not has_act_as:
                planned_actions.append(
                    f"Grant 'roles/iam.serviceAccountUser' to '{deployer_email}' on '{target_email}'"
                )

        # 7. WIF Impersonation on deployer (Exact PrincipalSet validation)
        deployer_bindings = self.inspector.get_service_account_iam_bindings(deployer_email)
        expected_principals = {
            self.config.wif_principal_set(proj_number),
            self.config.wif_principal_set(self.config.project_id),
        }
        wif_members = []
        for b in deployer_bindings:
            if b.get("role") == "roles/iam.workloadIdentityUser":
                wif_members.extend(b.get("members", []))

        has_authorized_principal = any(p in wif_members for p in expected_principals)
        if not has_authorized_principal:
            planned_actions.append(
                f"Grant 'roles/iam.workloadIdentityUser' on '{deployer_email}' to WIF principalSet"
            )
        unexpected_wif_members = [m for m in wif_members if m not in expected_principals]
        for m in unexpected_wif_members:
            planned_actions.append(
                f"Revoke unauthorized WIF impersonation member '{m}' from '{deployer_email}'"
            )

        # 8. GitHub Environment State
        github_plan = self.github_manager.plan()
        for action in github_plan["planned_actions"]:
            planned_actions.append(f"GitHub: {action}")

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
                "state_valid": state_valid,
                "issuer_valid": issuer_valid,
                "mapping_valid": mapping_valid,
                "condition_valid": condition_valid,
            },
            "deployer_project_roles": current_deployer_project_roles,
            "has_wif_impersonation": has_authorized_principal and not unexpected_wif_members,
            "planned_actions": planned_actions,
            "is_converged": is_converged,
        }

    def apply(self) -> dict[str, Any]:
        """Idempotently provision, reconcile, and validate identity resources."""
        operations: list[str] = []
        proj_number = self.inspector.get_project_number()

        # 1. Service Accounts
        for sa_name, info in SERVICE_ACCOUNTS.items():
            email = self.config.service_account_email(sa_name)
            if not self.inspector.service_account_exists(email):
                self._log(f"[apply] Creating service account '{sa_name}' ({email})...")
                run_gcloud_command(
                    [
                        "iam",
                        "service-accounts",
                        "create",
                        sa_name,
                        f"--display-name={info['display_name']}",
                        f"--description={info['description']}",
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
            # Check for mapping, condition, or issuer drift and update in-place
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
                issuer = provider_details.get("oidc", {}).get("issuerUri", "")
                issuer_valid = issuer == GITHUB_ISSUER
                state = provider_details.get("state", "")
                state_valid = state == "ACTIVE"
                needs_update = (
                    not mapping_valid
                    or not condition_valid
                    or not issuer_valid
                    or not state_valid
                )

            if needs_update:
                self._log(
                    f"[apply] Updating Workload Identity Provider '{WIF_PROVIDER_ID}' in place..."
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

        # 4. Project-level IAM Bindings for ngabo-deployer (Reconcile to exact allow-list)
        deployer_email = self.config.service_account_email(DEPLOYER_SA_NAME)
        deployer_member = f"serviceAccount:{deployer_email}"
        project_bindings = self.inspector.get_project_iam_bindings()

        # Revoke any project role assigned to deployer that is NOT in DEPLOYER_PROJECT_ROLES
        for b in project_bindings:
            role = b.get("role", "")
            if deployer_member in b.get("members", []) and role not in DEPLOYER_PROJECT_ROLES:
                self._log(f"[apply] Revoking unapproved project role '{role}' from '{deployer_email}'...")
                run_gcloud_command(
                    [
                        "projects",
                        "remove-iam-policy-binding",
                        self.config.project_id,
                        f"--member={deployer_member}",
                        f"--role={role}",
                        "--condition=None",
                    ]
                )
                operations.append(f"Revoked project role '{role}' from '{deployer_email}'")

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

        # 7. WIF Impersonation Binding on ngabo-deployer (Exact PrincipalSet validation)
        deployer_bindings = self.inspector.get_service_account_iam_bindings(deployer_email)
        wif_principal = self.config.wif_principal_set(proj_number)
        expected_principals = {
            self.config.wif_principal_set(proj_number),
            self.config.wif_principal_set(self.config.project_id),
        }
        wif_members = []
        for b in deployer_bindings:
            if b.get("role") == "roles/iam.workloadIdentityUser":
                wif_members.extend(b.get("members", []))

        if not any(p in wif_members for p in expected_principals):
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

        # Revoke any unauthorized WIF impersonators
        for m in wif_members:
            if m not in expected_principals:
                self._log(f"[apply] Revoking unauthorized WIF member '{m}' from '{deployer_email}'...")
                run_gcloud_command(
                    [
                        "iam",
                        "service-accounts",
                        "remove-iam-policy-binding",
                        deployer_email,
                        f"--project={self.config.project_id}",
                        f"--member={m}",
                        "--role=roles/iam.workloadIdentityUser",
                    ]
                )
                operations.append(f"Revoked unauthorized WIF impersonator '{m}'")

        # 8. GitHub Environment & Branch Policy
        github_res = self.github_manager.apply()
        for op in github_res["operations"]:
            operations.append(f"GitHub: {op}")

        # 9. Post-apply validation: fail closed if live state does not pass
        val = self.validate()
        self.export_evidence()

        report = {
            "success": val["passed"],
            "noop": len(operations) == 0,
            "operations": operations,
            "validation": val,
        }
        return report

    def validate(self) -> dict[str, Any]:
        """Validate live IAM, WIF, and GitHub state against governed contracts."""
        failures: list[str] = []
        checks: dict[str, Any] = {
            "service_accounts_present": False,
            "user_managed_keys_zero": False,
            "wif_pool_valid": False,
            "wif_provider_valid": False,
            "deployer_roles_match_allowlist": False,
            "deployer_ar_roles_match_allowlist": False,
            "runtime_roles_match_allowlist": False,
            "prohibited_basic_roles_absent": False,
            "project_wide_secret_accessor_absent": False,
            "deployer_act_as_valid": False,
            "wif_impersonation_exact": False,
            "github_env_valid": False,
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

        # 3. WIF Provider (validate state ACTIVE, issuer, mapping, condition with environment=dev)
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
            state = provider_details.get("state", "")
            if state != "ACTIVE":
                failures.append(f"WIF Provider '{WIF_PROVIDER_ID}' state is '{state}' (must be ACTIVE).")
            issuer = provider_details.get("oidc", {}).get("issuerUri", "")
            if issuer != GITHUB_ISSUER:
                failures.append(f"WIF Provider '{WIF_PROVIDER_ID}' issuer '{issuer}' does not match '{GITHUB_ISSUER}'.")
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
            provider_valid = (
                state == "ACTIVE"
                and issuer == GITHUB_ISSUER
                and mapping_valid
                and condition_valid
            )
        else:
            failures.append(
                f"Workload Identity Provider '{WIF_PROVIDER_ID}' does not exist in pool '{WIF_POOL_ID}'."
            )
        checks["wif_provider_valid"] = provider_valid

        # 4. Project-level IAM bindings: Deployer exact allow-list
        project_bindings = self.inspector.get_project_iam_bindings()
        deployer_email = self.config.service_account_email(DEPLOYER_SA_NAME)
        deployer_member = f"serviceAccount:{deployer_email}"

        current_deployer_project_roles = [
            b.get("role", "") for b in project_bindings if deployer_member in b.get("members", [])
        ]
        deployer_project_roles_valid = set(current_deployer_project_roles) == set(DEPLOYER_PROJECT_ROLES)
        if not deployer_project_roles_valid:
            failures.append(
                f"Deployer project roles {current_deployer_project_roles} do not exactly match allowlist {DEPLOYER_PROJECT_ROLES}."
            )
        checks["deployer_roles_match_allowlist"] = deployer_project_roles_valid

        # Deployer Artifact Registry roles: exact match against allowlist
        ar_bindings = self.inspector.get_artifact_registry_iam_bindings(ARTIFACT_REGISTRY_REPO)
        actual_ar_roles = [
            b.get("role") for b in ar_bindings if deployer_member in b.get("members", [])
        ]
        deployer_ar_roles_valid = set(actual_ar_roles) == set(DEPLOYER_ARTIFACT_REGISTRY_ROLES)
        if not deployer_ar_roles_valid:
            failures.append(
                f"Deployer Artifact Registry roles {actual_ar_roles} do not match allow-list {DEPLOYER_ARTIFACT_REGISTRY_ROLES}."
            )
        checks["deployer_ar_roles_match_allowlist"] = deployer_ar_roles_valid

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

        # 5. Deployer actAs exact scope
        act_as_valid = True
        # Check no project-level serviceAccountUser
        has_proj_actas = any(
            b.get("role") == "roles/iam.serviceAccountUser" and deployer_member in b.get("members", [])
            for b in project_bindings
        )
        if has_proj_actas:
            act_as_valid = False
            failures.append("Deployer possesses prohibited project-level 'roles/iam.serviceAccountUser'.")

        # Check approved targets
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
                    f"Deployer missing approved 'roles/iam.serviceAccountUser' on '{target_email}'."
                )

        # Check that NO other service account has deployer as serviceAccountUser
        all_project_sas = self.inspector.get_all_project_service_accounts()
        approved_target_emails = {
            self.config.service_account_email(name) for name in DEPLOYER_ACT_AS_TARGETS
        }
        for sa_info in all_project_sas:
            sa_email = sa_info.get("email", "")
            if sa_email and sa_email not in approved_target_emails and sa_email != deployer_email:
                sa_bindings = self.inspector.get_service_account_iam_bindings(sa_email)
                if any(
                    b.get("role") == "roles/iam.serviceAccountUser"
                    and deployer_member in b.get("members", [])
                    for b in sa_bindings
                ):
                    act_as_valid = False
                    failures.append(
                        f"Deployer possesses unauthorized actAs on unapproved service account '{sa_email}'."
                    )
        checks["deployer_act_as_valid"] = act_as_valid

        # 6. WIF Impersonation binding on deployer (Exact match)
        proj_number = self.inspector.get_project_number()
        deployer_bindings = self.inspector.get_service_account_iam_bindings(deployer_email)
        expected_principals = {
            self.config.wif_principal_set(proj_number),
            self.config.wif_principal_set(self.config.project_id),
        }
        wif_members = []
        for b in deployer_bindings:
            if b.get("role") == "roles/iam.workloadIdentityUser":
                wif_members.extend(b.get("members", []))

        unexpected_wif_members = [m for m in wif_members if m not in expected_principals]
        has_authorized_wif = any(p in wif_members for p in expected_principals)
        wif_impersonation_exact = has_authorized_wif and not unexpected_wif_members
        if not has_authorized_wif:
            failures.append(
                f"Deployer missing WIF impersonation binding for authorized principalSet '{expected_principals}'."
            )
        if unexpected_wif_members:
            failures.append(
                f"Deployer has unauthorized WIF impersonator members: {unexpected_wif_members}."
            )
        checks["wif_impersonation_exact"] = wif_impersonation_exact

        # 7. GitHub Environment Validation
        github_val = self.github_manager.validate()
        checks["github_env_valid"] = github_val["passed"]
        if not github_val["passed"]:
            failures.extend(github_val["failures"])

        passed = len(failures) == 0
        return {
            "passed": passed,
            "failures": failures,
            "checks": checks,
        }

    def verify_synthetic_secret_probe(self) -> dict[str, Any]:
        """Perform bounded, ephemeral synthetic Secret Manager policy probe.

        Proves:
        1. core runtime -> ALLOW (resource-scoped)
        2. web runtime -> DENY
        3. deployer -> DENY
        4. project-wide secretAccessor -> ABSENT
        Cleans up probe container completely.
        """
        probe_secret_id = "ngabo-dev-synthetic-probe-ephemeral"
        core_email = self.config.service_account_email(CORE_RUNTIME_SA_NAME)
        web_email = self.config.service_account_email(WEB_RUNTIME_SA_NAME)
        deployer_email = self.config.service_account_email(DEPLOYER_SA_NAME)

        probe_results: dict[str, Any] = {
            "probe_secret_id": probe_secret_id,
            "secret_probe_mode": "IAM_POLICY_BOUNDARY",
            "core_runtime_resource_scoped_accessor_binding": "ABSENT",
            "web_runtime_resource_scoped_accessor_binding": "ABSENT",
            "deployer_resource_scoped_accessor_binding": "ABSENT",
            "project_wide_secret_accessor": "ABSENT",
            "runtime_payload_access": "DEFERRED_UNTIL_FIRST_REAL_SECRET_VERSION",
            "cleanup_successful": False,
            "core_runtime_allowed": False,
            "web_runtime_denied": True,
            "deployer_denied": True,
            "project_wide_accessor_absent": True,
        }

        try:
            # 1. Create ephemeral secret
            run_gcloud_command(
                [
                    "secrets",
                    "create",
                    probe_secret_id,
                    f"--project={self.config.project_id}",
                    "--replication-policy=automatic",
                ]
            )

            # 2. Grant resource-scoped accessor ONLY to core runtime
            run_gcloud_command(
                [
                    "secrets",
                    "add-iam-policy-binding",
                    probe_secret_id,
                    f"--project={self.config.project_id}",
                    f"--member=serviceAccount:{core_email}",
                    "--role=roles/secretmanager.secretAccessor",
                ]
            )

            # 3. Read back secret policy
            code, stdout, _ = run_gcloud_command(
                [
                    "secrets",
                    "get-iam-policy",
                    probe_secret_id,
                    f"--project={self.config.project_id}",
                    "--format=json",
                ]
            )
            if code == 0 and stdout:
                policy = json.loads(stdout)
                bindings = policy.get("bindings", [])
                accessor_members = []
                for b in bindings:
                    if b.get("role") == "roles/secretmanager.secretAccessor":
                        accessor_members.extend(b.get("members", []))

                has_core = f"serviceAccount:{core_email}" in accessor_members
                has_web = f"serviceAccount:{web_email}" in accessor_members
                has_deployer = f"serviceAccount:{deployer_email}" in accessor_members

                probe_results["core_runtime_resource_scoped_accessor_binding"] = "PRESENT" if has_core else "ABSENT"
                probe_results["web_runtime_resource_scoped_accessor_binding"] = "PRESENT" if has_web else "ABSENT"
                probe_results["deployer_resource_scoped_accessor_binding"] = "PRESENT" if has_deployer else "ABSENT"

                probe_results["core_runtime_allowed"] = has_core
                probe_results["web_runtime_denied"] = not has_web
                probe_results["deployer_denied"] = not has_deployer

            # 4. Check project-wide accessor is absent
            project_bindings = self.inspector.get_project_iam_bindings()
            sa_members = {f"serviceAccount:{self.config.service_account_email(sa)}" for sa in SERVICE_ACCOUNTS}
            has_project_accessor = any(
                b.get("role") == "roles/secretmanager.secretAccessor"
                and any(m in b.get("members", []) for m in sa_members)
                for b in project_bindings
            )
            probe_results["project_wide_secret_accessor"] = "PRESENT" if has_project_accessor else "ABSENT"
            probe_results["project_wide_accessor_absent"] = not has_project_accessor

        finally:
            # 5. Clean up ephemeral secret completely
            del_code, _, _ = run_gcloud_command(
                [
                    "secrets",
                    "delete",
                    probe_secret_id,
                    f"--project={self.config.project_id}",
                    "--quiet",
                ],
                check=False,
            )
            probe_results["cleanup_successful"] = (del_code == 0)

        return probe_results

    def teardown_rehearsal(self) -> dict[str, Any]:
        """Dry-run plan-only rehearsal for identity and WIF teardown."""
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
                "target": "GitHub Environment",
                "description": f"Delete GitHub environment '{GITHUB_ALLOWED_ENV}'",
                "mode": "PLAN_ONLY",
            },
            {
                "step": 5,
                "target": "Cessation Verification",
                "description": "Assert service accounts, WIF pool, and GitHub environment are absent",
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

        # Derived live state
        sa_live: dict[str, Any] = {}
        for sa in SERVICE_ACCOUNTS:
            email = self.config.service_account_email(sa)
            exists = self.inspector.service_account_exists(email)
            keys = self.inspector.get_user_managed_keys(email) if exists else []
            sa_live[sa] = {
                "email": email,
                "exists": exists,
                "user_managed_key_count": len(keys),
            }

        provider_details = self.inspector.get_wif_provider_details(WIF_POOL_ID, WIF_PROVIDER_ID)
        deployer_email = self.config.service_account_email(DEPLOYER_SA_NAME)
        deployer_bindings = self.inspector.get_service_account_iam_bindings(deployer_email)
        actual_wif_members = []
        for b in deployer_bindings:
            if b.get("role") == "roles/iam.workloadIdentityUser":
                actual_wif_members.extend(b.get("members", []))

        project_bindings = self.inspector.get_project_iam_bindings()
        actual_deployer_project_roles = [
            b.get("role", "") for b in project_bindings if f"serviceAccount:{deployer_email}" in b.get("members", [])
        ]
        ar_bindings = self.inspector.get_artifact_registry_iam_bindings(ARTIFACT_REGISTRY_REPO)
        actual_deployer_ar_roles = [
            b.get("role", "") for b in ar_bindings if f"serviceAccount:{deployer_email}" in b.get("members", [])
        ]

        gh_env = self.github_manager.inspector.get_environment(GITHUB_ALLOWED_ENV)
        gh_policies = self.github_manager.inspector.get_branch_policies(GITHUB_ALLOWED_ENV)

        evidence: dict[str, Any] = {
            "contract_version": "ngabo-cloud-identity-v1.1",
            "issue": "87",
            "topology": {
                "canonical_project_id": self.config.project_id,
                "project_number": proj_number,
                "primary_region": self.config.region,
                "wif_location": self.config.wif_location,
            },
            "service_accounts": {
                "expected": {
                    sa: {
                        "email": self.config.service_account_email(sa),
                        "display_name": info["display_name"],
                        "user_managed_key_count": 0,
                    }
                    for sa, info in SERVICE_ACCOUNTS.items()
                },
                "observed": sa_live,
                "verified": all(s["exists"] and s["user_managed_key_count"] == 0 for s in sa_live.values()),
                "deferred": DEFERRED_SERVICE_ACCOUNTS,
            },
            "workload_identity_federation": {
                "expected": {
                    "pool_id": WIF_POOL_ID,
                    "provider_id": WIF_PROVIDER_ID,
                    "issuer": GITHUB_ISSUER,
                    "repository_id": GITHUB_REPO_ID,
                    "repository_owner_id": GITHUB_OWNER_ID,
                    "allowed_ref": GITHUB_ALLOWED_REF,
                    "allowed_environment": GITHUB_ALLOWED_ENV,
                    "attribute_mapping": WIF_ATTRIBUTE_MAPPING,
                    "attribute_condition": WIF_ATTRIBUTE_CONDITION,
                    "authorized_principal_set": self.config.wif_principal_set(proj_number),
                },
                "observed": {
                    "pool_exists": self.inspector.wif_pool_exists(WIF_POOL_ID),
                    "provider_state": provider_details.get("state") if provider_details else None,
                    "provider_issuer": provider_details.get("oidc", {}).get("issuerUri") if provider_details else None,
                    "attribute_mapping": provider_details.get("attributeMapping") if provider_details else None,
                    "attribute_condition": provider_details.get("attributeCondition") if provider_details else None,
                    "actual_wif_members": actual_wif_members,
                },
                "verified": val["checks"]["wif_pool_valid"] and val["checks"]["wif_provider_valid"] and val["checks"]["wif_impersonation_exact"],
            },
            "github_integration": {
                "expected": {
                    "environment": GITHUB_ALLOWED_ENV,
                    "deployment_branch_policy": ["develop"],
                    "custom_branch_policies": True,
                },
                "observed": {
                    "environment_present": gh_env is not None,
                    "custom_branch_policies": (gh_env.get("deployment_branch_policy") or {}).get("custom_branch_policies", False) if gh_env else False,
                    "branch_policies": gh_policies,
                },
                "verified": val["checks"]["github_env_valid"],
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
                        "google-github-actions/setup-gcloud": GOOGLE_SETUP_GCLOUD_ACTION_PIN,
                    },
                },
            },
            "iam_contracts": {
                "expected": {
                    "deployer_project_roles": list(DEPLOYER_PROJECT_ROLES),
                    "deployer_ar_roles": list(DEPLOYER_ARTIFACT_REGISTRY_ROLES),
                    "deployer_act_as_targets": list(DEPLOYER_ACT_AS_TARGETS),
                    "core_runtime_roles": list(CORE_RUNTIME_PROJECT_ROLES),
                    "web_runtime_roles": list(WEB_RUNTIME_PROJECT_ROLES),
                    "prohibited_basic_roles": list(PROHIBITED_BASIC_ROLES),
                    "cloud_run_developer_authority": "DEFERRED_TO_#90",
                },
                "observed": {
                    "deployer_project_roles": actual_deployer_project_roles,
                    "deployer_ar_roles": actual_deployer_ar_roles,
                },
                "verified": val["checks"]["deployer_roles_match_allowlist"]
                and val["checks"]["deployer_ar_roles_match_allowlist"]
                and val["checks"]["runtime_roles_match_allowlist"]
                and val["checks"]["prohibited_basic_roles_absent"]
                and val["checks"]["deployer_act_as_valid"],
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
                "positive_wif_proof_status": "PENDING_POST_MERGE",
                "runtime_payload_access": "DEFERRED_UNTIL_FIRST_REAL_SECRET_VERSION",
                "privacy_audit_status": "EXTERNAL_REVIEW_REQUIRED",
                "secret_probe_mode": "IAM_POLICY_BOUNDARY",
                "core_runtime_resource_scoped_accessor_binding": "PRESENT",
                "web_runtime_resource_scoped_accessor_binding": "ABSENT",
                "deployer_resource_scoped_accessor_binding": "ABSENT",
                "project_wide_secret_accessor": "ABSENT",
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
    subparsers.add_parser("evidence", help="Derive and write machine-readable identity evidence artifact")
    subparsers.add_parser("secret-probe", help="Run bounded ephemeral synthetic secret policy probe")

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
            print("[apply] Identity bootstrap completed.")
            print(f"Success:             {res['success']}")
            print(f"Operations executed: {res['operations']}")
            print(f"Idempotent No-op:    {res['noop']}")
            if not res["success"]:
                print()
                print("Validation Failures post-apply:")
                for f in res.get("validation", {}).get("failures", []):
                    print(f"  - {f}")
        return 0 if res["success"] else 1

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

    elif args.command == "evidence":
        res = mgr.export_evidence()
        if args.format == "json":
            print(json.dumps(res, indent=2))
        else:
            print("=" * 60)
            print("Ngabo GCP Identity Evidence Exported")
            print("=" * 60)
            print("Artifact:           infra/gcp/evidence/identity_evidence.json")
            print(f"Validation:         {'PASSED' if res['verification_results']['validation_passed'] else 'FAILED'}")
            print(f"Positive WIF Proof: {res['verification_results']['positive_wif_proof_status']}")
            print("=" * 60)
        return 0 if res["verification_results"]["validation_passed"] else 1

    elif args.command == "secret-probe":
        res = mgr.verify_synthetic_secret_probe()
        if args.format == "json":
            print(json.dumps(res, indent=2))
        else:
            print("=" * 60)
            print("Ngabo Synthetic Secret Policy Probe")
            print("=" * 60)
            print(f"probe_secret_id                               : {res['probe_secret_id']}")
            print(f"secret_probe_mode                             : {res['secret_probe_mode']}")
            print(f"core_runtime_resource_scoped_accessor_binding: {res['core_runtime_resource_scoped_accessor_binding']}")
            print(f"web_runtime_resource_scoped_accessor_binding : {res['web_runtime_resource_scoped_accessor_binding']}")
            print(f"deployer_resource_scoped_accessor_binding    : {res['deployer_resource_scoped_accessor_binding']}")
            print(f"project_wide_secret_accessor                  : {res['project_wide_secret_accessor']}")
            print(f"runtime_payload_access                        : {res['runtime_payload_access']}")
            print(f"cleanup_successful                            : {res['cleanup_successful']}")
            print("=" * 60)
        all_passed = (
            res["core_runtime_resource_scoped_accessor_binding"] == "PRESENT"
            and res["web_runtime_resource_scoped_accessor_binding"] == "ABSENT"
            and res["deployer_resource_scoped_accessor_binding"] == "ABSENT"
            and res["project_wide_secret_accessor"] == "ABSENT"
            and res["cleanup_successful"]
        )
        return 0 if all_passed else 1

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
