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
from ngabo.domain.events.investigation_priority_signal_event import (
    DEFAULT_SIGNAL_EVENT_CONTRACT_VERSION,
    DEFAULT_SIGNAL_EVENT_TYPE,
    InvestigationPrioritySignalEvent,
)
from ngabo.domain.value_objects.deterministic_finding_evidence import (
    DeterministicFindingEvidence,
)
from ngabo.domain.value_objects.investigation_priority_signal import (
    InvestigationPrioritySignal,
)

GOVERNED_HERO_SIGNAL_ID = "sig-c4180061263e7207"
GOVERNED_HERO_EVENT_ID = "evt-a44635c546dfc667"
GOVERNED_HERO_EVENT_TYPE = DEFAULT_SIGNAL_EVENT_TYPE
GOVERNED_HERO_EVENT_CONTRACT = DEFAULT_SIGNAL_EVENT_CONTRACT_VERSION
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
GOVERNED_HERO_IMPORTED_RECORD_IDS = (
    "ISO-012",
    "ISO-027",
    "ISO-031",
    "ISO-034",
    "ISO-039",
    "ISO-052",
    "ISO-063",
    "ISO-071",
)
PRIMARY_INVARIANT_NOTICE = (
    "INVESTIGATION_PRIORITY_SIGNAL only; never an outbreak declaration, "
    "diagnosis, model confidence, or clinical decision."
)
DEFAULT_LOGICAL_HERO_LOCATOR = "data/synthetic/canonical_hero.csv"


