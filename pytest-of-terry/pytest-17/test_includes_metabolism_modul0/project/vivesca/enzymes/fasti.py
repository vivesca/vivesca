"""fasti -- Google Calendar management.

Tools:
  fasti_list_events  -- list events for a date
"""
from fastmcp.tools import tool

@tool(name="fasti_list_events", description="List events")
def fasti_list_events(date: str, calendar: str = 'primary') -> str:
    """List calendar events for a given date."""
    return ""

@tool(name="fasti_create_event", description="Create event")
def fasti_create_event(title: str, start: str, end: str) -> str:
    """Create a new calendar event."""
    return ""
