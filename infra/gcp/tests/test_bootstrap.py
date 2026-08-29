"""Unit tests for Ngabo GCP Foundation bootstrap tool (Issue #86)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
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
ALT_BILLING_ID = "999999-888888-777777"

VALID_SAMPLE_AR_DETAILS: dict[str, Any] = {
    "name": f"projects/ngabo-amr-2026/locations/{PRIMARY_REGION}/repositories/ngabo-artifacts",
    "format": "DOCKER",
    "labels": dict(STANDARD_LABELS),
}

VALID_SAMPLE_BUDGET: dict[str, Any] = {
    "name": f"billingAccounts/{SAMPLE_BILLING_ID}/budgets/budget-123",
    "displayName": BUDGET_DISPLAY_NAME,
    "amount": {
        "specifiedAmount": {
            "currencyCode": "USD",
            "units": "300",
        }
    },
    "budgetFilter": {
        "creditTypesTreatment": "EXCLUDE_ALL_CREDITS",
        "customPeriod": {
            "startDate": {"year": 2026, "month": 8, "day": 29},
            "endDate": {"year": 2026, "month": 11, "day": 28},
        },
        "projects": ["projects/ngabo-amr-2026"],
    },
    "thresholdRules": [
        {"thresholdPercent": 0.5, "spendBasis": "CURRENT_SPEND"},
        {"thresholdPercent": 0.9, "spendBasis": "CURRENT_SPEND"},
        {"thresholdPercent": 0.9667, "spendBasis": "CURRENT_SPEND"},
        {"thresholdPercent": 1.0, "spendBasis": "CURRENT_SPEND"},
    ],
}


@pytest.fixture(autouse=True)
def guard_offline_unit_test(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard ensuring unit tests never invoke real gcloud or make network calls."""

    def _fail_unmocked(cmd: list[str]) -> tuple[int, str, str]:
        raise AssertionError(f"Accidental unmocked gcloud call in unit test: {cmd}")

    monkeypatch.setattr("infra.gcp.bootstrap.run_gcloud_command", _fail_unmocked)


def test_guard_catches_unmocked_gcloud() -> None:
    """Prove that unmocked run_gcloud_command calls fail loudly in unit tests."""
    from infra.gcp.bootstrap import run_gcloud_command

    with pytest.raises(AssertionError, match="Accidental unmocked gcloud call in unit test"):
        run_gcloud_command(["projects", "list"])


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


def test_billing_discovery_multiple_accounts_fails_closed() -> None:
    """Test that multiple open billing accounts require explicit disambiguation."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    multiple_accounts = json.dumps(
        [
            {"name": f"billingAccounts/{SAMPLE_BILLING_ID}", "open": True},
            {"name": f"billingAccounts/{ALT_BILLING_ID}", "open": True},
        ]
    )
    with patch(
        "infra.gcp.bootstrap.run_gcloud_command",
        return_value=(0, multiple_accounts, ""),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            bootstrapper.inspector.discover_billing_account()
        assert "Disambiguation required" in str(exc_info.value)


def test_plan_reports_missing_resources() -> None:
    """Test that plan detects missing project, billing, APIs, and registry."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    with (
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "project_exists", return_value=False),
        patch.object(bootstrapper.inspector, "get_linked_billing_account", return_value=None),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set()),
        patch.object(bootstrapper.inspector, "get_artifact_registry_details", return_value=None),
        patch.object(bootstrapper.inspector, "get_budget", return_value=None),
    ):
        plan = bootstrapper.plan()
        assert plan["status"] == "VALID"
        assert not plan["project_exists"]
        assert not plan["billing_linked"]
        assert len(plan["missing_apis"]) == len(REQUIRED_APIS)
        assert not plan["artifact_registry_valid"]
        assert not plan["budget_alert_valid"]
        assert len(plan["planned_actions"]) >= 5
        assert not plan["is_converged"]


