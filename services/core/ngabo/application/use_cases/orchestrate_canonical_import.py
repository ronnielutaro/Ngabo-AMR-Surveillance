"""Application use case for orchestrating canonical import and replay (Issue #44)."""

from __future__ import annotations

import logging

from ngabo.application.commands.import_canonical_source_command import (
    ImportCanonicalSourceCommand,
)
from ngabo.application.enums.import_error_code import ImportErrorCode
from ngabo.application.enums.import_outcome_disposition import ImportOutcomeDisposition
from ngabo.application.ports.load_import_source import LoadImportSource
from ngabo.application.ports.parse_canonical_source import ParseCanonicalSource
from ngabo.application.ports.source_replay_repository import SourceReplayRepository
from ngabo.application.value_objects.canonical_import_result import (
    CanonicalImportResult,
)
from ngabo.application.value_objects.import_error_detail import ImportErrorDetail
from ngabo.domain.services.import_deduplication import deduplicate_canonical_batch
from ngabo.domain.services.source_identity import compute_raw_source_digest

logger = logging.getLogger(__name__)


class OrchestrateCanonicalImport:
    """Framework-free use case composing deterministic import and replay validation."""

    def __init__(
        self,
        source_loader: LoadImportSource,
        replay_repo: SourceReplayRepository,
        parser: ParseCanonicalSource,
    ) -> None:
        if not callable(source_loader):
            raise TypeError(f"Invalid source_loader {source_loader!r}; expected callable")
        if not hasattr(replay_repo, "get_previous_watermark"):
            raise TypeError(
                f"Invalid replay_repo {replay_repo!r}; expected SourceReplayRepository"
            )
        if not callable(parser):
            raise TypeError(f"Invalid parser {parser!r}; expected callable ParseCanonicalSource")
        self._source_loader = source_loader
        self._replay_repo = replay_repo
        self._parser = parser

    def execute(self, command: ImportCanonicalSourceCommand) -> CanonicalImportResult:
        """Execute canonical import workflow.

        Execution order:
        1. Load raw artifact bytes via ``source_loader(command.source_location)``.
           Fails closed with ``SOURCE_READ_ERROR`` (raw_digest is None).
        2. Compute raw artifact SHA-256 digest via ``compute_raw_source_digest(raw_bytes)``.
        3. Decode raw bytes strictly as UTF-8 (``bytes(raw_bytes).decode('utf-8')``).
           Fails closed with ``UTF8_DECODE_ERROR`` (raw_digest preserved).
        4. Parse CSV & validate canonical records via ``parser(csv_text)``.
           Fails closed with ``PARSER_FAILURE`` (raw_digest preserved).
        5. Deduplicate batch & compute source watermark via ``deduplicate_canonical_batch(batch)``.
           Fails closed with ``CONFLICTING_DUPLICATE_RECORD`` (raw_digest preserved).
        6. Query previous watermark from ``replay_repo.get_previous_watermark(command.source_key)``.
           Fails closed with ``REPOSITORY_ERROR`` if repository read fails (raw_digest preserved).
        7. Determine disposition:
           - ``FIRST_IMPORT`` if previous watermark is None;
           - ``EXACT_REPLAY`` if previous watermark equals current watermark;
           - ``MATERIAL_CHANGE`` if previous watermark differs from current watermark.
        8. Return immutable ``CanonicalImportResult``.
        """
        if not isinstance(command, ImportCanonicalSourceCommand):
            raise TypeError(
                f"Invalid command {command!r}; expected ImportCanonicalSourceCommand"
            )

        # Step 1: Load raw artifact bytes
        try:
            raw_bytes = self._source_loader(command.source_location)
        except Exception as exc:
            logger.warning("Source load failed for %s: %s", command.source_location, exc)
            return CanonicalImportResult(
                success=False,
                disposition=ImportOutcomeDisposition.FAILED,
                source_key=command.source_key,
                raw_digest=None,
                watermark=None,
                batch=None,
                exact_duplicates=(),
                errors=(
                    ImportErrorDetail(
                        code=ImportErrorCode.SOURCE_READ_ERROR,
                        message=f"Failed to load source from {command.source_location!r}: {exc}",
                    ),
                ),
            )

        if not isinstance(raw_bytes, (bytes, bytearray)):
            return CanonicalImportResult(
                success=False,
                disposition=ImportOutcomeDisposition.FAILED,
                source_key=command.source_key,
                raw_digest=None,
                watermark=None,
                batch=None,
                exact_duplicates=(),
                errors=(
                    ImportErrorDetail(
                        code=ImportErrorCode.SOURCE_READ_ERROR,
                        message=f"Source loader returned {type(raw_bytes)!r}; expected bytes",
                    ),
                ),
            )

        # Step 2: Compute raw source digest BEFORE decoding
        raw_digest = compute_raw_source_digest(raw_bytes)

        # Step 3: Strict UTF-8 decoding
        try:
            csv_text = bytes(raw_bytes).decode("utf-8")
        except UnicodeDecodeError as exc:
            return CanonicalImportResult(
                success=False,
                disposition=ImportOutcomeDisposition.FAILED,
                source_key=command.source_key,
                raw_digest=raw_digest,
                watermark=None,
                batch=None,
                exact_duplicates=(),
                errors=(
                    ImportErrorDetail(
                        code=ImportErrorCode.UTF8_DECODE_ERROR,
                        message=(
                            f"Source bytes for {command.source_key!r} "
                            f"are not valid UTF-8: {exc}"
                        ),
                    ),
                ),
            )

        # Step 4: CSV parsing & canonical validation
        parsed = self._parser(csv_text)
        if not parsed.success or parsed.batch is None:
            parser_errors = tuple(
                ImportErrorDetail(
                    code=ImportErrorCode.PARSER_FAILURE,
                    message=err.detail or "CSV parsing or canonical validation failed",
                    field=err.column,
                    line_number=err.row_number,
                    isolate_id=err.record_id,
                )
                for err in parsed.errors
            )
            return CanonicalImportResult(
                success=False,
                disposition=ImportOutcomeDisposition.FAILED,
                source_key=command.source_key,
                raw_digest=raw_digest,
                watermark=None,
                batch=None,
                exact_duplicates=(),
                errors=parser_errors
                if parser_errors
                else (
                    ImportErrorDetail(
                        code=ImportErrorCode.PARSER_FAILURE,
                        message="CSV parser reported failure without error details",
                    ),
                ),
            )

        # Step 5: Deduplication & conflict detection gate
        dedup_report = deduplicate_canonical_batch(parsed.batch)
        if not dedup_report.success or dedup_report.batch is None or dedup_report.watermark is None:
            conflict_errors = tuple(
                ImportErrorDetail(
                    code=ImportErrorCode.CONFLICTING_DUPLICATE_RECORD,
                    message=err.detail or f"Conflicting duplicate isolate_id: {err.isolate_id!r}",
                    isolate_id=err.isolate_id,
                    indices=err.indices,
                    differing_fields=err.differing_fields,
                )
                for err in dedup_report.errors
            )
            return CanonicalImportResult(
                success=False,
                disposition=ImportOutcomeDisposition.FAILED,
                source_key=command.source_key,
                raw_digest=raw_digest,
                watermark=None,
                batch=None,
                exact_duplicates=dedup_report.exact_duplicates,
                errors=conflict_errors,
            )

        # Step 6: Query previous watermark from replay repository
        try:
            previous_watermark = self._replay_repo.get_previous_watermark(command.source_key)
        except Exception as exc:
            return CanonicalImportResult(
                success=False,
                disposition=ImportOutcomeDisposition.FAILED,
                source_key=command.source_key,
                raw_digest=raw_digest,
                watermark=None,
                batch=None,
                exact_duplicates=dedup_report.exact_duplicates,
                errors=(
                    ImportErrorDetail(
                        code=ImportErrorCode.REPOSITORY_ERROR,
                        message=f"Failed to query previous watermark: {exc}",
                    ),
                ),
            )

        # Step 7: Evaluate replay disposition
        if previous_watermark is None:
            disposition = ImportOutcomeDisposition.FIRST_IMPORT
        elif previous_watermark == dedup_report.watermark:
            disposition = ImportOutcomeDisposition.EXACT_REPLAY
        else:
            disposition = ImportOutcomeDisposition.MATERIAL_CHANGE

        return CanonicalImportResult(
            success=True,
            disposition=disposition,
            source_key=command.source_key,
            raw_digest=raw_digest,
            watermark=dedup_report.watermark,
            batch=dedup_report.batch,
            exact_duplicates=dedup_report.exact_duplicates,
            errors=(),
        )

    def __call__(self, command: ImportCanonicalSourceCommand) -> CanonicalImportResult:
        """Alias for ``execute`` to support callable use-case invocation."""
        return self.execute(command)
