"""Deterministic hero support-context builder (#176).

Derives the exactly-current-run ``HeroSupportContext`` from the real #54 context,
the #55 approved evidence, and the #56 package evidence binding. This supplies the
canonical proof VALUES the verifier compares a model reference against: record
field/values, deterministic finding details, and approved-evidence source/chunk
identity/provenance. It is framework-free and uses only application/domain value
objects.
"""

from __future__ import annotations

from ngabo.application.value_objects.canonical_binding import (
    CanonicalEvidence,
    CanonicalFinding,
)
from ngabo.application.value_objects.hero_support_context import HeroSupportContext
from ngabo.application.value_objects.investigation_execution import (
    EventInvocationResult,
)
from ngabo.application.value_objects.package_candidate_result import (
    PackageCandidateResult,
)
from ngabo.application.value_objects.triage_result import TriageResult


class HeroSupportContextBuilder:
    """Build the canonical support context for one hero run."""

    def build(
        self,
        investigation: EventInvocationResult,
        triage: TriageResult,
        synthesis: PackageCandidateResult,
    ) -> HeroSupportContext:
        joined = investigation.joined_investigation
        if joined is None:
            raise ValueError("investigation result lacks a joined context")
        capability = investigation.capability_result
        records: dict[str, dict[str, str]] = {}
        if capability is not None:
            for isolate in capability.isolates:
                records[isolate.isolate_id] = {
                    "organism_code": isolate.organism_code,
                    "organism_name": isolate.organism_name,
                    "facility_id": isolate.facility_id,
                    "ward": isolate.ward,
                    "lab_id": isolate.lab_id,
                }
        findings: dict[str, CanonicalFinding] = {}
        profile = joined.profile_result
        if profile is not None and profile.finding_reference is not None:
            ref = profile.finding_reference
            findings[ref.finding_id] = CanonicalFinding(
                finding_id=ref.finding_id,
                policy_version=ref.policy_version,
                input_refs=ref.input_refs,
                output_value=ref.output_value,
            )
        baseline = joined.baseline_result
        signal_eval = getattr(baseline, "signal_evaluation", None)
        signal = getattr(signal_eval, "signal", None)
        if signal is not None and getattr(signal, "signal_id", None):
            findings[signal.signal_id] = CanonicalFinding(
                finding_id=signal.signal_id,
                policy_version=getattr(signal, "policy_version", "v1"),
                input_refs=tuple(getattr(signal, "supporting_finding_refs", ())),
                output_value=getattr(signal, "output_value", ""),
            )

        evidence: dict[str, CanonicalEvidence] = {}
        evidence_result = triage.evidence_result
        corpus_id = (
            synthesis.package.metadata.evidence_binding.corpus_id
            if synthesis.package is not None
            else "ngabo-approved-evidence-v1"
        )
        if evidence_result is not None:
            for hit in evidence_result.hits:
                existing = evidence.get(hit.source_id.value)
                if existing is None:
                    evidence[hit.source_id.value] = CanonicalEvidence(
                        source_id=hit.source_id.value,
                        provenance=corpus_id,
                        chunk_ids=(hit.reference_id.value,),
                    )
                else:
                    evidence[hit.source_id.value] = CanonicalEvidence(
                        source_id=existing.source_id,
                        provenance=existing.provenance,
                        chunk_ids=existing.chunk_ids + (hit.reference_id.value,),
                    )
        return HeroSupportContext(
            incident_id=joined.incident_id,
            incident_version=joined.incident_version,
            source_watermark=joined.source_watermark,
            execution_id=str(investigation.execution_id),
            policy_config_version=joined.baseline_result.signal_evaluation.policy_config.policy_version
            if joined.baseline_result is not None
            and joined.baseline_result.signal_evaluation is not None
            else "v1",
            canonical_records=records,
            canonical_findings=findings,
            canonical_evidence=evidence,
            authorized_target_ids=frozenset(
                {"ngabo-demo-receiver-0001"}
            ),
        )