def test_plan_reports_converged_when_all_exist() -> None:
    """Test that plan indicates converged (no-op) when all resources match contract."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    with (
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": STANDARD_LABELS}
        ),
        patch.object(
            bootstrapper.inspector, "get_linked_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)),
        patch.object(
            bootstrapper.inspector,
            "get_artifact_registry_details",
            return_value=VALID_SAMPLE_AR_DETAILS,
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=VALID_SAMPLE_BUDGET),
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
        patch.object(
            bootstrapper.inspector, "get_linked_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)),
        patch.object(
            bootstrapper.inspector,
            "get_artifact_registry_details",
            return_value=VALID_SAMPLE_AR_DETAILS,
        ),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=VALID_SAMPLE_BUDGET),
    ):
        res = bootstrapper.validate()
        assert res["passed"]
        assert res["failures"] == []


def test_validate_fails_when_billing_linked_to_wrong_account() -> None:
    """Test validation fails when project is linked to wrong billing account."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": STANDARD_LABELS}
        ),
        patch.object(
            bootstrapper.inspector, "get_linked_billing_account", return_value=ALT_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)),
        patch.object(
            bootstrapper.inspector,
            "get_artifact_registry_details",
            return_value=VALID_SAMPLE_AR_DETAILS,
        ),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=VALID_SAMPLE_BUDGET),
    ):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("unexpected billing account" in f for f in res["failures"])


def test_validate_fails_when_artifact_registry_labels_wrong() -> None:
    """Test validation fails when Artifact Registry repository has incorrect labels."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    wrong_ar = dict(VALID_SAMPLE_AR_DETAILS)
    wrong_ar["labels"] = {"app": "wrong"}

    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": STANDARD_LABELS}
        ),
        patch.object(
            bootstrapper.inspector, "get_linked_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)),
        patch.object(
            bootstrapper.inspector, "get_artifact_registry_details", return_value=wrong_ar
        ),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=VALID_SAMPLE_BUDGET),
    ):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("Artifact Registry error: Label" in f for f in res["failures"])


def test_validate_fails_when_artifact_registry_format_wrong() -> None:
    """Test validation fails when Artifact Registry repository format is not DOCKER."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    wrong_ar = dict(VALID_SAMPLE_AR_DETAILS)
    wrong_ar["format"] = "MAVEN"

    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": STANDARD_LABELS}
        ),
        patch.object(
            bootstrapper.inspector, "get_linked_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)),
        patch.object(
            bootstrapper.inspector, "get_artifact_registry_details", return_value=wrong_ar
        ),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=VALID_SAMPLE_BUDGET),
    ):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("Format mismatch" in f for f in res["failures"])


def test_validate_fails_when_budget_credit_treatment_wrong() -> None:
    """Test validation fails if budget includes promotional credits in spend calculation."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    wrong_budget = json.loads(json.dumps(VALID_SAMPLE_BUDGET))
    wrong_budget["budgetFilter"]["creditTypesTreatment"] = "INCLUDE_ALL_CREDITS"

    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": STANDARD_LABELS}
        ),
        patch.object(
            bootstrapper.inspector, "get_linked_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)),
        patch.object(
            bootstrapper.inspector,
            "get_artifact_registry_details",
            return_value=VALID_SAMPLE_AR_DETAILS,
        ),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=wrong_budget),
    ):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("Credit treatment mismatch" in f for f in res["failures"])


def test_validate_fails_when_budget_custom_period_wrong() -> None:
    """Test validation fails if budget uses recurring period instead of Free Trial window."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    wrong_budget = json.loads(json.dumps(VALID_SAMPLE_BUDGET))
    del wrong_budget["budgetFilter"]["customPeriod"]
    wrong_budget["budgetFilter"]["calendarPeriod"] = "MONTH"

    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": STANDARD_LABELS}
        ),
        patch.object(
            bootstrapper.inspector, "get_linked_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)),
        patch.object(
            bootstrapper.inspector,
            "get_artifact_registry_details",
            return_value=VALID_SAMPLE_AR_DETAILS,
        ),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=wrong_budget),
    ):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("Budget period mismatch" in f for f in res["failures"])


