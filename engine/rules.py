"""
Hard override rules for the Instant Refund Decision Engine.

These are applied BEFORE scoring. If a rule fires, the scoring step is skipped
and the forced decision is returned directly. This models real-world policy
guardrails that override the statistical model in edge cases.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.models import Customer, Item


def apply_hard_rules(
    customer: "Customer",
    item: "Item",
    return_reason: str,
) -> tuple[Optional[str], Optional[str]]:
    """
    Evaluate hard override rules before scoring.

    Returns:
        (decision, rule_name) if a rule fires.
        (None, None) if no rule fires — proceed to score-based routing.
    """
    # Rule 1: Multiple fraud flags → always inspect
    if customer.fraud_flags >= 2:
        return "flagged_inspection", "multiple_fraud_flags"

    # Rule 2: Very high-value item → always inspect (financial exposure too large)
    if item.price > 500.0:
        return "flagged_inspection", "high_value_item"

    # Rule 3: Very low-value item → always approve (not worth inspection cost)
    if item.price < 10.0:
        return "auto_approved", "low_value_item"

    # Rule 4: Confirmed wrong item shipped → always approve (retailer error)
    if return_reason == "wrong_item":
        return "auto_approved", "retailer_error"

    return None, None


RULE_DESCRIPTIONS = {
    "multiple_fraud_flags": "Customer has 2+ fraud flags on record — manual review required.",
    "high_value_item": "Item value exceeds $500 — all high-value returns require inspection.",
    "low_value_item": "Item value under $10 — inspection cost exceeds item value.",
    "retailer_error": "Wrong item shipped — retailer-side error, auto-approved.",
}
