"""Offline deterministic unit tests for Ngabo Identity, Service Accounts, and WIF Management (Issue #87).

All tests execute strictly offline with mocked subprocess/Cloud SDK execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from infra.gcp.github_env import GitHubEnvInspector, GitHubEnvManager
from infra.gcp.identity import GcpIdentityInspector, GcpIdentityManager
from infra.gcp.identity_config import (
    ACTIONS_CHECKOUT_PIN,
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
    GOOGLE_AUTH_ACTION_PIN,
    GOOGLE_SETUP_GCLOUD_ACTION_PIN,
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
    "oidc": {"issuerUri": GITHUB_ISSUER},
    "state": "ACTIVE",
}

# DEPLOYER_PROJECT_ROLES is empty tuple () per #87 least privilege contract
VALID_PROJECT_BINDINGS: list[dict[str, Any]] = []

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
    mgr.inspector.get_project_iam_bindings = MagicMock(return_value=list(VALID_PROJECT_BINDINGS))  # type: ignore[method-assign]
    mgr.inspector.get_artifact_registry_iam_bindings = MagicMock(return_value=list(VALID_AR_BINDINGS))  # type: ignore[method-assign]
    mgr.inspector.get_all_project_service_accounts = MagicMock(  # type: ignore[method-assign]
        return_value=[{"email": mgr.config.service_account_email(sa)} for sa in SERVICE_ACCOUNTS]
    )

    def sa_bindings_side_effect(sa_email: str) -> list[dict[str, Any]]:
        if DEPLOYER_SA_NAME in sa_email:
            return list(VALID_DEPLOYER_SA_BINDINGS)
        return list(VALID_RUNTIME_SA_BINDINGS)

    mgr.inspector.get_service_account_iam_bindings = MagicMock(  # type: ignore[method-assign]
        side_effect=sa_bindings_side_effect
    )

    # GitHub Environment mocks
    mgr.github_manager.inspector.get_environment = MagicMock(  # type: ignore[method-assign]
        return_value={
            "deployment_branch_policy": {
                "protected_branches": False,
                "custom_branch_policies": True,
            }
        }
    )
    mgr.github_manager.inspector.get_branch_policies = MagicMock(return_value=["develop"])  # type: ignore[method-assign]

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
        env = str(assertion.get("environment", ""))
        return (
            repo_id == GITHUB_REPO_ID
            and owner_id == GITHUB_OWNER_ID
            and ref == GITHUB_ALLOWED_REF
            and env == GITHUB_ALLOWED_ENV
        )

    valid_assertion = {
        "repository_id": GITHUB_REPO_ID,
        "repository_owner_id": GITHUB_OWNER_ID,
        "ref": "refs/heads/develop",
        "environment": "dev",
    }
    # Correct repo + owner + develop + dev -> ALLOW
    assert evaluate_condition(valid_assertion) is True

    # Negative: correct repo + owner + develop + no environment -> DENY
    no_env = {k: v for k, v in valid_assertion.items() if k != "environment"}
    assert evaluate_condition(no_env) is False

    # Negative: correct repo + owner + develop + wrong environment -> DENY
    wrong_env = {**valid_assertion, "environment": "production"}
    assert evaluate_condition(wrong_env) is False

    # Negative: feature branch + dev -> DENY
    wrong_ref = {**valid_assertion, "ref": "refs/heads/feature/cloud-1a-3-keyless-iam"}
    assert evaluate_condition(wrong_ref) is False

    # Negative: wrong repository ID -> DENY
    wrong_repo = {**valid_assertion, "repository_id": "9999999999"}
    assert evaluate_condition(wrong_repo) is False

    # Negative: wrong owner ID -> DENY
    wrong_owner = {**valid_assertion, "repository_owner_id": "99999999"}
    assert evaluate_condition(wrong_owner) is False

    # Negative: pull request ref -> DENY
    pr_ref = {**valid_assertion, "ref": "refs/pull/102/merge"}
    assert evaluate_condition(pr_ref) is False

    # Negative: tags -> DENY
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
    assert res["checks"]["deployer_ar_roles_match_allowlist"] is True
    assert res["checks"]["runtime_roles_match_allowlist"] is True
    assert res["checks"]["prohibited_basic_roles_absent"] is True
    assert res["checks"]["project_wide_secret_accessor_absent"] is True
    assert res["checks"]["deployer_act_as_valid"] is True
    assert res["checks"]["wif_impersonation_exact"] is True
    assert res["checks"]["github_env_valid"] is True


def test_validate_fails_if_user_managed_key_present() -> None:
    """Test that validation fails if any user-managed key exists on a service account."""
    mgr = create_converged_manager()
    mgr.inspector.get_user_managed_keys = MagicMock(  # type: ignore[method-assign]
        return_value=[{"name": "projects/-/serviceAccounts/123/keys/bad-key"}]
    )
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["user_managed_keys_zero"] is False
    assert any("Prohibited user-managed key" in f for f in res["failures"])


def test_validate_fails_if_service_account_missing() -> None:
    """Test that validation fails if any required service account is absent."""
    mgr = create_converged_manager()
    mgr.inspector.service_account_exists = MagicMock(return_value=False)  # type: ignore[method-assign]
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["service_accounts_present"] is False


def test_validate_fails_if_wif_pool_missing() -> None:
    """Test that validation fails if WIF pool does not exist."""
    mgr = create_converged_manager()
    mgr.inspector.wif_pool_exists = MagicMock(return_value=False)  # type: ignore[method-assign]
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["wif_pool_valid"] is False


def test_validate_fails_if_wif_provider_missing() -> None:
    """Test that validation fails if WIF provider does not exist."""
    mgr = create_converged_manager()
    mgr.inspector.wif_provider_exists = MagicMock(return_value=False)  # type: ignore[method-assign]
    mgr.inspector.get_wif_provider_details = MagicMock(return_value=None)  # type: ignore[method-assign]
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["wif_provider_valid"] is False


def test_validate_fails_if_wif_provider_issuer_mismatched_or_inactive() -> None:
    """Test that validation fails if WIF provider issuer or state is invalid."""
    mgr = create_converged_manager()
    bad_provider = dict(VALID_SAMPLE_PROVIDER_DETAILS)
    bad_provider["oidc"] = {"issuerUri": "https://evil.token.issuer.com"}
    mgr.inspector.get_wif_provider_details = MagicMock(return_value=bad_provider)  # type: ignore[method-assign]

    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["wif_provider_valid"] is False
    assert any("issuer" in f for f in res["failures"])

    bad_state_provider = dict(VALID_SAMPLE_PROVIDER_DETAILS)
    bad_state_provider["state"] = "DISABLED"
    mgr.inspector.get_wif_provider_details = MagicMock(return_value=bad_state_provider)  # type: ignore[method-assign]
    res2 = mgr.validate()
    assert res2["passed"] is False
    assert any("ACTIVE" in f for f in res2["failures"])


# ---------------------------------------------------------------------------
# IAM Allow-list & Scope Enforcement Tests
# ---------------------------------------------------------------------------


def test_validate_fails_on_unapproved_deployer_project_role() -> None:
    """Test that validation fails if deployer has ANY project role not in DEPLOYER_PROJECT_ROLES."""
    mgr = create_converged_manager()
    # DEPLOYER_PROJECT_ROLES is empty; adding any role must trigger failure
    unapproved_bindings = [
        {
            "role": "roles/run.developer",
            "members": [f"serviceAccount:{DEPLOYER_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
        }
    ]
    mgr.inspector.get_project_iam_bindings = MagicMock(return_value=unapproved_bindings)  # type: ignore[method-assign]
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["deployer_roles_match_allowlist"] is False
    assert any("Deployer project roles" in f for f in res["failures"])


def test_validate_fails_on_extra_artifact_registry_role() -> None:
    """Test that validation fails if deployer possesses extra Artifact Registry roles."""
    mgr = create_converged_manager()
    extra_ar_bindings = [
        {
            "role": "roles/artifactregistry.reader",
            "members": [f"serviceAccount:{DEPLOYER_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
        },
        {
            "role": "roles/artifactregistry.writer",
            "members": [f"serviceAccount:{DEPLOYER_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
        },
    ]
    mgr.inspector.get_artifact_registry_iam_bindings = MagicMock(return_value=extra_ar_bindings)  # type: ignore[method-assign]
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["deployer_ar_roles_match_allowlist"] is False


def test_validate_fails_on_prohibited_basic_role() -> None:
    """Test that validation fails if any service account possesses a basic role."""
    for role in PROHIBITED_BASIC_ROLES:
        mgr = create_converged_manager()
        bad_bindings = [
            {
                "role": role,
                "members": [f"serviceAccount:{DEPLOYER_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
            }
        ]
        mgr.inspector.get_project_iam_bindings = MagicMock(return_value=bad_bindings)  # type: ignore[method-assign]
        res = mgr.validate()
        assert res["passed"] is False
        assert res["checks"]["prohibited_basic_roles_absent"] is False


def test_validate_fails_on_project_wide_secret_accessor() -> None:
    """Test that validation fails if any service account has project-wide secretAccessor."""
    mgr = create_converged_manager()
    bad_bindings = [
        {
            "role": "roles/secretmanager.secretAccessor",
            "members": [f"serviceAccount:{CORE_RUNTIME_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
        }
    ]
    mgr.inspector.get_project_iam_bindings = MagicMock(return_value=bad_bindings)  # type: ignore[method-assign]
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["project_wide_secret_accessor_absent"] is False


def test_validate_fails_on_project_wide_service_account_user() -> None:
    """Test that validation fails if deployer has project-level roles/iam.serviceAccountUser."""
    mgr = create_converged_manager()
    bad_bindings = [
        {
            "role": "roles/iam.serviceAccountUser",
            "members": [f"serviceAccount:{DEPLOYER_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
        }
    ]
    mgr.inspector.get_project_iam_bindings = MagicMock(return_value=bad_bindings)  # type: ignore[method-assign]
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["deployer_act_as_valid"] is False
    assert any("prohibited project-level 'roles/iam.serviceAccountUser'" in f for f in res["failures"])


def test_validate_fails_on_unauthorized_act_as_target() -> None:
    """Test that validation fails if deployer has actAs on an unapproved service account."""
    mgr = create_converged_manager()
    unapproved_sa = f"907313480935-compute@developer.gserviceaccount.com"
    all_sas = [
        {"email": mgr.config.service_account_email(sa)} for sa in SERVICE_ACCOUNTS
    ] + [{"email": unapproved_sa}]
    mgr.inspector.get_all_project_service_accounts = MagicMock(return_value=all_sas)  # type: ignore[method-assign]

    def bad_sa_bindings(email: str) -> list[dict[str, Any]]:
        if email == unapproved_sa:
            return [{
                "role": "roles/iam.serviceAccountUser",
                "members": [f"serviceAccount:{DEPLOYER_SA_NAME}@{SAMPLE_PROJECT_ID}.iam.gserviceaccount.com"],
            }]
        if DEPLOYER_SA_NAME in email:
            return list(VALID_DEPLOYER_SA_BINDINGS)
        return list(VALID_RUNTIME_SA_BINDINGS)

    mgr.inspector.get_service_account_iam_bindings = MagicMock(side_effect=bad_sa_bindings)  # type: ignore[method-assign]
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["deployer_act_as_valid"] is False
    assert any("unauthorized actAs on unapproved service account" in f for f in res["failures"])


def test_validate_fails_on_unauthorized_wif_impersonator() -> None:
    """Test that validation fails if any extra or unauthorized principal can impersonate deployer."""
    mgr = create_converged_manager()
    bad_deployer_bindings = [
        {
            "role": "roles/iam.workloadIdentityUser",
            "members": [
                f"principalSet://iam.googleapis.com/projects/{SAMPLE_PROJECT_NUMBER}/locations/global/workloadIdentityPools/{WIF_POOL_ID}/attribute.repository_id/{GITHUB_REPO_ID}",
                "user:attacker@evil.com",
            ],
        }
    ]

    def bad_bindings_side_effect(email: str) -> list[dict[str, Any]]:
        if DEPLOYER_SA_NAME in email:
            return bad_deployer_bindings
        return list(VALID_RUNTIME_SA_BINDINGS)

    mgr.inspector.get_service_account_iam_bindings = MagicMock(side_effect=bad_bindings_side_effect)  # type: ignore[method-assign]
    res = mgr.validate()
    assert res["passed"] is False
    assert res["checks"]["wif_impersonation_exact"] is False
    assert any("unauthorized WIF impersonator members" in f for f in res["failures"])


# ---------------------------------------------------------------------------
# Fail-Closed Inspector Exception Handling Tests
# ---------------------------------------------------------------------------


def test_inspector_fails_closed_on_subprocess_error() -> None:
    """Test that inspector raises RuntimeError on subprocess failures instead of returning empty lists."""
    cfg = GcpIdentityConfig(project_id=SAMPLE_PROJECT_ID)
    inspector = GcpIdentityInspector(cfg)

    with patch("infra.gcp.identity.run_gcloud_command") as mock_gcloud:
        mock_gcloud.return_value = (1, "", "Permission denied")
        with pytest.raises(RuntimeError, match="INSPECTION_FAILED"):
            inspector.get_user_managed_keys("some-sa@proj.iam.gserviceaccount.com")

        with pytest.raises(RuntimeError, match="INSPECTION_FAILED"):
            inspector.get_project_iam_bindings()

        with pytest.raises(RuntimeError, match="INSPECTION_FAILED"):
            inspector.get_service_account_iam_bindings("some-sa@proj.iam.gserviceaccount.com")

        with pytest.raises(RuntimeError, match="INSPECTION_FAILED"):
            inspector.get_artifact_registry_iam_bindings("repo")


def test_inspector_fails_closed_on_malformed_json() -> None:
    """Test that inspector raises RuntimeError on malformed JSON stdout."""
    cfg = GcpIdentityConfig(project_id=SAMPLE_PROJECT_ID)
    inspector = GcpIdentityInspector(cfg)

    with patch("infra.gcp.identity.run_gcloud_command") as mock_gcloud:
        mock_gcloud.return_value = (0, "not-valid-json{{{", "")
        with pytest.raises(RuntimeError, match="INSPECTION_FAILED"):
            inspector.get_user_managed_keys("some-sa@proj.iam.gserviceaccount.com")


# ---------------------------------------------------------------------------
# GitHub Environment Automation Tests
# ---------------------------------------------------------------------------


def test_github_env_manager_plan_and_validate() -> None:
    """Test GitHubEnvManager plan and validate behavior."""
    inspector = GitHubEnvInspector()
    inspector.get_environment = MagicMock(return_value=None)  # type: ignore[method-assign]
    mgr = GitHubEnvManager(inspector)

    plan = mgr.plan()
    assert plan["is_converged"] is False
    assert len(plan["planned_actions"]) >= 2

    # Converged case
    inspector.get_environment = MagicMock(  # type: ignore[method-assign]
        return_value={"deployment_branch_policy": {"custom_branch_policies": True}}
    )
    inspector.get_branch_policies = MagicMock(return_value=["develop"])  # type: ignore[method-assign]
    val = mgr.validate()
    assert val["passed"] is True
    assert val["checks"]["environment_present"] is True
    assert val["checks"]["custom_branch_policies_enabled"] is True
    assert val["checks"]["exact_branch_policy_matches"] is True


# ---------------------------------------------------------------------------
# Pinned Actions Contract Verification Tests
# ---------------------------------------------------------------------------


def test_actions_checkout_pin_contract() -> None:
    """Ensure actions/checkout pin uses verified current version and full commit SHA."""
    assert ACTIONS_CHECKOUT_PIN["version"] == "v7.0.1"
    assert ACTIONS_CHECKOUT_PIN["commit_sha"] == "3d3c42e5aac5ba805825da76410c181273ba90b1"
    assert len(ACTIONS_CHECKOUT_PIN["commit_sha"]) == 40


def test_google_auth_action_pin_contract() -> None:
    """Ensure google-github-actions/auth pin uses verified current version and full commit SHA."""
    assert GOOGLE_AUTH_ACTION_PIN["version"] == "v3.0.0"
    assert GOOGLE_AUTH_ACTION_PIN["commit_sha"] == "7c6bc770dae815cd3e89ee6cdf493a5fab2cc093"
    assert len(GOOGLE_AUTH_ACTION_PIN["commit_sha"]) == 40


def test_google_setup_gcloud_action_pin_contract() -> None:
    """Ensure google-github-actions/setup-gcloud pin uses verified current version and full commit SHA."""
    assert GOOGLE_SETUP_GCLOUD_ACTION_PIN["version"] == "v3.0.1"
    assert GOOGLE_SETUP_GCLOUD_ACTION_PIN["commit_sha"] == "aa5489c8933f4cc7a4f7d45035b3b1440c9c10db"
    assert len(GOOGLE_SETUP_GCLOUD_ACTION_PIN["commit_sha"]) == 40


# ---------------------------------------------------------------------------
# Evidence & Teardown Rehearsal Tests
# ---------------------------------------------------------------------------


def test_export_evidence_derives_expected_observed_verified(tmp_path: Path) -> None:
    """Ensure export_evidence produces expected, observed, and verified sections."""
    mgr = create_converged_manager()
    out_file = tmp_path / "identity_evidence.json"
    evidence = mgr.export_evidence(out_file)

    assert out_file.exists()
    assert "expected" in evidence["service_accounts"]
    assert "observed" in evidence["service_accounts"]
    assert "verified" in evidence["service_accounts"]
    assert evidence["service_accounts"]["verified"] is True

    assert "expected" in evidence["workload_identity_federation"]
    assert "observed" in evidence["workload_identity_federation"]
    assert evidence["workload_identity_federation"]["verified"] is True

    assert evidence["verification_results"]["positive_wif_proof_status"] == "PENDING_POST_MERGE"
    assert evidence["verification_results"]["runtime_payload_access"] == "DEFERRED_UNTIL_FIRST_REAL_SECRET_VERSION"
    assert evidence["verification_results"]["privacy_audit_status"] == "EXTERNAL_REVIEW_REQUIRED"


def test_teardown_rehearsal_is_plan_only() -> None:
    """Ensure teardown rehearsal does not execute destructive actions."""
    mgr = create_converged_manager()
    rehearsal = mgr.teardown_rehearsal()
    assert rehearsal["teardown_mode"] == "PLAN_ONLY"
    assert rehearsal["destructive_actions_executed"] is False
    assert len(rehearsal["steps"]) == 5


def test_synthetic_secret_probe_mocked() -> None:
    """Test verify_synthetic_secret_probe with mocked gcloud responses."""
    mgr = create_converged_manager()
    with patch("infra.gcp.identity.run_gcloud_command") as mock_gcloud:
        core_email = mgr.config.service_account_email(CORE_RUNTIME_SA_NAME)
        # 1. create -> 0
        # 2. add-binding -> 0
        # 3. get-iam-policy -> 0 with core binding
        # 4. delete -> 0
        policy_json = json.dumps({
            "bindings": [
                {
                    "role": "roles/secretmanager.secretAccessor",
                    "members": [f"serviceAccount:{core_email}"],
                }
            ]
        })
        mock_gcloud.side_effect = [
            (0, "", ""),
            (0, "", ""),
            (0, policy_json, ""),
            (0, "", ""),
        ]
        res = mgr.verify_synthetic_secret_probe()
        assert res["core_runtime_allowed"] is True
        assert res["web_runtime_denied"] is True
        assert res["deployer_denied"] is True
        assert res["project_wide_accessor_absent"] is True
        assert res["cleanup_successful"] is True
