from fastmcp.resources import resource

@resource("vivesca://constitution")
def constitution() -> str:
    return ""
