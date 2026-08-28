"""Application use case for certifying the offline hero surveillance release gate (Issue #48).

Primary Invariant: The certified output is strictly an INVESTIGATION_PRIORITY_SIGNAL.
It is NEVER an outbreak declaration, outbreak probability, diagnosis, model confidence,
clinical decision, or prescribing/treatment guidance.
"""

from __future__ import annotations

import logging

from ngabo.application.commands.certify_offline_hero_command import (
    CertifyOfflineHeroCommand,
)
from ngabo.application.commands.import_canonical_source_command import (
    ImportCanonicalSourceCommand,
)
from ngabo.application.enums.import_outcome_disposition import ImportOutcomeDisposition
from ngabo.application.ports.load_import_source import LoadImportSource
from ngabo.application.ports.parse_canonical_source import ParseCanonicalSource
from ngabo.application.ports.source_replay_repository import SourceReplayRepository
from ngabo.application.use_cases.orchestrate_canonical_import import (
    OrchestrateCanonicalImport,
)
from ngabo.application.value_objects.offline_hero_certification_result import (
    GOVERNED_HERO_COMPONENTS,
    GOVERNED_HERO_IMPORTED_RECORD_IDS,
    GOVERNED_HERO_RAW_DIGEST,
    GOVERNED_HERO_SCORE,
    GOVERNED_HERO_SIGNAL_ID,
    GOVERNED_HERO_WATERMARK,
    OfflineHeroCertificationResult,
)
from ngabo.domain.events.investigation_priority_signal_event import (
    create_investigation_priority_signal_event,
)
from ngabo.domain.services.signal_detection import evaluate_surveillance_signals
from ngabo.domain.value_objects.deterministic_finding_evidence import (
    DeterministicFindingEvidence,
)
from ngabo.domain.value_objects.signal_config import SignalConfig

logger = logging.getLogger(__name__)


