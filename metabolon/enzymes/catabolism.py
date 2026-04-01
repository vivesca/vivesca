"""spending -- catabolic metabolism of credit card statements.

Tools:
  catabolism -- parse statements, summarise spending, flag issues, confirm payments
"""


from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from pydantic import Field

from metabolon.locus import spending
from metabolon.morphology import EffectorResult, Secretion

SPENDING_DIR = spending
PAYMENTS_FILE = SPENDING_DIR / "payments.yaml"


class CatabolismResult(Secretion):
    """Product of catabolic spending digestion."""

    summary: str
    statements_processed: int = 0
    total_alerts: int = 0
    details: list[dict] = Field(default_factory=list)


class CatabolismConfirmResult(EffectorResult):
    """Result of confirming a catabolic payment."""

    pass


def _spending(days: int = 30) -> CatabolismResult:
    """Catabolic digestion of credit card statements.

    Args:
        days: budget monitoring window (how many days of spending to evaluate).
    """
    from metabolon.respirometry import metabolize_statements
    from metabolon.respirometry.payments import assess_missing_statements, flag_overdue_payments

    config_file = SPENDING_DIR / "config.yaml"
    results = metabolize_statements()

    # Check for overdue/upcoming payments regardless of new statements
    payment_alerts = flag_overdue_payments(PAYMENTS_FILE)
    missing_alerts = assess_missing_statements(config_file, SPENDING_DIR)

    if not results and not payment_alerts and not missing_alerts:
        return CatabolismResult(summary="No new statements found. All cards accounted for.")

    degraded = [r for r in results if "error" in r]
    digested = [r for r in results if "error" not in r]

    all_alerts: list[str] = []
    for r in digested:
        all_alerts.extend(r.get("alerts", []))

    parts: list[str] = []

    if digested:
        for r in digested:
            total = r.get("total_hkd", 0)
            parts.append(
                f"{r['card']} ({r['statement_date']}): "
                f"{r['transaction_count']} transactions, "
                f"HKD {total:,.2f}"
            )
        # Include payment actions
        for r in digested:
            action = r.get("payment_action")
            if action:
                parts.append(action)
    elif not payment_alerts:
        parts.append("No new statements found.")

    for r in degraded:
        parts.append(f"Error: {r['error']}")

    if payment_alerts:
        parts.append("")
        parts.append("Payment alerts:")
        parts.extend(f"  - {a}" for a in payment_alerts)
        all_alerts.extend(payment_alerts)

    if missing_alerts:
        parts.append("")
        parts.append("Missing statements:")
        parts.extend(f"  - {a}" for a in missing_alerts)
        all_alerts.extend(missing_alerts)

    if all_alerts and any("Alert" not in p for p in parts if p.startswith("  - ")):
        monitor_alerts = []
        for r in digested:
            monitor_alerts.extend(r.get("alerts", []))
        if monitor_alerts:
            parts.append("")
            parts.append("Alerts:")
            parts.extend(f"  - {a}" for a in monitor_alerts)

    return CatabolismResult(
        summary="\n".join(parts),
        statements_processed=len(digested),
        total_alerts=len(all_alerts),
        details=results,
    )


def _confirm(bank: str) -> CatabolismConfirmResult:
    """Confirm catabolic payment — remove pending entry.

    Args:
        bank: bank identifier (mox, ccba, scb, hsbc).
    """
    from metabolon.respirometry.payments import dequeue_payment

    bank = bank.lower().strip()
    removed = dequeue_payment(PAYMENTS_FILE, bank)

    if removed is None:
        return CatabolismConfirmResult(
            success=False,
            message=f"No pending payment found for {bank.upper()}.",
        )

    amount = removed.get("amount", 0)
    due_date = removed.get("due_date", "unknown")
    return CatabolismConfirmResult(
        success=True,
        message=(
            f"Payment confirmed: {bank.upper()} HKD {amount:,.2f} "
            f"(was due {due_date}). Removed from pending."
        ),
    )


@tool(
    name="catabolism",
    description="Financial tracking. Actions: spending|confirm",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def catabolism(
    action: str,
    days: int = 30,
    bank: str = "",
) -> CatabolismResult | CatabolismConfirmResult:
    """Financial tracking — spending summaries and payment confirmation.

    Args:
        action: spending|confirm
        days: budget monitoring window for spending action (default 30).
        bank: bank identifier for confirm action (mox, ccba, scb, hsbc).
    """
    if action == "spending":
        return _spending(days=days)
    elif action == "confirm":
        return _confirm(bank=bank)
    else:
        return CatabolismConfirmResult(
            success=False,
            message=f"Unknown action '{action}'. Use spending or confirm.",
        )
