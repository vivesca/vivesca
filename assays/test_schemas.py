from __future__ import annotations

"""Tests for vivesca base output schemas."""


from pydantic import BaseModel


def test_secretion_is_base_model():
    from metabolon.morphology import Secretion

    assert issubclass(Secretion, BaseModel)


def test_secretion_allows_extra_fields():
    from metabolon.morphology import Secretion

    obj = Secretion.model_validate({"unexpected": "value"})
    assert obj.unexpected == "value"


def test_secretion_json_schema():
    from metabolon.morphology import Secretion

    class MyOutput(Secretion):
        name: str
        count: int

    schema = MyOutput.model_json_schema()
    assert "name" in schema["properties"]
    assert "count" in schema["properties"]


def test_pathology_fields():
    from metabolon.morphology import Pathology

    err = Pathology(error="not found", code="NOT_FOUND")
    assert err.error == "not found"
    assert err.code == "NOT_FOUND"
    assert err.details == {}


def test_pathology_with_details():
    from metabolon.morphology import Pathology

    err = Pathology(error="timeout", code="TIMEOUT", details={"elapsed": 30})
    assert err.details["elapsed"] == 30


def test_pathology_json_roundtrip():
    from metabolon.morphology import Pathology

    err = Pathology(error="fail", code="ERR")
    data = err.model_dump()
    restored = Pathology.model_validate(data)
    assert restored == err


def test_vesicle_fields():
    from metabolon.morphology import Vesicle

    out = Vesicle(items=[{"id": 1}, {"id": 2}], count=2)
    assert out.count == 2
    assert len(out.items) == 2


def test_schemas_vesicle_auto_count():
    from metabolon.morphology import Vesicle

    out = Vesicle(items=[{"a": 1}, {"b": 2}, {"c": 3}])
    assert out.count == 3


def test_vital_fields():
    from metabolon.morphology import Vital

    out = Vital(status="ok", message="All systems nominal")
    assert out.status == "ok"
    assert out.details == {}


def test_effector_result_fields():
    from metabolon.morphology import EffectorResult

    out = EffectorResult(success=True, message="Created event")
    assert out.success is True
    assert out.data == {}
