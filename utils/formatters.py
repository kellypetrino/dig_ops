def decision_badge(decision: str) -> str:
    if decision == "auto_approved":
        return "🟢 INSTANT REFUND APPROVED"
    return "🔴 FLAGGED FOR INSPECTION"


def risk_label(score: float) -> tuple[str, str]:
    """Return (label, color) for a risk score."""
    if score < 30:
        return "Low Risk", "#057a55"
    elif score < 55:
        return "Moderate Risk", "#d97706"
    return "High Risk", "#c81e1e"


def trust_label(score: float) -> tuple[str, str]:
    if score >= 80:
        return "High Trust", "#057a55"
    elif score >= 55:
        return "Moderate Trust", "#d97706"
    return "Low Trust", "#c81e1e"


def format_rule_name(rule: str) -> str:
    return {
        "multiple_fraud_flags": "Multiple fraud flags on account",
        "high_value_item": "Item value exceeds $500",
        "low_value_item": "Item value under $10",
        "retailer_error": "Wrong item shipped (retailer error)",
    }.get(rule, rule)
