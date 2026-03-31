"""config resource.

Resources:
  myapp://config — App config
"""

from fastmcp.resources import resource


@resource("myapp://config")
def config() -> str:
    """App config.

    Returns context that agents can read on demand.
    """
    # TODO: Implement — return useful context
    raise NotImplementedError("Implement config")