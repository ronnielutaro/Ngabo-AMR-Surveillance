"""Bootstrap console runner for certifying the offline hero surveillance release gate (Issue #48).

Prints machine-readable JSON certification evidence to stdout.
Exits 0 on certified hero release gate pass, non-zero on failure.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ngabo.application.commands.certify_offline_hero_command import (
    CertifyOfflineHeroCommand,
)
from ngabo.application.ports.load_import_source import LoadImportSource
from ngabo.application.ports.parse_canonical_source import ParseCanonicalSource
from ngabo.application.ports.source_replay_repository import SourceReplayRepository
from ngabo.application.use_cases.certify_offline_hero import CertifyOfflineHero
from ngabo.application.value_objects.offline_hero_certification_result import (
    OfflineHeroCertificationResult,
)
from ngabo.infrastructure.loaders.local_file_source_loader import LocalFileSourceLoader
from ngabo.infrastructure.repositories.in_memory_source_replay_repository import (
    InMemorySourceReplayRepository,
)
from ngabo.interfaces.parsers.whonet_csv_parser import parse_whonet_csv


def _resolve_repo_root() -> Path:
    """Resolve the repository root directory."""
    # .../services/core/ngabo/bootstrap/certify_hero.py -> 4 levels up is repo root
    return Path(__file__).resolve().parents[4]


def create_offline_hero_use_case(
    source_loader: LoadImportSource | None = None,
    replay_repo: SourceReplayRepository | None = None,
    parser: ParseCanonicalSource | None = None,
) -> CertifyOfflineHero:
    """Factory helper wiring default or injected adapters into CertifyOfflineHero use case."""
    return CertifyOfflineHero(
        source_loader=source_loader if source_loader is not None else LocalFileSourceLoader(),
        replay_repo=replay_repo if replay_repo is not None else InMemorySourceReplayRepository(),
        parser=parser if parser is not None else parse_whonet_csv,
    )


def certify_hero(
    csv_path: str | Path | None = None,
    use_case: CertifyOfflineHero | None = None,
) -> OfflineHeroCertificationResult:
    """Run offline hero certification using default or explicit CSV input."""
    resolved_path: str | None = None
    if csv_path is not None:
        resolved_path = str(Path(csv_path).resolve())
    else:
        default_csv = _resolve_repo_root() / "data" / "synthetic" / "canonical_hero.csv"
        if default_csv.is_file():
            resolved_path = str(default_csv)

    cmd = CertifyOfflineHeroCommand(source_location=resolved_path)
    runner = use_case or create_offline_hero_use_case()
    return runner.execute(cmd)


def main(argv: Sequence[str] | None = None) -> int:
    """Console script entry point (ngabo-certify-hero)."""
    parser = argparse.ArgumentParser(
        description="Certify Ngabo offline hero input-to-signal surveillance release gate."
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help=(
            "Path to synthetic WHONET-style CSV input "
            "(defaults to data/synthetic/canonical_hero.csv)."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress JSON stdout; only report exit status.",
    )
    args = parser.parse_args(argv)

    result = certify_hero(args.csv)

    if not args.quiet:
        print(result.to_json())

    is_hero_valid = result.verify_hero_expectations()
    if not is_hero_valid:
        if not result.certified:
            sys.stderr.write("ERROR: Certification failed during deterministic execution.\n")
            for err in result.errors:
                sys.stderr.write(f"  - {err}\n")
        else:
            sys.stderr.write(
                f"ERROR: Hero expectations violated: signal_count={result.signal_count}, "
                f"signal_id={result.hero_signal_id}, score={result.hero_signal_score}.\n"
            )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
