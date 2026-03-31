from fastmcp.tools import tool

@tool(name="alpha_get", description="Get alpha")
def alpha_get() -> str:
    return "a"

@tool(name="alpha_set", description="Set alpha")
def alpha_set(v: str) -> str:
    return v
