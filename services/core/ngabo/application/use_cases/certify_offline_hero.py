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
from ngabo.application.ports.load_import_source import LoadImportSource
from ngabo.application.ports.parse_canonical_source import ParseCanonicalSource
from ngabo.application.ports.source_replay_repository import SourceReplayRepository
from ngabo.application.use_cases.orchestrate_canonical_import import (
    OrchestrateCanonicalImport,
)
from ngabo.application.value_objects.offline_hero_certification_result import (
    OfflineHeroCertificationResult,
)
from ngabo.domain.services.signal_detection import evaluate_surveillance_signals
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

    def execute(
        self, command: CertifyOfflineHeroCommand | None = None
    ) -> OfflineHeroCertificationResult:
        """Execute complete offline deterministic pipeline from input to signal candidates.

        Steps:
        1. Resolve source location, source key, surveillance window, and config.
        2. Execute canonical import orchestration (read -> digest -> parse -> dedup -> watermark).
        3. Fail closed if import does not produce a valid batch.
        4. Pass canonical isolates to deterministic signal detection (profile similarity,
           concentration analysis, synthetic baseline comparison, composite scoring).
        5. Return typed OfflineHeroCertificationResult.
        """
        cmd = command if command is not None else CertifyOfflineHeroCommand()
        if not isinstance(cmd, CertifyOfflineHeroCommand):
            raise TypeError(
                f"command must be a CertifyOfflineHeroCommand; got {type(cmd).__name__}"
            )

        cfg = cmd.signal_config or SignalConfig()
        loc = cmd.resolved_location()

        # Step 2: Canonical import orchestration
        import_cmd = ImportCanonicalSourceCommand(
            source_key=cmd.source_key,
            source_location=loc,
        )
        import_res = self._import_orchestrator.execute(import_cmd)

        if not import_res.success or import_res.batch is None:
            err_msgs = tuple(f"{e.code.value}: {e.message}" for e in import_res.errors)
            return OfflineHeroCertificationResult(
                certified=False,
                input_location=loc,
                raw_source_digest=(
                    str(import_res.raw_digest) if import_res.raw_digest else None
                ),
                source_watermark=(
                    str(import_res.watermark) if import_res.watermark else None
                ),
                import_disposition=import_res.disposition,
                imported_record_count=0,
                exact_duplicate_count=len(import_res.exact_duplicates),
                signal_count=0,
                signals=(),
                policy_version=cfg.policy_version,
                config_version=cfg.config_version,
                algorithm_version=cfg.algorithm_version,
                errors=err_msgs,
            )

        # Step 4: Deterministic surveillance signal detection
        records = import_res.batch.records
        signals = evaluate_surveillance_signals(
            isolates=records,
            window_end=cmd.window_end,
            config=cfg,
        )

        return OfflineHeroCertificationResult(
            certified=True,
            input_location=loc,
            raw_source_digest=str(import_res.raw_digest) if import_res.raw_digest else None,
            source_watermark=str(import_res.watermark) if import_res.watermark else None,
            import_disposition=import_res.disposition,
            imported_record_count=len(records),
            exact_duplicate_count=len(import_res.exact_duplicates),
            signal_count=len(signals),
            signals=signals,
            policy_version=cfg.policy_version,
            config_version=cfg.config_version,
            algorithm_version=cfg.algorithm_version,
            errors=(),
        )

    def __call__(
        self, command: CertifyOfflineHeroCommand | None = None
    ) -> OfflineHeroCertificationResult:
        """Callable protocol support."""
        return self.execute(command)
