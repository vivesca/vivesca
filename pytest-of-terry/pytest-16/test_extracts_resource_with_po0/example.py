from fastmcp.resources import resource

@resource("vivesca://budget")
def budget_status() -> str:
    return "ok"
