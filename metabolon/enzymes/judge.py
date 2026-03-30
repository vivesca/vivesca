"""judge — LLM quality gate against named rubrics.

Tools:
  judge_evaluate — evaluate content against a rubric
"""

from typing import Optional


from metabolon.organelles.effector import run_cli  # noqa: E402

from fastmcp.tools import tool  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

BINARY = "/Users/terry/.local/bin/judge"

_TIMEOUT = 60


@tool(
    name="judge_evaluate",
    description="Evaluate content against a rubric (article/job-eval/outreach).",
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def judge_evaluate(
    rubric: str,
    content: str,
    context: Optional[str] = None,
    model: str = "glm",
) -> str:
    """Evaluate content against a named rubric.

    Args:
        rubric: One of 'article', 'job-eval', or 'outreach'.
        content: The text to evaluate (piped via stdin).
        context: Optional additional context passed to the rubric.
        model: LLM model to use (default 'glm').
    """
    valid_rubrics = {"article", "job-eval", "outreach"}
    if rubric not in valid_rubrics:
        raise ValueError(
            f"Invalid rubric '{rubric}'. Must be one of: {', '.join(sorted(valid_rubrics))}"
        )

    args = [rubric, "--json", "--model", model]
    if context:
        args.extend(["--context", context])

    return run_cli(BINARY, args, timeout=_TIMEOUT, stdin_text=content)
