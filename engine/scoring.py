"""
Scoring logic for the Instant Refund Decision Engine.

Three components combine into a final risk score (0–100, higher = riskier):
  1. Customer trust score → converted to customer risk
  2. Item risk score
  3. Return reason modifier

Routing:
  risk_score < AUTO_APPROVE_THRESHOLD  → auto_approved
  risk_score >= AUTO_APPROVE_THRESHOLD → flagged_inspection
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.models import Customer, Item

AUTO_APPROVE_THRESHOLD = 45.0

# Weights for composite score
TRUST_WEIGHT = 0.40
ITEM_WEIGHT = 0.35
REASON_WEIGHT = 0.25

REASON_RISK_MODIFIER = {
    "defective": -20,
    "wrong_item": -15,
    "not_as_described": -10,
    "sizing_issue": 5,
    "changed_mind": 15,
}

CATEGORY_RISK = {
    "electronics": 30,
    "beauty": 20,
    "apparel": 10,
    "home_goods": 10,
    "books": 5,
}

RESALE_PENALTY = {
    "none": 15,
    "low": 10,
    "medium": 5,
    "high": 0,
}


def compute_trust_score(customer: "Customer") -> float:
    """Return a trust score 0–100 (higher = more trustworthy)."""
    score = 100.0

    # Penalty: return rate
    return_rate = customer.total_returns / max(customer.lifetime_orders, 1)
    if return_rate > 0.50:
        score -= 35
    elif return_rate > 0.30:
        score -= 20
    elif return_rate > 0.15:
        score -= 8

    # Penalty: fraud flags (hard signal, -25 each, capped at -50)
    score -= min(customer.fraud_flags * 25, 50)

    # Penalty/bonus: account tenure
    if customer.account_tenure_days < 30:
        score -= 10
    elif customer.account_tenure_days > 730:
        score += 10
    elif customer.account_tenure_days > 365:
        score += 5

    # Bonus: high order volume (engaged customer)
    if customer.lifetime_orders > 50:
        score += 5
    elif customer.lifetime_orders < 3:
        score -= 5

    return round(max(0.0, min(100.0, score)), 1)


def compute_item_risk_score(item: "Item") -> float:
    """Return an item risk score 0–100 (higher = riskier to auto-approve)."""
    score = 0.0

    # Price tier
    if item.price_tier == "high":
        score += 35
    elif item.price_tier == "mid":
        score += 15
    else:
        score += 5

    # Category fraud/abuse rate
    score += CATEGORY_RISK.get(item.category, 10)

    # Resale viability (if item can't be resold, auto-approving costs more)
    score += RESALE_PENALTY.get(item.resale_viability, 10)

    # Days since purchase (older returns are riskier)
    if item.days_since_purchase > 60:
        score += 15
    elif item.days_since_purchase > 30:
        score += 8

    return round(min(100.0, score), 1)


def compute_final_risk_score(
    trust_score: float,
    item_risk_score: float,
    return_reason: str,
    weights: dict | None = None,
) -> tuple[float, dict]:
    """
    Compute the composite risk score and return (score, breakdown).

    weights: optional dict with keys 'trust', 'item', 'reason' summing to 1.0.
             Defaults to TRUST_WEIGHT / ITEM_WEIGHT / REASON_WEIGHT.
    """
    if weights is None:
        w_trust = TRUST_WEIGHT
        w_item = ITEM_WEIGHT
        w_reason = REASON_WEIGHT
    else:
        w_trust = weights.get("trust", TRUST_WEIGHT)
        w_item = weights.get("item", ITEM_WEIGHT)
        w_reason = weights.get("reason", REASON_WEIGHT)

    trust_risk = 100.0 - trust_score
    reason_modifier = REASON_RISK_MODIFIER.get(return_reason, 0)
    reason_component = 50 + reason_modifier  # center at 50

    raw_score = (
        trust_risk * w_trust
        + item_risk_score * w_item
        + reason_component * w_reason
    )
    final_score = round(max(0.0, min(100.0, raw_score)), 1)

    breakdown = {
        "trust_score": trust_score,
        "trust_risk": round(trust_risk, 1),
        "trust_contribution": round(trust_risk * w_trust, 1),
        "item_risk_score": item_risk_score,
        "item_contribution": round(item_risk_score * w_item, 1),
        "return_reason": return_reason,
        "reason_modifier": reason_modifier,
        "reason_component": reason_component,
        "reason_contribution": round(reason_component * w_reason, 1),
        "final_risk_score": final_score,
        "threshold": AUTO_APPROVE_THRESHOLD,
    }

    return final_score, breakdown


def route_return(risk_score: float, threshold: float = AUTO_APPROVE_THRESHOLD) -> str:
    """Return routing decision based on risk score."""
    return "auto_approved" if risk_score < threshold else "flagged_inspection"
