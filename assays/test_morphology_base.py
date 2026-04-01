"""Tests for morphology base models (Secretion, Pathology, Vesicle, Vital, EffectorResult)."""

from metabolon.morphology.base import Secretion, Pathology, Vesicle, Vital, EffectorResult


def test_secretion_basic():
    s = Secretion()
    assert isinstance(s, Secretion)
    d = s.model_dump()
    assert isinstance(d, dict)


def test_secretion_extra_fields():
    s = Secretion(custom="hello", count=42)
    assert s.custom == "hello"
    assert s.count == 42


def test_pathology_defaults():
    p = Pathology(error="something broke")
    assert p.error == "something broke"
    assert p.code == "unknown"
    assert p.details == {}


def test_pathology_custom():
    p = Pathology(error="timeout", code="E_TIMEOUT", details={"seconds": 30})
    assert p.code == "E_TIMEOUT"
    assert p.details["seconds"] == 30


def test_morphology_base_vesicle_auto_count():
    v = Vesicle(items=[{"a": 1}, {"b": 2}])
    assert v.count == 2


def test_vesicle_empty():
    v = Vesicle(items=[])
    assert v.count == 0


def test_vesicle_explicit_count():
    v = Vesicle(items=[{"a": 1}], count=99)
    assert v.count == 99


def test_vital_ok():
    v = Vital(status="ok", message="all good")
    assert v.status == "ok"


def test_vital_with_details():
    v = Vital(status="warning", message="high load", details={"cpu": 90})
    assert v.details["cpu"] == 90


def test_effector_result_success():
    r = EffectorResult(success=True, message="created file")
    assert r.success is True
    assert r.data == {}


def test_effector_result_failure():
    r = EffectorResult(success=False, message="not found", data={"path": "/x"})
    assert r.success is False
    assert r.data["path"] == "/x"
