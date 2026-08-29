"""Offline deterministic unit tests for Ngabo Identity, Service Accounts, and WIF Management (Issue #87).

All tests execute strictly offline with mocked subprocess/Cloud SDK execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from infra.gcp.identity import GcpIdentityManager
from infra.gcp.identity_config import (
    ACTIONS_CHECKOUT_PIN,
    CORE_RUNTIME_SA_NAME,
    DEPLOYER_ACT_AS_TARGETS,
    DEPLOYER_PROJECT_ROLES,
    DEPLOYER_SA_NAME,
    GITHUB_ALLOWED_ENV,
    GITHUB_ALLOWED_REF,
    GITHUB_ISSUER,
    GITHUB_OWNER_ID,
    GITHUB_REPO_ID,
    GOOGLE_AUTH_ACTION_PIN,
    PROHIBITED_BASIC_ROLES,
    SECRET_CONTRACTS,
    SERVICE_ACCOUNTS,
    WEB_RUNTIME_SA_NAME,
    WIF_ATTRIBUTE_CONDITION,
    WIF_ATTRIBUTE_MAPPING,
    WIF_POOL_ID,
    WIF_PROVIDER_ID,
    GcpIdentityConfig,
)

SAMPLE_PROJECT_ID = "ngabo-amr-2026"
SAMPLE_PROJECT_NUMBER = "907313480935"

VALID_SAMPLE_PROVIDER_DETAILS = {
    "name": f"projects/{SAMPLE_PROJECT_NUMBER}/locations/global/workloadIdentityPools/{WIF_POOL_ID}/providers/{WIF_PROVIDER_ID}",
    "displayName": "Ngabo GitHub Repository Provider",
    "attributeMapping": WIF_ATTRIBUTE_MAPPING,
    "attributeCondition": WIF_ATTRIBUTE_CONDITION,
    "issuerUri": GITHUB_ISSUER,
    "state": "ACTIVE",
}

VALID_PROJECT_BINDINGS = [
    {
        "role": "roles/run.developer",
        "members": [f"serviceAccount:{DEPLOYER_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
    }
]

VALID_AR_BINDINGS = [
    {
        "role": "roles/artifactregistry.reader",
        "members": [f"serviceAccount:{DEPLOYER_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
    }
]

VALID_RUNTIME_SA_BINDINGS = [
    {
        "role": "roles/iam.serviceAccountUser",
        "members": [f"serviceAccount:{DEPLOYER_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
    }
]

VALID_DEPLOYER_SA_BINDINGS = [
    {
        "role": "roles/iam.workloadIdentityUser",
        "members": [
            f"principalSet://iam.googleapis.com/projects/{SAMPLE_PROJECT_NUMBER}/locations/global/workloadIdentityPools/{WIF_POOL_ID}/attribute.repository_id/{GITHUB_REPO_ID}"
        ],
    }
]


@pytest.fixture(autouse=True)
def guard_offline_execution() -> Any:
    """Ensure no tests ever call real gcloud/gh binaries."""
    with patch("subprocess.run") as mock_subproc:
        mock_subproc.side_effect = RuntimeError("Real subprocess execution blocked in offline test suite.")
        yield mock_subproc


def create_converged_manager() -> GcpIdentityManager:
    """Helper to construct a manager with all inspector queries mocked to match target contract."""
    cfg = GcpIdentityConfig(
        project_id=SAMPLE_PROJECT_ID,
        project_number=SAMPLE_PROJECT_NUMBER,
    )
    mgr = GcpIdentityManager(cfg)

    mgr.inspector.get_project_number = MagicMock(return_value=SAMPLE_PROJECT_NUMBER)  # type: ignore[method-assign]
    mgr.inspector.service_account_exists = MagicMock(return_value=True)  # type: ignore[method-assign]
    mgr.inspector.get_user_managed_keys = MagicMock(return_value=[])  # type: ignore[method-assign]
    mgr.inspector.wif_pool_exists = MagicMock(return_value=True)  # type: ignore[method-assign]
    mgr.inspector.wif_provider_exists = MagicMock(return_value=True)  # type: ignore[method-assign]
    mgr.inspector.get_wif_provider_details = MagicMock(return_value=VALID_SAMPLE_PROVIDER_DETAILS)  # type: ignore[method-assign]
    mgr.inspector.get_project_iam_bindings = MagicMock(return_value=VALID_PROJECT_BINDINGS)  # type: ignore[method-assign]
    mgr.inspector.get_artifact_registry_iam_bindings = MagicMock(return_value=VALID_AR_BINDINGS)  # type: ignore[method-assign]

    def sa_bindings_side_effect(sa_email: str) -> list[dict[str, Any]]:
        if DEPLOYER_SA_NAME in sa_email:
            return VALID_DEPLOYER_SA_BINDINGS
        return VALID_RUNTIME_SA_BINDINGS

    mgr.inspector.get_service_account_iam_bindings = MagicMock(  # type: ignore[method-assign]
        side_effect=sa_bindings_side_effect
    )
    return mgr


# ---------------------------------------------------------------------------
# WIF & Synthetic OIDC Claim Policy Evaluation Tests
# ---------------------------------------------------------------------------


def test_wif_attribute_mapping_has_required_keys() -> None:
    """Validate that WIF attribute mappings include mandatory subject and numeric claims."""
    assert "google.subject" in WIF_ATTRIBUTE_MAPPING
    assert WIF_ATTRIBUTE_MAPPING["google.subject"] == "assertion.sub"
    assert WIF_ATTRIBUTE_MAPPING["attribute.repository_id"] == "assertion.repository_id"
    assert WIF_ATTRIBUTE_MAPPING["attribute.repository_owner_id"] == "assertion.repository_owner_id"
    assert WIF_ATTRIBUTE_MAPPING["attribute.ref"] == "assertion.ref"
    assert WIF_ATTRIBUTE_MAPPING["attribute.environment"] == "assertion.environment"
    assert WIF_ATTRIBUTE_MAPPING["attribute.workflow_ref"] == "assertion.workflow_ref"


def test_synthetic_oidc_claims_evaluation() -> None:
    """Evaluate synthetic OIDC assertions against the provider attribute condition."""

    def evaluate_condition(assertion: dict[str, Any]) -> bool:
        repo_id = str(assertion.get("repository_id", ""))
        owner_id = str(assertion.get("repository_owner_id", ""))
        ref = str(assertion.get("ref", ""))
        return (
            repo_id == GITHUB_REPO_ID
            and owner_id == GITHUB_OWNER_ID
            and ref == GITHUB_ALLOWED_REF
        )

    valid_assertion = {
        "repository_id": GITHUB_REPO_ID,
        "repository_owner_id": GITHUB_OWNER_ID,
        "ref": "refs/heads/develop",
        "environment": "dev",
    }
    assert evaluate_condition(valid_assertion) is True

    # Negative: wrong repository ID
    wrong_repo = {**valid_assertion, "repository_id": "9999999999"}
    assert evaluate_condition(wrong_repo) is False

    # Negative: wrong owner ID
    wrong_owner = {**valid_assertion, "repository_owner_id": "99999999"}
    assert evaluate_condition(wrong_owner) is False

    # Negative: feature branch
    wrong_ref = {**valid_assertion, "ref": "refs/heads/feature/unauthorized"}
    assert evaluate_condition(wrong_ref) is False

    # Negative: pull request ref
    pr_ref = {**valid_assertion, "ref": "refs/pull/100/merge"}
    assert evaluate_condition(pr_ref) is False

    # Negative: tags
    tag_ref = {**valid_assertion, "ref": "refs/tags/v0.1.0"}
    assert evaluate_condition(tag_ref) is False


# ---------------------------------------------------------------------------
# Key Policy & Validation Tests
# ---------------------------------------------------------------------------


def test_validate_passes_on_converged_environment() -> None:
    """Test that validation passes cleanly on a fully converged environment."""
    mgr = create_converged_manager()
    res = mgr.validate()
    assert res["passed"] is True
    assert res["failures"] == []
    assert res["checks"]["service_accounts_present"] is True
    assert res["checks"]["user_managed_keys_zero"] is True
    assert res["checks"]["wif_pool_valid"] is True
    assert res["checks"]["wif_provider_valid"] is True
    assert res["checks"]["deployer_roles_match_allowlist"] is True
    assert res["checks"]["runtime_roles_match_allowlist"] is True
    assert res["checks"]["prohibited_basic_roles_absent"] is True
    assert res["checks"]["project_wide_secret_accessor_absent"] is True
    assert res["checks"]["deployer_act_as_valid"] is True
    assert res["checks"]["wif_impersonation_valid"] is True


def test_validate_fails_if_user_managed_key_present() -> None:
    """Test that validation fails if any user-managed key exists on a service account."""
    mgr = create_converged_manager()
    mgr.inspector.get_user_managed_keys = MagicMock(  # type: ignore[method-assign]
        side_effect=lambda email: [{"name": "key1"}] if DEPLOYER_SA_NAME in email else []
    )
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["user_managed_keys_zero"] is False
    assert any("Prohibited user-managed key found" in f for f in res["failures"])


def test_validate_fails_if_service_account_missing() -> None:
    """Test validation failure when a required service account is missing."""
    mgr = create_converged_manager()
    mgr.inspector.service_account_exists = MagicMock(  # type: ignore[method-assign]
        side_effect=lambda email: CORE_RUNTIME_SA_NAME not in email
    )
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["service_accounts_present"] is False
    assert any("Required service account 'ngabo-core-runtime'" in f for f in res["failures"])


def test_validate_fails_on_prohibited_basic_roles() -> None:
    """Test validation rejection when prohibited roles (e.g. roles/owner, roles/editor) appear."""
    mgr = create_converged_manager()
    for bad_role in PROHIBITED_BASIC_ROLES:
        mgr.inspector.get_project_iam_bindings = MagicMock(  # type: ignore[method-assign]
            return_value=VALID_PROJECT_BINDINGS + [
                {
                    "role": bad_role,
                    "members": [f"serviceAccount:{DEPLOYER_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
                }
            ]
        )
        res = mgr.validate()
        assert res["passed"] is False
        assert res["checks"]["prohibited_basic_roles_absent"] is False
        assert any(bad_role in f for f in res["failures"])


def test_validate_fails_on_project_wide_secret_accessor() -> None:
    """Test validation rejection if project-wide secretAccessor is assigned to any service account."""
    mgr = create_converged_manager()
    mgr.inspector.get_project_iam_bindings = MagicMock(  # type: ignore[method-assign]
        return_value=VALID_PROJECT_BINDINGS + [
            {
                "role": "roles/secretmanager.secretAccessor",
                "members": [f"serviceAccount:{CORE_RUNTIME_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
            }
        ]
    )
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["project_wide_secret_accessor_absent"] is False
    assert any("prohibited project-wide secretAccessor" in f for f in res["failures"])


def test_validate_fails_on_missing_act_as_binding() -> None:
    """Test validation failure if deployer lacks actAs on a runtime service account."""
    mgr = create_converged_manager()
    mgr.inspector.get_service_account_iam_bindings = MagicMock(  # type: ignore[method-assign]
        side_effect=lambda email: []
    )
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["deployer_act_as_valid"] is False


def test_validate_fails_on_missing_wif_impersonation() -> None:
    """Test validation failure if deployer lacks workloadIdentityUser binding."""
    mgr = create_converged_manager()
    mgr.inspector.get_service_account_iam_bindings = MagicMock(  # type: ignore[method-assign]
        side_effect=lambda email: VALID_RUNTIME_SA_BINDINGS if DEPLOYER_SA_NAME not in email else []
    )
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["wif_impersonation_valid"] is False


# ---------------------------------------------------------------------------
# Plan and Apply Idempotency Tests
# ---------------------------------------------------------------------------


def test_plan_converged_when_live_matches_target() -> None:
    """Test that plan reports converged with 0 planned actions on target state."""
    mgr = create_converged_manager()
    plan = mgr.plan()
    assert plan["is_converged"] is True
    assert plan["planned_actions"] == []


def test_plan_reports_unconverged_actions() -> None:
    """Test that plan enumerates missing service accounts, pool, provider, and bindings."""
    cfg = GcpIdentityConfig(project_id=SAMPLE_PROJECT_ID, project_number=SAMPLE_PROJECT_NUMBER)
    mgr = GcpIdentityManager(cfg)
    mgr.inspector.get_project_number = MagicMock(return_value=SAMPLE_PROJECT_NUMBER)  # type: ignore[method-assign]
    mgr.inspector.service_account_exists = MagicMock(return_value=False)  # type: ignore[method-assign]
    mgr.inspector.get_user_managed_keys = MagicMock(return_value=[])  # type: ignore[method-assign]
    mgr.inspector.wif_pool_exists = MagicMock(return_value=False)  # type: ignore[method-assign]
    mgr.inspector.get_project_iam_bindings = MagicMock(return_value=[])  # type: ignore[method-assign]
    mgr.inspector.get_artifact_registry_iam_bindings = MagicMock(return_value=[])  # type: ignore[method-assign]
    mgr.inspector.get_service_account_iam_bindings = MagicMock(return_value=[])  # type: ignore[method-assign]

    plan = mgr.plan()
    assert plan["is_converged"] is False
    assert any("Create service account 'ngabo-deployer'" in a for a in plan["planned_actions"])
    assert any(f"Create Workload Identity Pool '{WIF_POOL_ID}'" in a for a in plan["planned_actions"])
    assert any("Grant 'roles/run.developer'" in a for a in plan["planned_actions"])


def test_apply_idempotent_no_op() -> None:
    """Test that apply executes 0 operations on converged environment."""
    mgr = create_converged_manager()
    captured_commands: list[list[str]] = []

    def mock_gcloud(cmd: list[str]) -> tuple[int, str, str]:
        captured_commands.append(cmd)
        return (0, "{}", "")

    with patch("infra.gcp.identity.run_gcloud_command", side_effect=mock_gcloud):
        res = mgr.apply()
        assert res["success"] is True
        assert res["noop"] is True
        assert res["operations"] == []
        assert len(captured_commands) == 0


def test_apply_provisions_missing_resources() -> None:
    """Test that apply executes creation commands for missing items."""
    cfg = GcpIdentityConfig(project_id=SAMPLE_PROJECT_ID, project_number=SAMPLE_PROJECT_NUMBER)
    mgr = GcpIdentityManager(cfg)
    mgr.inspector.get_project_number = MagicMock(return_value=SAMPLE_PROJECT_NUMBER)  # type: ignore[method-assign]
    mgr.inspector.service_account_exists = MagicMock(return_value=False)  # type: ignore[method-assign]
    mgr.inspector.get_user_managed_keys = MagicMock(return_value=[])  # type: ignore[method-assign]
    mgr.inspector.wif_pool_exists = MagicMock(return_value=False)  # type: ignore[method-assign]
    mgr.inspector.wif_provider_exists = MagicMock(return_value=False)  # type: ignore[method-assign]
    mgr.inspector.get_project_iam_bindings = MagicMock(return_value=[])  # type: ignore[method-assign]
    mgr.inspector.get_artifact_registry_iam_bindings = MagicMock(return_value=[])  # type: ignore[method-assign]
    mgr.inspector.get_service_account_iam_bindings = MagicMock(return_value=[])  # type: ignore[method-assign]

    captured_commands: list[list[str]] = []

    def mock_gcloud(cmd: list[str]) -> tuple[int, str, str]:
        captured_commands.append(cmd)
        return (0, "{}", "")

    with patch("infra.gcp.identity.run_gcloud_command", side_effect=mock_gcloud):
        res = mgr.apply()
        assert res["success"] is True
        assert res["noop"] is False
        assert len(res["operations"]) > 0
        # Assert service account creations occurred
        assert any("service-accounts" in cmd and "create" in cmd for cmd in captured_commands)
        # Assert WIF pool creation occurred
        assert any("workload-identity-pools" in cmd and "create" in cmd for cmd in captured_commands)
        # Assert WIF provider creation occurred
        assert any("providers" in cmd and "create-oidc" in cmd for cmd in captured_commands)


# ---------------------------------------------------------------------------
# Secret Contract & Teardown Rehearsal Tests
# ---------------------------------------------------------------------------


def test_secret_contracts_defined_without_values() -> None:
    """Validate that Secret Manager contracts define environments, owners, and behaviors without secret values."""
    assert len(SECRET_CONTRACTS) >= 2
    for contract in SECRET_CONTRACTS:
        assert contract.environment in ("dev", "judge")
        assert contract.owner_workload == "ngabo-core"
        assert CORE_RUNTIME_SA_NAME in contract.authorized_readers
        assert DEPLOYER_SA_NAME not in contract.authorized_readers
        assert "fails fast" in contract.missing_secret_behavior.lower()
        assert "Destroy secret versions" in contract.teardown_behavior


def test_teardown_rehearsal_is_plan_only() -> None:
    """Test that teardown rehearsal produces a 4-step plan without destructive execution."""
    mgr = create_converged_manager()
    teardown = mgr.teardown_rehearsal()
    assert teardown["teardown_mode"] == "PLAN_ONLY"
    assert teardown["destructive_actions_executed"] is False
    assert teardown["cessation_verification_executed"] is False
    assert teardown["cessation_verification_required_on_real_teardown"] is True
    assert len(teardown["steps"]) == 4


def test_export_evidence_structure(tmp_path: Path) -> None:
    """Test that export_evidence produces compliant machine-readable JSON."""
    mgr = create_converged_manager()
    evidence_file = tmp_path / "identity_evidence.json"
    evidence = mgr.export_evidence(evidence_file)

    assert evidence["contract_version"] == "ngabo-cloud-identity-v1"
    assert evidence["issue"] == "87"
    assert evidence["topology"]["canonical_project_id"] == SAMPLE_PROJECT_ID
    assert evidence["service_accounts"]["created"][DEPLOYER_SA_NAME]["user_managed_key_count"] == 0
    assert evidence["workload_identity_federation"]["pool_id"] == WIF_POOL_ID
    assert evidence["github_integration"]["auth_proof_workflow"]["permissions"] == {
        "contents": "read",
        "id-token": "write",
    }
    assert evidence["iam_contracts"]["prohibited_basic_roles_verified_absent"] == list(
        PROHIBITED_BASIC_ROLES
    )
    assert evidence["verification_results"]["privacy_audit_status"] == "EXTERNAL_REVIEW_REQUIRED"

    # Verify file was written and is valid JSON
    assert evidence_file.exists()
    with open(evidence_file, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["contract_version"] == "ngabo-cloud-identity-v1"


# ---------------------------------------------------------------------------
# Workflow File & Action Pinning Tests
# ---------------------------------------------------------------------------


def test_workflow_file_permissions_and_pinned_actions() -> None:
    """Verify that .github/workflows/wif-auth-proof.yml uses exact minimal permissions and pinned commit SHAs."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    workflow_path = repo_root / ".github" / "workflows" / "wif-auth-proof.yml"
    assert workflow_path.exists(), f"Workflow file {workflow_path} must exist."

    content = workflow_path.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in content
    assert "environment: dev" in content
    assert "contents: read" in content
    assert "id-token: write" in content

    # Check pinned action SHAs
    assert ACTIONS_CHECKOUT_PIN["commit_sha"] in content
    assert GOOGLE_AUTH_ACTION_PIN["commit_sha"] in content
    # Verify no unpinned floating tags like @v3 or @main
    assert "@v4" not in content
    assert "@v3" not in content
    assert "@v2" not in content
    assert "@main" not in content
    assert "@master" not in content


