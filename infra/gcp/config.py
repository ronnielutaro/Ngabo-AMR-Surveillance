"""Configuration and constants for Ngabo Google Cloud foundation bootstrap (Issue #86).

Governs API allow-lists, canonical regions, labels, resource classification,
and cost caps in alignment with docs/CLOUD_COST_AND_TEARDOWN_POLICY.md.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ResourceClassification(StrEnum):
    """Lifecycle classification for foundation resources."""

    CREATE_NOW = "CREATE_NOW"
    ENABLE_API_ONLY = "ENABLE_API_ONLY"
    DEFINE_ONLY = "DEFINE_ONLY"
    DEFER = "DEFER"


# ---------------------------------------------------------------------------
# Core Project & Location Constants
# ---------------------------------------------------------------------------

DEFAULT_PROJECT_ID = "ngabo-amr-2026"
DEFAULT_PROJECT_NAME = "Ngabo AMR Surveillance"

# Primary Region Selection:
# us-central1 was selected for broad required-service availability, Cloud Run reference
# pricing/free-tier economics, Artifact Registry/compute co-location, and compatibility
# with the current regional foundation. Future Gemini/Vertex endpoint placement remains
# owned by #49. Co-locating eligible regional resources reduces avoidable inter-region transfer.
PRIMARY_REGION = "us-central1"

# Firestore location: us-central1 regional location co-located with compute/storage,
# avoiding multi-region replication latency and unnecessary cost. Database creation is deferred.
FIRESTORE_LOCATION = "us-central1"

ENVIRONMENTS = ("dev", "judge", "shared")

# ---------------------------------------------------------------------------
# Resource Labels
# ---------------------------------------------------------------------------

APP_LABEL = "ngabo"
MANAGED_BY_LABEL = "ngabo-bootstrap"
LIFECYCLE_LABEL = "hackathon"
ENVIRONMENT_LABEL = "shared"
OWNER_LABEL = "ngabo-maintainer"

STANDARD_LABELS: dict[str, str] = {
    "app": APP_LABEL,
    "managed-by": MANAGED_BY_LABEL,
    "lifecycle": LIFECYCLE_LABEL,
    "environment": ENVIRONMENT_LABEL,
    "owner": OWNER_LABEL,
}

# Issue #90: canonical Cloud Run label set for the dev skeleton. This is the
# single source of truth for BOTH the trusted deployment path and the
# desired-state validator. The skeleton runs in the `dev` environment, so
# environment=dev here (distinct from the shared STANDARD_LABELS value used
# by other foundation resources). managed-by=ngabo-bootstrap is truthful:
# Terraform does not manage these services.
CLOUD_RUN_LABELS: dict[str, str] = {
    "app": APP_LABEL,
    "managed-by": MANAGED_BY_LABEL,
    "lifecycle": LIFECYCLE_LABEL,
    "environment": "dev",
    "owner": OWNER_LABEL,
}

# ---------------------------------------------------------------------------
# API Allow-list (14 Justified APIs)
# ---------------------------------------------------------------------------

REQUIRED_APIS: tuple[str, ...] = (
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "billingbudgets.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
)

# ---------------------------------------------------------------------------
# Resource Specifications
# ---------------------------------------------------------------------------

ARTIFACT_REGISTRY_REPO = "ngabo-artifacts"
ARTIFACT_REGISTRY_FORMAT = "docker"
ARTIFACT_REGISTRY_DESCRIPTION = "Ngabo container image repository for core and web services"

# Free Trial Budget Alert Contract
# Note: Google Cloud Billing Budgets API explicitly disallows forecasted-spend thresholds
# when a customPeriod (start-date and end-date) is configured. Therefore, all threshold rules
# use current-spend basis across the 90-day Free Trial window.
BUDGET_DISPLAY_NAME = "ngabo-free-trial-budget"
BUDGET_AMOUNT_USD = 300.0
BUDGET_START_DATE = "2026-08-29"
BUDGET_END_DATE = "2026-11-28"
BUDGET_CREDIT_TREATMENT = "exclude-all-credits"  # API value: "EXCLUDE_ALL_CREDITS"
BUDGET_THRESHOLDS: tuple[dict[str, Any], ...] = (
    {"percent": 0.5, "basis": "current-spend"},
    {"percent": 0.9, "basis": "current-spend"},
    {"percent": 0.9667, "basis": "current-spend"},  # ~$290 / $300: alerts on $10 teardown margin
    {"percent": 1.0, "basis": "current-spend"},
)

# Governed Cloud Run caps contract for future issues (#90+)
CLOUD_RUN_CAPS_CONTRACT: dict[str, object] = {
    "min_instances": 0,
    "max_instances": 2,
    "timeout_seconds": 60,
    "cpu": "1",
    "memory": "512Mi",
    "concurrency": 80,
    "scale_to_zero_required": True,
}

# Storage lifecycle contract for ephemeral artifacts
GCS_LIFECYCLE_CONTRACT: dict[str, object] = {
    "lifecycle_rule": "Delete objects older than 7 days",
    "storage_class": "STANDARD",
    "public_access_prevention": "enforced",
}

# ---------------------------------------------------------------------------
# Resource Ownership Matrix
# ---------------------------------------------------------------------------

RESOURCE_CLASSIFICATION_MATRIX: dict[str, tuple[ResourceClassification, str]] = {
    "gcp_project": (
        ResourceClassification.CREATE_NOW,
        "Issue #86 owns the canonical GCP project boundary.",
    ),
    "billing_link": (
        ResourceClassification.CREATE_NOW,
        "Issue #86 links the canonical project to the maintainer's Free Trial billing account.",
    ),
    "api_enablement": (
        ResourceClassification.CREATE_NOW,
        "Issue #86 enables the 14 allow-listed APIs.",
    ),
    "artifact_registry": (
        ResourceClassification.CREATE_NOW,
        "Issue #86 creates the empty docker repository foundation for #89.",
    ),
    "billing_budget_alerts": (
        ResourceClassification.CREATE_NOW,
        "Issue #86 provisions budget monitoring alerts ($150, $270, $300 thresholds).",
    ),
    "cloud_run_api": (
        ResourceClassification.ENABLE_API_ONLY,
        "Issue #86 enables run.googleapis.com; application service deployment belongs to #90.",
    ),
    "secret_manager_api": (
        ResourceClassification.ENABLE_API_ONLY,
        "Issue #86 enables secretmanager.googleapis.com; secret contracts belong to #87.",
    ),
    "cloud_build_api": (
        ResourceClassification.ENABLE_API_ONLY,
        "Issue #86 enables cloudbuild.googleapis.com; container build workflows belong to #88/#89.",
    ),
    "firestore_api": (
        ResourceClassification.ENABLE_API_ONLY,
        "Issue #86 enables firestore.googleapis.com; database rules belong to persistence issue.",
    ),
    "pubsub_api": (
        ResourceClassification.ENABLE_API_ONLY,
        "Issue #86 enables pubsub.googleapis.com; event topic contracts belong to messaging issue.",
    ),
    "storage_api": (
        ResourceClassification.ENABLE_API_ONLY,
        "Issue #86 enables storage.googleapis.com; application buckets are deferred.",
    ),
    "iam_and_wif": (
        ResourceClassification.DEFER,
        "Workload Identity Federation and service accounts strictly belong to #87.",
    ),
    "container_images": (
        ResourceClassification.DEFER,
        "Building and publishing immutable images strictly belongs to #89.",
    ),
    "cloud_run_services": (
        ResourceClassification.DEFER,
        "Deploying ngabo-core and ngabo-web Cloud Run services strictly belongs to #90.",
    ),
}


@dataclass(frozen=True)
class GcpBootstrapConfig:
    """Runtime configuration for bootstrap operations."""

    project_id: str = DEFAULT_PROJECT_ID
    project_name: str = DEFAULT_PROJECT_NAME
    region: str = PRIMARY_REGION
    billing_account: str | None = None
    labels: Mapping[str, str] = field(default_factory=lambda: dict(STANDARD_LABELS))
    dry_run: bool = False

    @classmethod
    def from_env(
        cls,
        project_id: str | None = None,
        billing_account: str | None = None,
        region: str | None = None,
        dry_run: bool = False,
    ) -> GcpBootstrapConfig:
        """Resolve configuration from parameters or environment variables."""
        resolved_project_id = project_id or os.environ.get(
            "NGABO_GCP_PROJECT_ID", DEFAULT_PROJECT_ID
        )
        resolved_billing_account = billing_account or os.environ.get("NGABO_GCP_BILLING_ACCOUNT")
        resolved_region = region or os.environ.get("NGABO_GCP_REGION", PRIMARY_REGION)

        return cls(
            project_id=resolved_project_id.strip(),
            region=resolved_region.strip(),
            billing_account=(
                resolved_billing_account.strip() if resolved_billing_account else None
            ),
            dry_run=dry_run,
        )

    def validate(self) -> list[str]:
        """Validate configuration rules without network access."""
        errors: list[str] = []
        if not self.project_id:
            errors.append("project_id must not be empty.")
        elif (
            len(self.project_id) < 6
            or len(self.project_id) > 30
            or not self.project_id[0].isalpha()
            or not self.project_id.islower()
            or self.project_id.endswith("-")
        ):
            errors.append(
                f"Invalid project_id '{self.project_id}': Must be 6-30 lowercase characters, "
                "start with a letter, and not end with a hyphen."
            )

        if not self.region:
            errors.append("region must not be empty.")
        elif self.region != PRIMARY_REGION:
            errors.append(
                f"Unsupported region '{self.region}': Must match primary region '{PRIMARY_REGION}'."
            )

        return errors
