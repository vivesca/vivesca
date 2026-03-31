"""analyze prompt template.

Prompts:
  analyze — Analyze data
"""

from fastmcp.prompts import prompt


@prompt(
    name="analyze",
    description="Analyze data",
)
def analyze(
    topic: str,
    context: str = "",
) -> str:
    """Analyze data.

    Args:
        topic: The subject for this prompt.
        context: Optional background context.
    """
    context_block = f"\nContext: {context}\n" if context else ""

    return (
        f"Analyze data\n\n"
        f"Topic: {topic}\n"
        f"{context_block}"
    )