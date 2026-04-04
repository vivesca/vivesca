"""Tests for metabolon.morphology.base — Pydantic secretion models."""

from metabolon.morphology.base import EffectorResult, Pathology, Secretion, Vesicle, Vital

# --- Secretion (base) ---


class TestSecretion:
    def test_allows_extra_fields(self):
        s = Secretion(custom_field="hello", number=42)
        assert s.custom_field == "hello"
        assert s.number == 42

    def test_json_roundtrip(self):
        s = Secretion(x=1)
        data = s.model_dump()
        assert Secretion.model_validate(data).x == 1


# --- Pathology ---


class TestPathology:
    def test_defaults(self):
        p = Pathology(error="boom")
        assert p.error == "boom"
        assert p.code == "unknown"
        assert p.details == {}

    def test_custom_values(self):
        p = Pathology(error="not found", code="ENOENT", details={"path": "/tmp/x"})
        assert p.code == "ENOENT"
        assert p.details["path"] == "/tmp/x"

    def test_not_subclass_of_secretion(self):
        """Pathology is its own BaseModel, not a Secretion."""
        assert not isinstance(Pathology(error="x"), Secretion)


# --- Vesicle ---


class TestVesicle:
    def test_auto_count(self):
        v = Vesicle(items=[{"a": 1}, {"b": 2}, {"c": 3}])
        assert v.count == 3

    def test_empty_items_default_count(self):
        v = Vesicle(items=[])
        assert v.count == 0

    def test_explicit_count_preserved(self):
        v = Vesicle(items=[{"a": 1}], count=99)
        assert v.count == 99

    def test_is_secretion(self):
        assert isinstance(Vesicle(items=[]), Secretion)


# --- Vital ---


class TestVital:
    def test_ok_status(self):
        v = Vital(status="ok", message="all good")
        assert v.status == "ok"
        assert v.details == {}

    def test_warning_with_details(self):
        v = Vital(status="warning", message="degraded", details={"latency_ms": 500})
        assert v.details["latency_ms"] == 500

    def test_is_secretion(self):
        assert isinstance(Vital(status="ok", message=""), Secretion)


# --- EffectorResult ---


class TestEffectorResult:
    def test_success(self):
        r = EffectorResult(success=True, message="done")
        assert r.success is True
        assert r.data == {}

    def test_failure_with_data(self):
        r = EffectorResult(success=False, message="failed", data={"attempted": 3})
        assert r.success is False
        assert r.data["attempted"] == 3

    def test_is_secretion(self):
        assert isinstance(EffectorResult(success=True, message=""), Secretion)