# ---------------------------------------------------------------------------
# CLI & Configuration Helper Tests
# ---------------------------------------------------------------------------


def test_gcp_identity_config_methods() -> None:
    """Test helper methods on GcpIdentityConfig."""
    cfg = GcpIdentityConfig(project_id="test-proj", project_number="123456789")
    assert cfg.service_account_email("my-sa") == "my-sa@test-proj.iam.gserviceaccount.com"
    assert (
        cfg.wif_pool_name()
        == "projects/123456789/locations/global/workloadIdentityPools/ngabo-github"
    )
    assert (
        cfg.wif_provider_name()
        == "projects/123456789/locations/global/workloadIdentityPools/ngabo-github/providers/ngabo-repo"
    )
    assert (
        cfg.wif_principal_set()
        == f"principalSet://iam.googleapis.com/projects/123456789/locations/global/workloadIdentityPools/ngabo-github/attribute.repository_id/{GITHUB_REPO_ID}"
    )


def test_cli_plan_text_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI main() for plan command in text and json formats."""
    from infra.gcp.identity import main

    with patch("infra.gcp.identity.GcpIdentityManager", return_value=create_converged_manager()):
        # Text format
        code = main(["plan"])
        assert code == 0
        captured = capsys.readouterr()
        assert "Ngabo GCP Identity & WIF Plan" in captured.out
        assert "Converged (No-op):True" in captured.out

        # JSON format
        code = main(["--format=json", "plan"])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["is_converged"] is True


def test_cli_validate_text_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI main() for validate command in text and json formats."""
    from infra.gcp.identity import main

    with patch("infra.gcp.identity.GcpIdentityManager", return_value=create_converged_manager()):
        # Text format
        code = main(["validate"])
        assert code == 0
        captured = capsys.readouterr()
        assert "Ngabo GCP Identity & WIF Validation" in captured.out
        assert "PASSED" in captured.out

        # JSON format
        code = main(["--format=json", "validate"])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["passed"] is True


def test_cli_apply_text_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI main() for apply command in text and json formats."""
    from infra.gcp.identity import main

    mgr = create_converged_manager()
    with patch("infra.gcp.identity.GcpIdentityManager", return_value=mgr):
        # Text format
        code = main(["apply"])
        assert code == 0
        captured = capsys.readouterr()
        assert "Identity bootstrap completed successfully." in captured.out

        # JSON format
        code = main(["--format=json", "apply"])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["success"] is True
        assert data["noop"] is True


def test_cli_teardown_text_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Test CLI main() for teardown --dry-run command in text and json formats."""
    from infra.gcp.identity import main

    mgr = create_converged_manager()
    with patch("infra.gcp.identity.GcpIdentityManager", return_value=mgr):
        # Text format
        code = main(["teardown", "--dry-run"])
        assert code == 0
        captured = capsys.readouterr()
        assert "Teardown Rehearsal (PLAN_ONLY)" in captured.out

        # JSON format
        code = main(["--format=json", "teardown", "--dry-run"])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["teardown_mode"] == "PLAN_ONLY"
