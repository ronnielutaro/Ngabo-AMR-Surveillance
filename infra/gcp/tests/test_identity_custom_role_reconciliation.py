"""Regression tests for Issue #90 custom-role reconciliation.

These tests cover the exact defects found in the final PR #116 review:
- a declared custom role must survive repeated identity apply runs;
- custom-role grantees are an exact allow-list, not a contains-at-least contract.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from infra.gcp.identity import GcpIdentityManager
from infra.gcp.identity_config import (
    CORE_RUNTIME_SA_NAME,
    DEPLOYER_SA_NAME,
    GITHUB_ISSUER,
    GITHUB_REPO_ID,
    SERVICE_ACCOUNTS,
    WEB_RUNTIME_SA_NAME,
    WIF_ATTRIBUTE_CONDITION,
    WIF_ATTRIBUTE_MAPPING,
    WIF_POOL_ID,
    WIF_PROVIDER_ID,
    GcpIdentityConfig,
)

PROJECT_ID = "ngabo-amr-2026"
PROJECT_NUMBER = "907313480935"
CUSTOM_ROLE = f"projects/{PROJECT_ID}/roles/ngaboRunServiceIam"
DEPLOYER_EMAIL = f"{DEPLOYER_SA_NAME}@{PROJECT_ID}.iam.gserviceaccount.com"
DEPLOYER_MEMBER = f"serviceAccount:{DEPLOYER_EMAIL}"
ATTACKER_MEMBER = "user:unexpected@example.com"


def _provider_details() -> dict[str, Any]:
    return {
        "name": (
            f"projects/{PROJECT_NUMBER}/locations/global/"
            f"workloadIdentityPools/{WIF_POOL_ID}/providers/{WIF_PROVIDER_ID}"
        ),
        "attributeMapping": WIF_ATTRIBUTE_MAPPING,
        "attributeCondition": WIF_ATTRIBUTE_CONDITION,
        "oidc": {"issuerUri": GITHUB_ISSUER},
        "state": "ACTIVE",
    }


def _project_bindings(*, extra_custom_member: bool = False) -> list[dict[str, Any]]:
    custom_members = [DEPLOYER_MEMBER]
    if extra_custom_member:
        custom_members.append(ATTACKER_MEMBER)
    return [
        {"role": "roles/run.developer", "members": [DEPLOYER_MEMBER]},
        {"role": CUSTOM_ROLE, "members": custom_members},
    ]


def _manager(*, extra_custom_member: bool = False) -> GcpIdentityManager:
    cfg = GcpIdentityConfig(project_id=PROJECT_ID, project_number=PROJECT_NUMBER)
    mgr = GcpIdentityManager(cfg)

    mgr.inspector.get_project_number = MagicMock(return_value=PROJECT_NUMBER)  # type: ignore[method-assign]
    mgr.inspector.service_account_exists = MagicMock(return_value=True)  # type: ignore[method-assign]
    mgr.inspector.get_user_managed_keys = MagicMock(return_value=[])  # type: ignore[method-assign]
    mgr.inspector.wif_pool_exists = MagicMock(return_value=True)  # type: ignore[method-assign]
    mgr.inspector.wif_provider_exists = MagicMock(return_value=True)  # type: ignore[method-assign]
    mgr.inspector.get_wif_provider_details = MagicMock(return_value=_provider_details())  # type: ignore[method-assign]
    mgr.inspector.get_project_iam_bindings = MagicMock(  # type: ignore[method-assign]
        return_value=_project_bindings(extra_custom_member=extra_custom_member)
    )
    mgr.inspector.get_artifact_registry_iam_bindings = MagicMock(  # type: ignore[method-assign]
        return_value=[
            {
                "role": "roles/artifactregistry.writer",
                "members": [DEPLOYER_MEMBER],
            }
        ]
    )
    mgr.inspector.get_all_project_service_accounts = MagicMock(  # type: ignore[method-assign]
        return_value=[{"email": mgr.config.service_account_email(sa)} for sa in SERVICE_ACCOUNTS]
    )
    mgr.inspector.custom_role_exists = MagicMock(return_value=True)  # type: ignore[method-assign]
    mgr.inspector.get_custom_role_permissions = MagicMock(  # type: ignore[method-assign]
        return_value=["run.services.setIamPolicy"]
    )

    runtime_binding = {
        "role": "roles/iam.serviceAccountUser",
        "members": [DEPLOYER_MEMBER],
    }
    wif_binding = {
        "role": "roles/iam.workloadIdentityUser",
        "members": [
            (
                f"principalSet://iam.googleapis.com/projects/{PROJECT_NUMBER}/"
                f"locations/global/workloadIdentityPools/{WIF_POOL_ID}/"
                f"attribute.repository_id/{GITHUB_REPO_ID}"
            )
        ],
    }

    def _sa_bindings(email: str) -> list[dict[str, Any]]:
        if email == DEPLOYER_EMAIL:
            return [wif_binding]
        if email in {
            mgr.config.service_account_email(CORE_RUNTIME_SA_NAME),
            mgr.config.service_account_email(WEB_RUNTIME_SA_NAME),
        }:
            return [runtime_binding]
        return []

    mgr.inspector.get_service_account_iam_bindings = MagicMock(  # type: ignore[method-assign]
        side_effect=_sa_bindings
    )

    mgr.github_manager.plan = MagicMock(  # type: ignore[method-assign]
        return_value={"is_converged": True, "planned_actions": []}
    )
    mgr.github_manager.validate = MagicMock(  # type: ignore[method-assign]
        return_value={"passed": True, "failures": [], "checks": {}}
    )
    mgr.github_manager.apply = MagicMock(  # type: ignore[method-assign]
        return_value={"success": True, "operations": []}
    )
    return mgr


def test_converged_plan_does_not_revoke_declared_custom_role() -> None:
    """A valid custom role is governed separately and must not look stale."""
    mgr = _manager()
    plan = mgr.plan()

    assert plan["is_converged"] is True, plan["planned_actions"]
    assert not any("ngaboRunServiceIam" in action for action in plan["planned_actions"])


def test_validate_rejects_unexpected_custom_role_grantee() -> None:
    """Any grantee outside grant_to makes the IAM state fail closed."""
    mgr = _manager(extra_custom_member=True)
    result = mgr.validate()

    assert result["passed"] is False
    assert result["checks"]["custom_roles_valid"] is False
    assert any(
        "unexpected members" in failure and ATTACKER_MEMBER in failure
        for failure in result["failures"]
    )


def test_repeated_apply_on_converged_state_is_true_noop() -> None:
    """The second identity apply must preserve the custom role and mutate nothing."""
    mgr = _manager()
    mgr.export_evidence = MagicMock(return_value={})  # type: ignore[method-assign]

    with patch("infra.gcp.identity.run_gcloud_command") as mock_gcloud:
        result = mgr.apply()

    assert result["success"] is True
    assert result["noop"] is True
    assert result["operations"] == []
    mock_gcloud.assert_not_called()


def test_apply_removes_unexpected_custom_role_grantee() -> None:
    """Apply reconciles extra custom-role members instead of certifying them."""
    mgr = _manager(extra_custom_member=True)
    mgr.validate = MagicMock(  # type: ignore[method-assign]
        return_value={"passed": True, "failures": [], "checks": {}}
    )
    mgr.export_evidence = MagicMock(return_value={})  # type: ignore[method-assign]

    with patch(
        "infra.gcp.identity.run_gcloud_command",
        return_value=(0, "", ""),
    ) as mock_gcloud:
        result = mgr.apply()

    removal_commands = [
        call.args[0]
        for call in mock_gcloud.call_args_list
        if call.args
        and call.args[0][:2] == ["projects", "remove-iam-policy-binding"]
    ]
    assert removal_commands == [
        [
            "projects",
            "remove-iam-policy-binding",
            PROJECT_ID,
            f"--member={ATTACKER_MEMBER}",
            f"--role={CUSTOM_ROLE}",
            "--all",
        ]
    ]
    assert any("Revoked unexpected custom role member" in op for op in result["operations"])