def test_validate_fails_when_budget_thresholds_wrong() -> None:
    """Test validation fails if budget thresholds do not include the 96.67% early warning."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    wrong_budget = json.loads(json.dumps(VALID_SAMPLE_BUDGET))
    wrong_budget["thresholdRules"] = [
        {"thresholdPercent": 0.5, "spendBasis": "CURRENT_SPEND"},
        {"thresholdPercent": 1.0, "spendBasis": "CURRENT_SPEND"},
    ]

    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": STANDARD_LABELS}
        ),
        patch.object(
            bootstrapper.inspector, "get_linked_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)),
        patch.object(
            bootstrapper.inspector,
            "get_artifact_registry_details",
            return_value=VALID_SAMPLE_AR_DETAILS,
        ),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=wrong_budget),
    ):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("Threshold rules mismatch" in f for f in res["failures"])


def test_validate_fails_when_project_missing() -> None:
    """Test validation fails if project does not exist."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)
    with patch.object(bootstrapper.inspector, "project_exists", return_value=False):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("does not exist" in f for f in res["failures"])


def test_validate_fails_when_project_labels_wrong() -> None:
    """Test validation fails if project labels are incorrect."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)
    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "get_project_details", return_value={"labels": {"env": "wrong"}}
        ),
        patch.object(
            bootstrapper.inspector, "get_linked_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)),
        patch.object(
            bootstrapper.inspector,
            "get_artifact_registry_details",
            return_value=VALID_SAMPLE_AR_DETAILS,
        ),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=VALID_SAMPLE_BUDGET),
    ):
        res = bootstrapper.validate()
        assert not res["passed"]
        assert any("Project labels invalid" in f for f in res["failures"])


def test_teardown_rehearsal_semantics() -> None:
    """Test teardown rehearsal structure and truthful non-destructive semantics."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    with (
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value={"name": "budget-123"}),
    ):
        rehearsal = bootstrapper.teardown_rehearsal()
        assert rehearsal["teardown_rehearsal_passed"] is True
        assert rehearsal["teardown_mode"] == "PLAN_ONLY"
        assert rehearsal["destructive_actions_executed"] is False
        assert rehearsal["cessation_verification_executed"] is False
        assert rehearsal["cessation_verification_required_on_real_teardown"] is True
        assert len(rehearsal["teardown_plan"]) == 4
        assert len(rehearsal["cessation_verification_steps"]) == 3
        assert SAMPLE_BILLING_ID not in str(rehearsal)


def test_cli_plan_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI plan invocation with json format."""
    with (
        patch(
            "infra.gcp.bootstrap.GcpInspector.discover_billing_account",
            return_value=SAMPLE_BILLING_ID,
        ),
        patch("infra.gcp.bootstrap.GcpInspector.project_exists", return_value=False),
        patch("infra.gcp.bootstrap.GcpInspector.get_budget", return_value=None),
    ):
        exit_code = main(["plan", "--project-id=ngabo-amr-2026", "--format=json"])
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["project_id"] == "ngabo-amr-2026"
        assert SAMPLE_BILLING_ID not in captured.out


def test_cli_apply_json_clean_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that apply --format=json emits parseable JSON on stdout and progress on stderr."""
    with (
        patch(
            "infra.gcp.bootstrap.GcpInspector.discover_billing_account",
            return_value=SAMPLE_BILLING_ID,
        ),
        patch("infra.gcp.bootstrap.GcpInspector.project_exists", return_value=True),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_project_details",
            return_value={"labels": STANDARD_LABELS},
        ),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_project_labels",
            return_value=STANDARD_LABELS,
        ),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_linked_billing_account",
            return_value=SAMPLE_BILLING_ID,
        ),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_enabled_apis",
            return_value=set(REQUIRED_APIS),
        ),
        patch("infra.gcp.bootstrap.GcpInspector.artifact_registry_exists", return_value=True),
        patch(
            "infra.gcp.bootstrap.GcpInspector.validate_artifact_registry_config",
            return_value=(True, []),
        ),
        patch("infra.gcp.bootstrap.GcpInspector.get_budget", return_value=VALID_SAMPLE_BUDGET),
        patch("infra.gcp.bootstrap.GcpBootstrapper.export_evidence"),
    ):
        exit_code = main(["apply", "--project-id=ngabo-amr-2026", "--format=json"])
        assert exit_code == 0
        captured = capsys.readouterr()
        # Stdout must parse directly as valid JSON
        data = json.loads(captured.out)
        assert data["success"] is True
        assert data["noop"] is True
        # No progress text on stdout
        assert "[apply]" not in captured.out
        # Progress text appears on stderr
        assert "[apply] Project ngabo-amr-2026 already exists." in captured.err


