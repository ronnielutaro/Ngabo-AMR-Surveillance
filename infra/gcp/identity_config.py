"""Configuration and constants for Ngabo keyless IAM, service accounts, and secret boundaries (Issue #87).

Governs service accounts, Workload Identity Federation (WIF) with GitHub Actions,
least-privilege IAM allow-lists, and Secret Manager access contracts in alignment
with docs/CLOUD_COST_AND_TEARDOWN_POLICY.md.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Core Project & Location Constants
# ---------------------------------------------------------------------------

DEFAULT_PROJECT_ID = "ngabo-amr-2026"
DEFAULT_PRIMARY_REGION = "us-central1"
DEFAULT_WIF_LOCATION = "global"
WIF_LOCATION = DEFAULT_WIF_LOCATION

# ---------------------------------------------------------------------------
# GitHub Repository Identity Claims (Public Immutable Numeric IDs)
# ---------------------------------------------------------------------------

GITHUB_REPO_ID = "1333677446"
GITHUB_OWNER_ID = "29591720"
GITHUB_REPO_NAME = "ronnielutaro/Ngabo-AMR-Surveillance"
GITHUB_ALLOWED_REF = "refs/heads/develop"
GITHUB_ALLOWED_ENV = "dev"
GITHUB_ISSUER = "https://token.actions.githubusercontent.com"

# Pinned GitHub Actions Commit SHAs
ACTIONS_CHECKOUT_PIN = {
    "version": "v4.2.2",
    "commit_sha": "11bd71901bbe5b1630ceea73d27597364c9af683",
}
GOOGLE_AUTH_ACTION_PIN = {
    "version": "v2.1.8",
    "commit_sha": "71f986410dfbc7added4569d411d040a91dc6935",
}

# ---------------------------------------------------------------------------
# Workload Identity Federation (WIF) Specification
# ---------------------------------------------------------------------------

WIF_POOL_ID = "ngabo-github"
WIF_POOL_DISPLAY_NAME = "Ngabo GitHub Actions Pool"
WIF_POOL_DESCRIPTION = "Workload Identity Pool for ronnielutaro/Ngabo-AMR-Surveillance GitHub Actions"

WIF_PROVIDER_ID = "ngabo-repo"
WIF_PROVIDER_DISPLAY_NAME = "Ngabo GitHub Repository Provider"
WIF_PROVIDER_DESCRIPTION = "OIDC Provider for GitHub Actions with repository and ref constraints"

WIF_ATTRIBUTE_MAPPING: dict[str, str] = {
    "google.subject": "assertion.sub",
    "attribute.repository_id": "assertion.repository_id",
    "attribute.repository_owner_id": "assertion.repository_owner_id",
    "attribute.ref": "assertion.ref",
    "attribute.environment": "assertion.environment",
    "attribute.workflow_ref": "assertion.workflow_ref",
}

WIF_ATTRIBUTE_CONDITION = (
    f'assertion.repository_id == "{GITHUB_REPO_ID}" && '
    f'assertion.repository_owner_id == "{GITHUB_OWNER_ID}" && '
    f'assertion.ref == "{GITHUB_ALLOWED_REF}"'
)

# ---------------------------------------------------------------------------
# Service Account Definitions
# ---------------------------------------------------------------------------

DEPLOYER_SA_NAME = "ngabo-deployer"
CORE_RUNTIME_SA_NAME = "ngabo-core-runtime"
WEB_RUNTIME_SA_NAME = "ngabo-web-runtime"

SERVICE_ACCOUNTS: dict[str, dict[str, str]] = {
    DEPLOYER_SA_NAME: {
        "display_name": "Ngabo CI/CD Deployment Identity",
        "description": "Dedicated deployment identity for automated GitHub Actions delivery to Cloud Run.",
    },
    CORE_RUNTIME_SA_NAME: {
        "display_name": "Ngabo Core Backend Runtime Identity",
        "description": "Dedicated least-privilege runtime service identity for ngabo-core Cloud Run service.",
    },
    WEB_RUNTIME_SA_NAME: {
        "display_name": "Ngabo Web Frontend Runtime Identity",
        "description": "Dedicated least-privilege runtime service identity for ngabo-web Cloud Run service.",
    },
}

# Conceptual service accounts deliberately deferred until owning components exist
DEFERRED_SERVICE_ACCOUNTS: dict[str, str] = {
    "event-publisher": (
        "Deferred until the signal-event publishing architecture is implemented "
        "and a distinct runtime boundary is justified."
    ),
    "acknowledger": (
        "Deferred until external-action / machine-ack architecture is implemented "
        "and a separately assumable identity is justified."
    ),
}

# ---------------------------------------------------------------------------
# IAM Allow-list and Scope Contracts
# ---------------------------------------------------------------------------

# Roles permitted for ngabo-deployer
DEPLOYER_PROJECT_ROLES: tuple[str, ...] = ("roles/run.developer",)
DEPLOYER_ARTIFACT_REGISTRY_ROLES: tuple[str, ...] = ("roles/artifactregistry.reader",)
DEPLOYER_ACT_AS_TARGETS: tuple[str, ...] = (CORE_RUNTIME_SA_NAME, WEB_RUNTIME_SA_NAME)

# Runtime service accounts begin with zero speculative project-level roles
CORE_RUNTIME_PROJECT_ROLES: tuple[str, ...] = ()
WEB_RUNTIME_PROJECT_ROLES: tuple[str, ...] = ()

# Prohibited basic / broad roles that must never be assigned to service accounts
PROHIBITED_BASIC_ROLES: tuple[str, ...] = (
    "roles/owner",
    "roles/editor",
    "roles/viewer",
    "roles/iam.securityAdmin",
    "roles/iam.serviceAccountAdmin",
    "roles/secretmanager.admin",
)

# ---------------------------------------------------------------------------
# Secret Manager Contract Specification
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SecretContract:
    """Governance contract for a Secret Manager secret resource."""

    name_pattern: str
    environment: str
    owner_workload: str
    authorized_readers: tuple[str, ...]
    rotation_trigger: str
    missing_secret_behavior: str
    invalid_version_behavior: str
    teardown_behavior: str


SECRET_CONTRACTS: tuple[SecretContract, ...] = (
    SecretContract(
        name_pattern="ngabo-dev-*",
        environment="dev",
        owner_workload="ngabo-core",
        authorized_readers=(CORE_RUNTIME_SA_NAME,),
        rotation_trigger="Manual via maintainer / 90-day cadence",
        missing_secret_behavior="Startup fails fast with explicit missing-secret error; no fallback",
        invalid_version_behavior="Startup fails fast with explicit invalid-version error; no fallback",
        teardown_behavior="Destroy secret versions and delete secret container upon environment teardown",
    ),
    SecretContract(
        name_pattern="ngabo-judge-*",
        environment="judge",
        owner_workload="ngabo-core",
        authorized_readers=(CORE_RUNTIME_SA_NAME,),
        rotation_trigger="Manual via maintainer / release-freeze cadence",
        missing_secret_behavior="Startup fails fast with explicit missing-secret error; no fallback",
        invalid_version_behavior="Startup fails fast with explicit invalid-version error; no fallback",
        teardown_behavior="Destroy secret versions and delete secret container upon environment teardown",
    ),
)


@dataclass
class GcpIdentityConfig:
    """Runtime configuration for Ngabo IAM and Identity operations."""

    project_id: str = DEFAULT_PROJECT_ID
    project_number: str | None = None
    region: str = DEFAULT_PRIMARY_REGION
    wif_location: str = DEFAULT_WIF_LOCATION
    billing_account: str | None = None

    @classmethod
    def from_env(cls) -> GcpIdentityConfig:
        """Construct configuration from environment variables."""
        return cls(
            project_id=os.environ.get("NGABO_GCP_PROJECT", DEFAULT_PROJECT_ID),
            project_number=os.environ.get("NGABO_GCP_PROJECT_NUMBER"),
            region=os.environ.get("NGABO_GCP_REGION", DEFAULT_PRIMARY_REGION),
            wif_location=os.environ.get("NGABO_GCP_WIF_LOCATION", DEFAULT_WIF_LOCATION),
            billing_account=os.environ.get("NGABO_GCP_BILLING_ACCOUNT"),
        )

    def service_account_email(self, sa_name: str) -> str:
        """Compute the full service account email address."""
        return f"{sa_name}@{self.project_id}.iam.gserviceaccount.com"

    def wif_pool_name(self, project_number: str | None = None) -> str:
        """Compute the canonical WIF pool resource name."""
        proj = project_number or self.project_number or self.project_id
        return f"projects/{proj}/locations/{self.wif_location}/workloadIdentityPools/{WIF_POOL_ID}"

    def wif_provider_name(self, project_number: str | None = None) -> str:
        """Compute the canonical WIF provider resource name."""
        return f"{self.wif_pool_name(project_number)}/providers/{WIF_PROVIDER_ID}"

    def wif_principal_set(self, project_number: str | None = None) -> str:
        """Compute the principalSet for repository-bound impersonation."""
        proj = project_number or self.project_number or self.project_id
        return (
            f"principalSet://iam.googleapis.com/projects/{proj}/locations/"
            f"{self.wif_location}/workloadIdentityPools/{WIF_POOL_ID}/attribute.repository_id/{GITHUB_REPO_ID}"
        )
