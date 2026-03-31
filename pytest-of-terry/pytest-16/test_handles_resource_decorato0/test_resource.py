
"""Sample resource module."""

from some_lib import resource

@resource("my_resource")
def get_data():
    """Get some data."""
    pass

@resource(uri="vivesca://custom")
def custom_uri():
    pass
