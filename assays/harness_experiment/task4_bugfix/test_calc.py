"""Tests for Calculator — 2 will fail due to bugs in calc.py."""

import pytest
from calc import Calculator


@pytest.fixture
def calc():
    return Calculator()


def test_add(calc):
    assert calc.add(2, 3) == 5


def test_subtract(calc):
    assert calc.subtract(10, 3) == 7


def test_multiply(calc):
    assert calc.multiply(4, 5) == 20  # FAILS: multiply returns 9 (a+b)


def test_multiply_by_zero(calc):
    assert calc.multiply(7, 0) == 0  # FAILS: multiply returns 7 (a+b)


def test_divide(calc):
    assert calc.divide(10, 2) == 5.0


def test_divide_float(calc):
    assert calc.divide(7, 2) == pytest.approx(3.5)  # FAILS: // returns 3


def test_divide_by_zero(calc):
    with pytest.raises(ValueError):
        calc.divide(1, 0)


def test_add_negative(calc):
    assert calc.add(-1, -1) == -2


def test_subtract_negative(calc):
    assert calc.subtract(3, 10) == -7


def test_divide_negative(calc):
    assert calc.divide(-10, 2) == -5.0
