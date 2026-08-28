"""Ngabo infrastructure layer — framework/vendor adapters.

Provides concrete adapters implementing inward application ports:
- Repositories: InMemorySourceReplayRepository (Issue #44, #48)
- Loaders: LocalFileSourceLoader (Issue #44, #48)
"""

from ngabo.infrastructure.loaders import LocalFileSourceLoader
from ngabo.infrastructure.repositories import InMemorySourceReplayRepository

__all__ = [
    "InMemorySourceReplayRepository",
    "LocalFileSourceLoader",
]