@dataclass(frozen=True)
class OfflineHeroCertificationResult:
    """Immutable, machine-verifiable offline release gate certification result.

    Distinguishes deterministic execution success (execution_succeeded) from
    canonical hero release certification (certified).
    """

    execution_succeeded: bool
    certified: bool
    input_location: str
    raw_source_digest: str | None
    source_watermark: str | None
    import_disposition: ImportOutcomeDisposition | None
    imported_record_count: int
    imported_record_ids: tuple[str, ...]
    exact_duplicate_count: int
    signal_count: int
    signals: tuple[InvestigationPrioritySignal, ...]
    policy_version: str
    config_version: str
    algorithm_version: str
    event: InvestigationPrioritySignalEvent | None = None
    event_id: str | None = None
    event_contract_version: str = DEFAULT_SIGNAL_EVENT_CONTRACT_VERSION
    finding_evidence: tuple[DeterministicFindingEvidence, ...] = ()
    errors: tuple[str, ...] = ()
    model_required: bool = False
    network_required: bool = False
    cloud_required: bool = False
    human_intervention_required: bool = False
    autonomous_external_actions: int = 0
    model_calls: int = 0
    network_calls: int = 0
    cloud_calls: int = 0
    human_prompts: int = 0
    human_interventions: int = 0
    clarifications: int = 0
    approvals: int = 0
    primary_invariant: str = PRIMARY_INVARIANT_NOTICE

    def __post_init__(self) -> None:
        if self.imported_record_count != len(self.imported_record_ids):
            raise ValueError(
                f"imported_record_count ({self.imported_record_count}) must match "
                f"imported_record_ids length ({len(self.imported_record_ids)})"
            )
        if self.signal_count != len(self.signals):
            raise ValueError(
                f"signal_count ({self.signal_count}) must match "
                f"signals length ({len(self.signals)})"
            )

        if not self.execution_succeeded and self.certified:
            raise ValueError("certified cannot be True when execution_succeeded is False")

        if self.event is not None and self.event_id != self.event.event_id:
            raise ValueError(
                f"event_id ({self.event_id}) must match event.event_id ({self.event.event_id})"
            )

        if self.certified:
            if not self.execution_succeeded:
                raise ValueError("certified requires execution_succeeded=True")
            if self.errors:
                raise ValueError("certified requires errors to be empty")
            if self.signal_count != 1 or len(self.signals) != 1 or self.hero_signal is None:
                raise ValueError("certified requires exactly one hero signal")
            if self.event is None:
                raise ValueError("certified requires a non-null event")

            sig = self.hero_signal
            if self.event.signal_id != sig.signal_id:
                raise ValueError(
                    f"event.signal_id ({self.event.signal_id}) must match "
                    f"hero_signal.signal_id ({sig.signal_id})"
                )
            if self.event.source_watermark != self.source_watermark:
                raise ValueError(
                    f"event.source_watermark ({self.event.source_watermark}) must match "
                    f"source_watermark ({self.source_watermark})"
                )
            if self.event.facility_id != sig.facility_id:
                raise ValueError("event.facility_id must match hero_signal.facility_id")
            if self.event.ward != sig.ward:
                raise ValueError("event.ward must match hero_signal.ward")
            if self.event.organism_code != sig.organism_code:
                raise ValueError("event.organism_code must match hero_signal.organism_code")
            if self.event.window_start != sig.window_start:
                raise ValueError("event.window_start must match hero_signal.window_start")
            if self.event.window_end != sig.window_end:
                raise ValueError("event.window_end must match hero_signal.window_end")
            if self.event.signal_score != sig.signal_score:
                raise ValueError("event.signal_score must match hero_signal.signal_score")
            if self.event.policy_version != sig.policy_version:
                raise ValueError("event.policy_version must match hero_signal.policy_version")
            if self.event.config_version != sig.config_version:
                raise ValueError("event.config_version must match hero_signal.config_version")
            if self.event.algorithm_version != sig.algorithm_version:
                raise ValueError("event.algorithm_version must match hero_signal.algorithm_version")
            if self.event.supporting_finding_refs != sig.supporting_finding_refs:
                raise ValueError(
                    "event.supporting_finding_refs must match hero_signal.supporting_finding_refs"
                )
            if self.event.supporting_isolate_refs != sig.supporting_isolate_refs:
                raise ValueError(
                    "event.supporting_isolate_refs must match hero_signal.supporting_isolate_refs"
                )
            if self.event.contract_version != self.event_contract_version:
                raise ValueError(
                    "event.contract_version must match result.event_contract_version"
                )

            # Finding evidence manifest consistency
            expected_evidence = sig.to_finding_evidence()
            if self.finding_evidence != expected_evidence:
                raise ValueError(
                    "finding_evidence must exactly match hero_signal.to_finding_evidence()"
                )
            if not self.finding_evidence:
                raise ValueError("certified requires non-empty finding_evidence manifest")
            evidence_finding_ids = tuple(f.finding_id for f in self.finding_evidence)
            if evidence_finding_ids != sig.supporting_finding_refs:
                raise ValueError(
                    f"finding_evidence IDs {evidence_finding_ids!r} must match "
                    f"supporting_finding_refs {sig.supporting_finding_refs!r}"
                )

            if not self.verify_hero_expectations():
                raise ValueError("certified requires all canonical hero expectations to pass")

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
        if not self.execution_succeeded:
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
        if self.imported_record_count != 8:
            return False
        if self.imported_record_ids != GOVERNED_HERO_IMPORTED_RECORD_IDS:
            return False
        if self.import_disposition not in (
            ImportOutcomeDisposition.FIRST_IMPORT,
            ImportOutcomeDisposition.EXACT_REPLAY,
        ):
            return False

        # Full event contract and semantic agreement verification
        if self.event is None:
            return False
        if self.event_id != self.event.event_id:
            return False
        if self.event.event_id != GOVERNED_HERO_EVENT_ID:
            return False
        if self.event.event_type != GOVERNED_HERO_EVENT_TYPE:
            return False
        if self.event.contract_version != GOVERNED_HERO_EVENT_CONTRACT:
            return False
        if self.event.signal_id != sig.signal_id:
            return False
        if self.event.source_watermark != self.source_watermark:
            return False
        if self.event.facility_id != sig.facility_id:
            return False
        if self.event.ward != sig.ward:
            return False
        if self.event.organism_code != sig.organism_code:
            return False
        if self.event.window_start != sig.window_start:
            return False
        if self.event.window_end != sig.window_end:
            return False
        if self.event.signal_score != sig.signal_score:
            return False
        if self.event.policy_version != sig.policy_version:
            return False
        if self.event.config_version != sig.config_version:
            return False
        if self.event.algorithm_version != sig.algorithm_version:
            return False
        if self.event.supporting_finding_refs != sig.supporting_finding_refs:
            return False
        if self.event.supporting_isolate_refs != sig.supporting_isolate_refs:
            return False

        # Finding evidence manifest verification
        if not self.finding_evidence:
            return False
        if self.finding_evidence != sig.to_finding_evidence():
            return False
        if tuple(f.finding_id for f in self.finding_evidence) != sig.supporting_finding_refs:
            return False

        if (
            self.model_required
            or self.network_required
            or self.cloud_required
            or self.human_intervention_required
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
            "execution_succeeded": self.execution_succeeded,
            "input_valid": self.execution_succeeded and len(self.errors) == 0,
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
            "imported_record_ids": list(self.imported_record_ids),
            "exact_duplicate_count": self.exact_duplicate_count,
            "signal_count": self.signal_count,
            "signal_id": self.hero_signal_id,
            "signal_score": self.hero_signal_score,
            "components": self.hero_components,
            "supporting_finding_refs": list(sig.supporting_finding_refs) if sig else [],
            "supporting_isolate_refs": list(sig.supporting_isolate_refs) if sig else [],
            "finding_evidence": [f.to_dict() for f in self.finding_evidence],
            "event": self.event.to_dict() if self.event else None,
            "event_id": self.event_id,
            "policy_version": self.policy_version,
            "config_version": self.config_version,
            "algorithm_version": self.algorithm_version,
            "event_contract_version": self.event_contract_version,
            "model_required": self.model_required,
            "network_required": self.network_required,
            "cloud_required": self.cloud_required,
            "human_intervention_required": self.human_intervention_required,
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