class CertifyOfflineHero:
    """Framework-free application use case orchestrating offline hero certification."""

    def __init__(
        self,
        source_loader: LoadImportSource,
        replay_repo: SourceReplayRepository,
        parser: ParseCanonicalSource,
    ) -> None:
        if not callable(source_loader):
            raise TypeError(f"Invalid source_loader {source_loader!r}; expected callable")
        if not hasattr(replay_repo, "accept_watermark"):
            raise TypeError(
                f"Invalid replay_repo {replay_repo!r}; expected SourceReplayRepository"
            )
        if not callable(parser):
            raise TypeError(f"Invalid parser {parser!r}; expected callable ParseCanonicalSource")

        self._source_loader = source_loader
        self._replay_repo = replay_repo
        self._parser = parser
        self._import_orchestrator = OrchestrateCanonicalImport(
            source_loader=self._source_loader,
            replay_repo=self._replay_repo,
            parser=self._parser,
        )

    def execute(self, command: CertifyOfflineHeroCommand) -> OfflineHeroCertificationResult:
        """Execute complete offline deterministic pipeline from input to signal candidates.

        Steps:
        1. Resolve source location, source key, surveillance window, and config.
        2. Execute canonical import orchestration (read -> digest -> parse -> dedup -> watermark).
        3. Fail closed if import does not produce a valid batch.
        4. Pass canonical isolates to deterministic signal detection (profile similarity,
           concentration analysis, synthetic baseline comparison, composite scoring).
        5. Create deterministic signal event if signal triggers.
        6. Return typed OfflineHeroCertificationResult distinguishing execution success
           from canonical hero release certification.
        """
        if not isinstance(command, CertifyOfflineHeroCommand):
            raise TypeError(
                f"command must be a CertifyOfflineHeroCommand; got {type(command).__name__}"
            )

        cfg = command.signal_config or SignalConfig()
        loc = command.source_location
        logical_loc = command.resolved_logical_locator

        # Step 2: Canonical import orchestration
        import_cmd = ImportCanonicalSourceCommand(
            source_key=command.source_key,
            source_location=loc,
        )
        import_res = self._import_orchestrator.execute(import_cmd)

        if not import_res.success or import_res.batch is None:
            err_msgs = tuple(f"{e.code.value}: {e.message}" for e in import_res.errors)
            return OfflineHeroCertificationResult(
                execution_succeeded=False,
                certified=False,
                input_location=logical_loc,
                raw_source_digest=(
                    str(import_res.raw_digest) if import_res.raw_digest else None
                ),
                source_watermark=(
                    str(import_res.watermark) if import_res.watermark else None
                ),
                import_disposition=import_res.disposition,
                imported_record_count=0,
                imported_record_ids=(),
                exact_duplicate_count=len(import_res.exact_duplicates),
                signal_count=0,
                signals=(),
                policy_version=cfg.policy_version,
                config_version=cfg.config_version,
                algorithm_version=cfg.algorithm_version,
                event=None,
                event_id=None,
                finding_evidence=(),
                errors=err_msgs,
            )

        # Step 4: Deterministic surveillance signal detection
        records = import_res.batch.records
        record_ids = tuple(sorted(r.isolate_id for r in records))
        signals = evaluate_surveillance_signals(
            isolates=records,
            window_end=command.window_end,
            config=cfg,
        )

        raw_digest_str = str(import_res.raw_digest) if import_res.raw_digest else None
        watermark_str = str(import_res.watermark) if import_res.watermark else None

        # Step 5: Deterministic signal event and finding evidence
        event = None
        event_id = None
        finding_evidence: tuple[DeterministicFindingEvidence, ...] = ()
        if len(signals) == 1 and watermark_str is not None:
            hero_sig = signals[0]
            event = create_investigation_priority_signal_event(
                signal=hero_sig,
                source_watermark=watermark_str,
            )
            event_id = event.event_id
            finding_evidence = hero_sig.to_finding_evidence()

        # Step 6: Verify canonical hero release invariants
        components_match = (
            len(signals) == 1
            and signals[0].components.c_phenotype == GOVERNED_HERO_COMPONENTS["c_phenotype"]
            and signals[0].components.c_location == GOVERNED_HERO_COMPONENTS["c_location"]
            and signals[0].components.c_temporal == GOVERNED_HERO_COMPONENTS["c_temporal"]
            and signals[0].components.c_baseline == GOVERNED_HERO_COMPONENTS["c_baseline"]
        )
        is_hero = (
            len(signals) == 1
            and signals[0].signal_id == GOVERNED_HERO_SIGNAL_ID
            and signals[0].signal_score == GOVERNED_HERO_SCORE
            and components_match
            and raw_digest_str == GOVERNED_HERO_RAW_DIGEST
            and watermark_str == GOVERNED_HERO_WATERMARK
            and len(records) == 8
            and record_ids == GOVERNED_HERO_IMPORTED_RECORD_IDS
            and event is not None
            and import_res.disposition in (
                ImportOutcomeDisposition.FIRST_IMPORT,
                ImportOutcomeDisposition.EXACT_REPLAY,
            )
        )

        return OfflineHeroCertificationResult(
            execution_succeeded=True,
            certified=is_hero,
            input_location=logical_loc,
            raw_source_digest=raw_digest_str,
            source_watermark=watermark_str,
            import_disposition=import_res.disposition,
            imported_record_count=len(records),
            imported_record_ids=record_ids,
            exact_duplicate_count=len(import_res.exact_duplicates),
            signal_count=len(signals),
            signals=signals,
            policy_version=cfg.policy_version,
            config_version=cfg.config_version,
            algorithm_version=cfg.algorithm_version,
            event=event,
            event_id=event_id,
            finding_evidence=finding_evidence,
            errors=(),
        )

    def __call__(self, command: CertifyOfflineHeroCommand) -> OfflineHeroCertificationResult:
        """Callable protocol support."""
        return self.execute(command)
