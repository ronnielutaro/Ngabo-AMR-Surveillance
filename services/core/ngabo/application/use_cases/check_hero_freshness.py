"""Minimum freshness barrier for the deadline hero (#176).

Immediately before action authorization, re-check the current-state binding that
matters for the demo: incident id, version, source watermark, verified package
identity, and the governing policy/config version. If any changed since
verification, the hero blocks and never recomputes authorization from stale
proof. This is deliberately narrower than the full production freshness matrix
(#66).
"""

from __future__ import annotations

from ngabo.application.enums.hero_error_code import HeroErrorCode
from ngabo.application.value_objects.hero_support_context import HeroSupportContext
from ngabo.application.value_objects.incident_package import IncidentPackageCandidate


class CheckHeroFreshness:
    """Deterministic current-state binding check before action authorization."""

    def check(
        self,
        package: IncidentPackageCandidate,
        context: HeroSupportContext,
    ) -> tuple[bool, HeroErrorCode | None, str]:
        checks = (
            (
                package.incident_id.value == context.incident_id.value,
                HeroErrorCode.STALE_VERSION_BINDING,
                "incident_id changed since verification",
            ),
            (
                package.incident_version.value == context.incident_version.value,
                HeroErrorCode.STALE_VERSION_BINDING,
                "incident_version changed since verification",
            ),
            (
                package.source_watermark.value == context.source_watermark.value,
                HeroErrorCode.RUN_BINDING_MISMATCH,
                "source watermark changed since verification",
            ),
            (
                package.metadata.policy_config_version
                == context.policy_config_version,
                HeroErrorCode.STALE_VERSION_BINDING,
                "policy/config version changed since verification",
            ),
        )
        for ok, code, detail in checks:
            if not ok:
                return False, code, detail
        return True, None, "current-state binding holds"
