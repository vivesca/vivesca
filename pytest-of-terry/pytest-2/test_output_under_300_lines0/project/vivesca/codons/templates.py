from fastmcp.prompts import prompt

@prompt(name="research", description="Research brief")
def research(topic: str) -> str:
    return topic
