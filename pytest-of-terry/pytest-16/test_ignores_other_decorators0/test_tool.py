
"""Sample tool module for testing."""

from some_lib import tool

@tool("my_tool")
def my_function(arg1: str, arg2: int) -> str:
    """A sample tool function.
    
    More details here.
    """
    return arg1

@tool(name="another_tool")
def another_func(x: int) -> int:
    """Another tool."""
    return x

@other_decorator
def not_a_tool():
    pass

@tool
def bare_tool():
    """Bare tool with no args."""
    pass
