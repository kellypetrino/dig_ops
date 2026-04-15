from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Customer:
    customer_id: str
    name: str
    account_tenure_days: int
    lifetime_orders: int
    total_returns: int
    fraud_flags: int

    @property
    def return_rate(self) -> float:
        return self.total_returns / max(self.lifetime_orders, 1)

    @property
    def trust_score(self) -> float:
        from engine.scoring import compute_trust_score
        return compute_trust_score(self)


@dataclass
class Item:
    item_id: str
    name: str
    category: str  # electronics, apparel, home_goods, beauty, books
    price: float
    resale_viability: str  # high, medium, low, none
    days_since_purchase: int

    @property
    def price_tier(self) -> str:
        if self.price > 150:
            return "high"
        elif self.price >= 30:
            return "mid"
        return "low"


@dataclass
class ReturnRequest:
    return_id: str
    customer_id: str
    item_id: str
    return_reason: str  # defective, wrong_item, not_as_described, sizing_issue, changed_mind
    submitted_at: datetime
    decision: str  # auto_approved, flagged_inspection
    risk_score: float
    score_breakdown: dict = field(default_factory=dict)
    hard_rule_triggered: Optional[str] = None
