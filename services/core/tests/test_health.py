"""Bootstrap health smoke tests (M1A scaffold only)."""

from __future__ import annotations

import pytest

from ngabo.bootstrap.health import health


def test_health_reports_ok() -> None:
    payload = health()
    assert payload == {"status": "ok", "service": "ngabo-core"}


def test_health_omits_container_metadata_when_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NGABO_SERVICE_VERSION", raising=False)
    monkeypatch.delenv("NGABO_SOURCE_REVISION", raising=False)
    assert health() == {"status": "ok", "service": "ngabo-core"}


def test_health_includes_container_metadata_when_provided(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NGABO_SERVICE_VERSION", "0.1.0")
    monkeypatch.setenv("NGABO_SOURCE_REVISION", "0123456789abcdef")
    assert health() == {
        "status": "ok",
        "service": "ngabo-core",
        "version": "0.1.0",
        "revision": "0123456789abcdef",
    }


def test_readiness_includes_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    from ngabo.interfaces.health import readiness

    monkeypatch.setenv("NGABO_SERVICE_VERSION", "0.1.0")
    monkeypatch.setenv("NGABO_SOURCE_REVISION", "0123456789abcdef")
    payload = readiness()
    assert payload["status"] == "ok"
    assert payload["ready"] is True
    assert payload["revision"] == "0123456789abcdef"


def test_runtime_identity_includes_valid_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    from ngabo.interfaces.health import runtime_identity

    digest = "sha256:" + "a" * 64
    monkeypatch.setenv("NGABO_IMAGE_DIGEST", digest)
    monkeypatch.setenv("NGABO_ENVIRONMENT", "dev")
    identity = runtime_identity()
    assert identity["image_digest"] == digest
    assert identity["environment"] == "dev"
    assert identity["revision"] == "unknown"


def test_runtime_identity_omits_missing_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    from ngabo.interfaces.health import runtime_identity

    monkeypatch.delenv("NGABO_IMAGE_DIGEST", raising=False)
    assert "image_digest" not in runtime_identity()


def test_runtime_identity_omits_malformed_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    from ngabo.interfaces.health import runtime_identity

    for bad in ("latest", "sha256:abc", "sha256:" + "g" * 64, ""):
        monkeypatch.setenv("NGABO_IMAGE_DIGEST", bad)
        assert "image_digest" not in runtime_identity(), bad
