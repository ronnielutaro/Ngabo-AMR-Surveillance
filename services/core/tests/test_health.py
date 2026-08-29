"""Bootstrap health smoke tests (M1A scaffold only)."""

from __future__ import annotations

from ngabo.bootstrap.health import health


def test_health_reports_ok() -> None:
    payload = health()
    assert payload == {"status": "ok", "service": "ngabo-core"}


def test_health_omits_container_metadata_when_absent(monkeypatch) -> None:
    monkeypatch.delenv("NGABO_SERVICE_VERSION", raising=False)
    monkeypatch.delenv("NGABO_SOURCE_REVISION", raising=False)
    assert health() == {"status": "ok", "service": "ngabo-core"}


def test_health_includes_container_metadata_when_provided(monkeypatch) -> None:
    monkeypatch.setenv("NGABO_SERVICE_VERSION", "0.1.0")
    monkeypatch.setenv("NGABO_SOURCE_REVISION", "0123456789abcdef")
    assert health() == {
        "status": "ok",
        "service": "ngabo-core",
        "version": "0.1.0",
        "revision": "0123456789abcdef",
    }
