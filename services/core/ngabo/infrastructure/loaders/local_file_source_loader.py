"""Local file loader implementing LoadImportSource port (Issue #44, Issue #48)."""

from __future__ import annotations

from pathlib import Path

from ngabo.application.ports.load_import_source import LoadImportSource


class LocalFileSourceLoader(LoadImportSource):
    """Retrieves raw source artifact bytes from local filesystem paths."""

    def __call__(self, location: str) -> bytes:
        if not isinstance(location, str) or not location.strip():
            raise ValueError("location must be a non-empty string")
        path = Path(location)
        if not path.is_file():
            raise FileNotFoundError(f"Source file not found: {location!r}")
        return path.read_bytes()
