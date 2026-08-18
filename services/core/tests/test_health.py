"""Bootstrap health smoke tests (M1A scaffold only)."""

from __future__ import annotations

from ngabo.bootstrap.health import health


def test_health_reports_ok() -> None:
    payload = health()
    assert payload == {"status": "ok", "service": "ngabo-core"}
