"""Tests for Stack class. Implementation should be in stack.py."""

import pytest
from stack import Stack


@pytest.fixture
def stack():
    return Stack()


def test_new_stack_is_empty(stack):
    assert stack.is_empty()


def test_push_makes_non_empty(stack):
    stack.push(1)
    assert not stack.is_empty()


def test_push_pop_returns_value(stack):
    stack.push(42)
    assert stack.pop() == 42


def test_pop_empty_raises(stack):
    with pytest.raises(IndexError):
        stack.pop()


def test_peek_returns_top(stack):
    stack.push(1)
    stack.push(2)
    assert stack.peek() == 2


def test_peek_does_not_remove(stack):
    stack.push(1)
    stack.peek()
    assert stack.size() == 1


def test_peek_empty_raises(stack):
    with pytest.raises(IndexError):
        stack.peek()


def test_size_tracks_pushes(stack):
    for i in range(5):
        stack.push(i)
    assert stack.size() == 5


def test_lifo_order(stack):
    for val in [10, 20, 30]:
        stack.push(val)
    assert [stack.pop() for _ in range(3)] == [30, 20, 10]


def test_push_pop_mixed(stack):
    stack.push(1)
    stack.push(2)
    stack.pop()
    stack.push(3)
    assert stack.pop() == 3
    assert stack.pop() == 1
