"""Typed certification result for the offline hero input-to-signal release gate (Issue #48).

Primary Invariant: The certified output is strictly an INVESTIGATION_PRIORITY_SIGNAL.
It is NEVER an outbreak declaration, outbreak probability, diagnosis, model confidence,
clinical decision, or prescribing/treatment guidance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ngabo.application.enums.import_outcome_disposition import ImportOutcomeDisposition
from ngabo.domain.enums.signal_status import SignalReason, SignalStatus
from ngabo.domain.value_objects.investigation_priority_signal import (
    InvestigationPrioritySignal,
)

GOVERNED_HERO_SIGNAL_ID = "sig-c4180061263e7207"
GOVERNED_HERO_SCORE = 0.9375
GOVERNED_HERO_RAW_DIGEST = (
    "sha256:6b6bbc9a8d1f0e44419aee4ed4bdd073d965bab7507961307dcd051b4dae926b"
)
GOVERNED_HERO_WATERMARK = (
    "ngabo-source-v1:sha256:b1b00a5938f2515c77cf144ec4bf5731bcaa9406265996941818f914567cd94c"
)
GOVERNED_HERO_COMPONENTS = {
    "c_phenotype": 1.0,
    "c_location": 0.75,
    "c_temporal": 1.0,
    "c_baseline": 1.0,
}
PRIMARY_INVARIANT_NOTICE = (
    "INVESTIGATION_PRIORITY_SIGNAL only; never an outbreak declaration, "
    "diagnosis, model confidence, or clinical decision."
)


@dataclass(frozen=True)
class OfflineHeroCertificationResult:
    """Immutable, machine-verifiable offline release gate certification result."""

    certified: bool
    input_location: str
    raw_source_digest: str | None
    source_watermark: str | None
    import_disposition: ImportOutcomeDisposition | None
    imported_record_count: int
    exact_duplicate_count: int
    signal_count: int
    signals: tuple[InvestigationPrioritySignal, ...]
    policy_version: str
    config_version: str
    algorithm_version: str
    errors: tuple[str, ...] = ()
    autonomous_external_actions: int = 0
    model_calls: int = 0
    network_calls: int = 0
    cloud_calls: int = 0
    human_prompts: int = 0
    human_interventions: int = 0
    clarifications: int = 0
    approvals: int = 0
    primary_invariant: str = PRIMARY_INVARIANT_NOTICE

    @property
    def hero_signal(self) -> InvestigationPrioritySignal | None:
        """Convenience accessor for the single hero signal, if exactly one signal was emitted."""
        if len(self.signals) == 1:
            return self.signals[0]
        return None

    @property
    def hero_signal_id(self) -> str | None:
        """Signal ID of hero signal if emitted."""
        sig = self.hero_signal
        return sig.signal_id if sig is not None else None

    @property
    def hero_signal_score(self) -> float | None:
        """Signal score of hero signal if emitted."""
        sig = self.hero_signal
        return sig.signal_score if sig is not None else None

    @property
    def hero_components(self) -> dict[str, float] | None:
        """Component dictionary of hero signal if emitted."""
        sig = self.hero_signal
        if sig is None:
            return None
        return {
            "c_phenotype": sig.components.c_phenotype,
            "c_location": sig.components.c_location,
            "c_temporal": sig.components.c_temporal,
            "c_baseline": sig.components.c_baseline,
        }

    def verify_hero_expectations(self) -> bool:
        """Verify that this result satisfies all canonical hero release invariants."""
        if not self.certified:
            return False
        if self.signal_count != 1 or self.hero_signal is None:
            return False
        sig = self.hero_signal
        if sig.signal_id != GOVERNED_HERO_SIGNAL_ID:
            return False
        if sig.signal_score != GOVERNED_HERO_SCORE:
            return False
        if self.hero_components != GOVERNED_HERO_COMPONENTS:
            return False
        if sig.ward != "SYNTH-WARD-A" or sig.organism_code != "kle":
            return False
        if sig.facility_id != "SYNTH-FACILITY-001":
            return False
        if sig.status != SignalStatus.TRIGGERED:
            return False
        if sig.reason != SignalReason.HIGH_PRIORITY_CLUSTER:
            return False
        if self.raw_source_digest != GOVERNED_HERO_RAW_DIGEST:
            return False
        if self.source_watermark != GOVERNED_HERO_WATERMARK:
            return False
        if self.import_disposition not in (
            ImportOutcomeDisposition.FIRST_IMPORT,
            ImportOutcomeDisposition.EXACT_REPLAY,
        ):
            return False
        return not (
            self.autonomous_external_actions != 0
            or self.model_calls != 0
            or self.network_calls != 0
            or self.cloud_calls != 0
            or self.human_prompts != 0
            or self.human_interventions != 0
            or self.clarifications != 0
            or self.approvals != 0
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert certification outcome to a structured JSON-serializable dictionary."""
        sig = self.hero_signal
        cert_data: dict[str, Any] = {
            "certified": self.certified,
            "input_valid": self.certified and len(self.errors) == 0,
            "deterministic_import": self.import_disposition in (
                ImportOutcomeDisposition.FIRST_IMPORT,
                ImportOutcomeDisposition.EXACT_REPLAY,
            ),
            "input_location": self.input_location,
            "raw_source_digest": self.raw_source_digest,
            "source_watermark": self.source_watermark,
            "import_disposition": (
                self.import_disposition.value if self.import_disposition else None
            ),
            "imported_record_count": self.imported_record_count,
            "exact_duplicate_count": self.exact_duplicate_count,
            "signal_count": self.signal_count,
            "signal_id": self.hero_signal_id,
            "signal_score": self.hero_signal_score,
            "components": self.hero_components,
            "supporting_finding_refs": list(sig.supporting_finding_refs) if sig else [],
            "supporting_isolate_refs": list(sig.supporting_isolate_refs) if sig else [],
            "policy_version": self.policy_version,
            "config_version": self.config_version,
            "algorithm_version": self.algorithm_version,
            "autonomous_external_actions": self.autonomous_external_actions,
            "model_calls": self.model_calls,
            "network_calls": self.network_calls,
            "cloud_calls": self.cloud_calls,
            "human_prompts": self.human_prompts,
            "human_interventions": self.human_interventions,
            "clarifications": self.clarifications,
            "approvals": self.approvals,
            "primary_invariant": self.primary_invariant,
        }
        if self.errors:
            cert_data["errors"] = list(self.errors)
        return {"hero_certification": cert_data}

    def to_json(self, indent: int = 2) -> str:
        """Serialize certification result to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
