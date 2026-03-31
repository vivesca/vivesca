from fastmcp.tools import tool

@tool(name="weather_fetch", description="Fetch weather")
def weather_fetch() -> str:
    return "sunny"