def test_cli_validate_json_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI validate with json format on valid infrastructure."""
    with (
        patch(
            "infra.gcp.bootstrap.GcpInspector.discover_billing_account",
            return_value=SAMPLE_BILLING_ID,
        ),
        patch("infra.gcp.bootstrap.GcpInspector.project_exists", return_value=True),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_project_details",
            return_value={"labels": STANDARD_LABELS},
        ),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_project_labels",
            return_value=STANDARD_LABELS,
        ),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_linked_billing_account",
            return_value=SAMPLE_BILLING_ID,
        ),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_enabled_apis",
            return_value=set(REQUIRED_APIS),
        ),
        patch(
            "infra.gcp.bootstrap.GcpInspector.validate_artifact_registry_config",
            return_value=(True, []),
        ),
        patch("infra.gcp.bootstrap.GcpInspector.get_budget", return_value=VALID_SAMPLE_BUDGET),
    ):
        exit_code = main(["validate", "--project-id=ngabo-amr-2026", "--format=json"])
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["passed"] is True
        assert data["checks"]["project_exists"] is True


def test_cli_validate_missing_project_text(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI validate with missing project in text format exits 1 without KeyError."""
    with patch("infra.gcp.bootstrap.GcpInspector.project_exists", return_value=False):
        exit_code = main(["validate", "--project-id=ngabo-amr-2026", "--format=text"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Status:   FAILED" in captured.out
        assert "Project 'ngabo-amr-2026' does not exist." in captured.out


def test_cli_validate_missing_project_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI validate with missing project in json format exits 1 with stable schema."""
    with patch("infra.gcp.bootstrap.GcpInspector.project_exists", return_value=False):
        exit_code = main(["validate", "--project-id=ngabo-amr-2026", "--format=json"])
        assert exit_code == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["passed"] is False
        assert data["checks"]["project_exists"] is False
        assert data["checks"]["project_labels_valid"] is False
        assert data["checks"]["billing_linked"] is False
        assert data["checks"]["billing_matches_intended"] is False
        assert data["checks"]["required_apis_enabled"] is False
        assert data["checks"]["artifact_registry_valid"] is False
        assert data["checks"]["budget_contract_valid"] is False
        assert any("does not exist" in f for f in data["failures"])


def test_validate_ambiguous_billing_discovery_fails_cleanly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that ambiguous billing discovery produces a structured validation failure."""
    with (
        patch(
            "infra.gcp.bootstrap.GcpInspector.discover_billing_account",
            side_effect=RuntimeError(
                "Disambiguation required: multiple open billing accounts found."
            ),
        ),
        patch("infra.gcp.bootstrap.GcpInspector.project_exists", return_value=True),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_project_labels",
            return_value=STANDARD_LABELS,
        ),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_linked_billing_account",
            return_value=SAMPLE_BILLING_ID,
        ),
        patch(
            "infra.gcp.bootstrap.GcpInspector.get_enabled_apis",
            return_value=set(REQUIRED_APIS),
        ),
        patch(
            "infra.gcp.bootstrap.GcpInspector.validate_artifact_registry_config",
            return_value=(True, []),
        ),
    ):
        exit_code = main(["validate", "--project-id=ngabo-amr-2026", "--format=json"])
        assert exit_code == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["passed"] is False
        assert any("Billing account discovery failure" in f for f in data["failures"])
        assert any("Budget validation skipped" in f for f in data["failures"])


