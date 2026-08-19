"""Unit tests for the framework-free domain identity/version primitives.

Covers Issue #25 (M1B.1): ``IncidentId``, ``IncidentVersion`` and
``SourceWatermark`` — valid/invalid construction, value semantics and stable
string representation. No persistence, framework, or future-behavior tests.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ngabo.domain.value_objects.incident_id import IncidentId
from ngabo.domain.value_objects.incident_version import IncidentVersion
from ngabo.domain.value_objects.source_watermark import SourceWatermark


class TestIncidentId:
    def test_valid_construction(self) -> None:
        incident_id = IncidentId("INC-001")
        assert incident_id.value == "INC-001"
        assert str(incident_id) == "INC-001"

    @pytest.mark.parametrize(
        "value",
        ["", "   ", "abc", "INC-", "INC-abc", "INC-001 ", " INC-001", 123, None],
    )
    def test_invalid_construction_rejected(self, value: object) -> None:
        with pytest.raises(ValueError):
            IncidentId(value)  # type: ignore[arg-type]

    def test_equality_is_by_value(self) -> None:
        assert IncidentId("INC-001") == IncidentId("INC-001")
        assert IncidentId("INC-001") != IncidentId("INC-002")
        assert IncidentId("INC-001") != object()

    def test_hash_is_value_consistent(self) -> None:
        assert hash(IncidentId("INC-001")) == hash(IncidentId("INC-001"))
        assert len({IncidentId("INC-001"), IncidentId("INC-001")}) == 1
        assert {IncidentId("INC-001"): "x"}[IncidentId("INC-001")] == "x"

    def test_immutable(self) -> None:
        incident_id = IncidentId("INC-001")
        with pytest.raises(FrozenInstanceError):
            incident_id.value = "INC-002"  # type: ignore[misc]


class TestIncidentVersion:
    @pytest.mark.parametrize("value", [1, 4, 10_000])
    def test_valid_construction(self, value: int) -> None:
        version = IncidentVersion(value)
        assert version.value == value
        assert str(version) == str(value)

    @pytest.mark.parametrize("value", [0, -1, True, 1.5, "4", None])
    def test_invalid_construction_rejected(self, value: object) -> None:
        with pytest.raises(ValueError):
            IncidentVersion(value)  # type: ignore[arg-type]

    def test_equality_is_by_value(self) -> None:
        assert IncidentVersion(4) == IncidentVersion(4)
        assert IncidentVersion(4) != IncidentVersion(5)
        assert IncidentVersion(4) != object()

    def test_hash_is_value_consistent(self) -> None:
        assert hash(IncidentVersion(4)) == hash(IncidentVersion(4))
        assert len({IncidentVersion(4), IncidentVersion(4)}) == 1

    def test_immutable(self) -> None:
        version = IncidentVersion(4)
        with pytest.raises(FrozenInstanceError):
            version.value = 5  # type: ignore[misc]


class TestSourceWatermark:
    @pytest.mark.parametrize("value", ["batch-2026-0819:001", "wm-abc-123"])
    def test_valid_construction(self, value: str) -> None:
        watermark = SourceWatermark(value)
        assert watermark.value == value
        assert str(watermark) == value

    @pytest.mark.parametrize("value", ["", "   ", " abc", "abc ", 42, None])
    def test_invalid_construction_rejected(self, value: object) -> None:
        with pytest.raises(ValueError):
            SourceWatermark(value)  # type: ignore[arg-type]

    def test_equality_is_by_value(self) -> None:
        assert SourceWatermark("wm-abc") == SourceWatermark("wm-abc")
        assert SourceWatermark("wm-abc") != SourceWatermark("wm-def")
        assert SourceWatermark("wm-abc") != object()

    def test_hash_is_value_consistent(self) -> None:
        assert hash(SourceWatermark("wm-abc")) == hash(SourceWatermark("wm-abc"))
        assert len({SourceWatermark("wm-abc"), SourceWatermark("wm-abc")}) == 1

    def test_immutable(self) -> None:
        watermark = SourceWatermark("wm-abc")
        with pytest.raises(FrozenInstanceError):
            watermark.value = "wm-def"  # type: ignore[misc]
