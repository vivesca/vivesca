from fastmcp.tools import tool

@tool(name="fasti_list_events", description="List events")
def fasti_list_events(date: str) -> str:
    return "ok"
