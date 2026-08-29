"""Unit tests for Ngabo GCP Foundation bootstrap tool (Issue #86)."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from infra.gcp.bootstrap import (
    GcpBootstrapper,
    main,
    redact_sensitive,
)
from infra.gcp.config import (
    BUDGET_DISPLAY_NAME,
    PRIMARY_REGION,
    REQUIRED_APIS,
    STANDARD_LABELS,
    GcpBootstrapConfig,
)

SAMPLE_BILLING_ID = "012345-6789AB-CDEF01"


def test_config_validation_success() -> None:
    """Test valid configuration passes validation."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    errors = cfg.validate()
    assert errors == []


def test_config_validation_invalid_project_id() -> None:
    """Test rejection of malformed project IDs."""
    invalid_configs = [
        GcpBootstrapConfig(project_id="ng", region=PRIMARY_REGION),
        GcpBootstrapConfig(project_id="123-ngabo", region=PRIMARY_REGION),
        GcpBootstrapConfig(project_id="ngabo-amr-", region=PRIMARY_REGION),
        GcpBootstrapConfig(project_id="Ngabo-AMR", region=PRIMARY_REGION),
    ]
    for cfg in invalid_configs:
        assert len(cfg.validate()) > 0


def test_config_validation_invalid_region() -> None:
    """Test rejection of non-governed regions."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region="europe-west1")
    errors = cfg.validate()
    assert any("Unsupported region" in e for e in errors)


def test_redact_sensitive() -> None:
    """Verify that billing account IDs are masked."""
    sample = f"Account billingAccounts/{SAMPLE_BILLING_ID} linked to {SAMPLE_BILLING_ID}"
    redacted = redact_sensitive(sample)
    assert SAMPLE_BILLING_ID not in redacted
    assert "billingAccounts/[REDACTED_BILLING_ID]" in redacted
    assert "[REDACTED_BILLING_ID]" in redacted


def test_plan_reports_missing_resources() -> None:
    """Test that plan detects missing project, billing, APIs, and registry."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    with (
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "project_exists", return_value=False),
        patch.object(bootstrapper.inspector, "is_billing_linked", return_value=False),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set()),
        patch.object(bootstrapper.inspector, "artifact_registry_exists", return_value=False),
        patch.object(bootstrapper.inspector, "get_budget", return_value=None),
    ):
        plan = bootstrapper.plan()
        assert plan["status"] == "VALID"
        assert not plan["project_exists"]
        assert not plan["billing_linked"]
        assert len(plan["missing_apis"]) == len(REQUIRED_APIS)
        assert not plan["artifact_registry_exists"]
        assert not plan["budget_alert_exists"]
        assert len(plan["planned_actions"]) == 5
        assert not plan["is_converged"]


def test_plan_reports_converged_when_all_exist() -> None:
    """Test that plan indicates converged (no-op) when all resources exist."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    with (
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(bootstrapper.inspector, "is_billing_linked", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)
        ),
        patch.object(bootstrapper.inspector, "artifact_registry_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_budget", return_value={"displayName": BUDGET_DISPLAY_NAME}
        ),
    ):
        plan = bootstrapper.plan()
        assert plan["is_converged"]
        assert plan["planned_actions"] == []


def test_validate_passes_when_all_checks_succeed() -> None:
    """Test validation succeeds on fully provisioned foundation."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": STANDARD_LABELS}
        ),
        patch.object(bootstrapper.inspector, "is_billing_linked", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)
        ),
        patch.object(bootstrapper.inspector, "artifact_registry_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(
            bootstrapper.inspector, "get_budget", return_value={"displayName": BUDGET_DISPLAY_NAME}
        ),
    ):
        res = bootstrapper.validate()
        assert res["passed"]
        assert res["failures"] == []


def test_validate_fails_when_api_or_budget_missing() -> None:
    """Test validation fails if required APIs or budget alert are missing."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": STANDARD_LABELS}
        ),
        patch.object(bootstrapper.inspector, "is_billing_linked", return_value=True),
        patch.object(
            bootstrapper.inspector,
            "get_enabled_apis",
            return_value={"cloudresourcemanager.googleapis.com"},
        ),
        patch.object(bootstrapper.inspector, "artifact_registry_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=None),
    ):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("Missing required APIs" in f for f in res["failures"])
        assert any("budget alert" in f for f in res["failures"])


def test_validate_fails_when_project_missing() -> None:
    """Test validation fails if project does not exist."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)
    with patch.object(bootstrapper.inspector, "project_exists", return_value=False):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("does not exist" in f for f in res["failures"])


def test_validate_fails_when_labels_wrong() -> None:
    """Test validation fails if project labels are incorrect."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)
    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": {"env": "wrong"}}
        ),
        patch.object(bootstrapper.inspector, "is_billing_linked", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)
        ),
        patch.object(bootstrapper.inspector, "artifact_registry_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(
            bootstrapper.inspector, "get_budget", return_value={"displayName": BUDGET_DISPLAY_NAME}
        ),
    ):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("labels invalid" in f for f in res["failures"])


def test_validate_fails_when_billing_unlinked() -> None:
    """Test validation fails if billing is not linked."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)
    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": STANDARD_LABELS}
        ),
        patch.object(bootstrapper.inspector, "is_billing_linked", return_value=False),
        patch.object(
            bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)
        ),
        patch.object(bootstrapper.inspector, "artifact_registry_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(
            bootstrapper.inspector, "get_budget", return_value={"displayName": BUDGET_DISPLAY_NAME}
        ),
    ):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("active billing linked" in f for f in res["failures"])


def test_teardown_rehearsal() -> None:
    """Test teardown rehearsal structure and verification steps."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    with (
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(
            bootstrapper.inspector, "get_budget", return_value={"name": "budget-123"}
        ),
    ):
        rehearsal = bootstrapper.teardown_rehearsal()
        assert rehearsal["rehearsal_only"]
        assert len(rehearsal["teardown_plan"]) == 4
        assert len(rehearsal["cessation_verification_steps"]) == 3
        # Ensure billing ID was not leaked in commands
        assert SAMPLE_BILLING_ID not in str(rehearsal)


def test_cli_plan_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI plan invocation with json format."""
    with (
        patch(
            "infra.gcp.bootstrap.GcpInspector.discover_billing_account",
            return_value=SAMPLE_BILLING_ID,
        ),
        patch("infra.gcp.bootstrap.GcpInspector.project_exists", return_value=False),
    ):
        exit_code = main(["plan", "--project-id=ngabo-amr-2026", "--format=json"])
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["project_id"] == "ngabo-amr-2026"
        assert SAMPLE_BILLING_ID not in captured.out
