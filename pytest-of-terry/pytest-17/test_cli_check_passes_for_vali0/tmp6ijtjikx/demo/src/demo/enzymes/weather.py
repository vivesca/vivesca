"""weather — No description provided..

Tools:
  weather_fetch — No description provided.
"""

from pydantic import BaseModel
from vivesca.schemas import Secretion

from fastmcp.tools import tool
from mcp.types import ToolAnnotations


class WeatherFetchResult(Secretion):
    """Structured output for weather_fetch.

    Define your output fields here. Every field becomes part of
    the outputSchema that agents can rely on.
    """

    # TODO: Define output fields
    message: str


@tool(
    name="weather_fetch",
    description="No description provided.",
    annotations=ToolAnnotations(readOnlyHint=True),
)
def weather_fetch() -> WeatherFetchResult:
    """No description provided..

    Args:
        TODO: Define parameters above and document them here.
    """
    # TODO: Implement — call a service or CLI, return structured output
    raise NotImplementedError("Implement weather_fetch")