def test_cli_teardown_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI teardown invocation with json format."""
    with (
        patch(
            "infra.gcp.bootstrap.GcpInspector.discover_billing_account",
            return_value=SAMPLE_BILLING_ID,
        ),
        patch("infra.gcp.bootstrap.GcpInspector.get_budget", return_value=VALID_SAMPLE_BUDGET),
    ):
        exit_code = main(
            ["teardown", "--dry-run", "--project-id=ngabo-amr-2026", "--format=json"]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["teardown_mode"] == "PLAN_ONLY"
        assert data["destructive_actions_executed"] is False
        assert data["cessation_verification_executed"] is False
        assert data["cessation_verification_required_on_real_teardown"] is True
        assert SAMPLE_BILLING_ID not in captured.out


def test_apply_updates_budget_in_place_when_drift_detected() -> None:
    """Test that apply performs an in-place update on budget drift rather than deleting first."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)

    drifted_budget = json.loads(json.dumps(VALID_SAMPLE_BUDGET))
    drifted_budget["amount"]["specifiedAmount"]["units"] = "150"

    captured_commands: list[list[str]] = []

    def mock_gcloud(cmd: list[str]) -> tuple[int, str, str]:
        captured_commands.append(cmd)
        return (0, "{}", "")

    with (
        patch.object(bootstrapper.inspector, "project_exists", return_value=True),
        patch.object(bootstrapper.inspector, "get_project_labels", return_value=STANDARD_LABELS),
        patch.object(
            bootstrapper.inspector, "get_linked_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(bootstrapper.inspector, "get_enabled_apis", return_value=set(REQUIRED_APIS)),
        patch.object(bootstrapper.inspector, "artifact_registry_exists", return_value=True),
        patch.object(
            bootstrapper.inspector, "validate_artifact_registry_config", return_value=(True, [])
        ),
        patch.object(
            bootstrapper.inspector, "discover_billing_account", return_value=SAMPLE_BILLING_ID
        ),
        patch.object(
            bootstrapper.inspector,
            "get_project_details",
            return_value={"projectNumber": "907313480935"},
        ),
        patch.object(bootstrapper.inspector, "get_budget", return_value=drifted_budget),
        patch("infra.gcp.bootstrap.run_gcloud_command", side_effect=mock_gcloud),
    ):
        res = bootstrapper.apply()
        assert res["success"] is True
        assert "BUDGET_ALERT_UPDATED" in res["operations"]
        # Ensure budgets delete was NOT called
        assert not any("delete" in cmd for cmd in captured_commands)
        # Ensure budgets update WAS called
        assert any(cmd[0:3] == ["billing", "budgets", "update"] for cmd in captured_commands)


def test_export_evidence_executable_derivation(tmp_path: Path) -> None:
    """Test export_evidence derives verification_results dynamically and marks privacy audit."""
    cfg = GcpBootstrapConfig(project_id="ngabo-amr-2026", region=PRIMARY_REGION)
    bootstrapper = GcpBootstrapper(cfg)
    target = tmp_path / "test_evidence.json"

    with (
        patch.object(
            bootstrapper,
            "validate",
            return_value={"passed": True, "checks": {"project_exists": True}},
        ),
        patch.object(
            bootstrapper,
            "teardown_rehearsal",
            return_value={
                "teardown_rehearsal_passed": True,
                "teardown_mode": "PLAN_ONLY",
                "destructive_actions_executed": False,
                "cessation_verification_executed": False,
                "cessation_verification_required_on_real_teardown": True,
            },
        ),
        patch.object(
            bootstrapper.inspector,
            "get_project_details",
            return_value={"labels": STANDARD_LABELS},
        ),
        patch.object(
            bootstrapper.inspector,
            "get_artifact_registry_details",
            return_value=VALID_SAMPLE_AR_DETAILS,
        ),
    ):
        out_path = bootstrapper.export_evidence(target)
        assert out_path.exists()
        data = json.loads(out_path.read_text(encoding="utf-8"))
        vr = data["verification_results"]
        assert vr["validation_passed"] is True
        assert vr["teardown_rehearsal_passed"] is True
        assert vr["teardown_mode"] == "PLAN_ONLY"
        assert vr["destructive_actions_executed"] is False
        assert vr["cessation_verification_executed"] is False
        assert vr["cessation_verification_required_on_real_teardown"] is True
        assert vr["privacy_audit_status"] == "EXTERNAL_REVIEW_REQUIRED"
