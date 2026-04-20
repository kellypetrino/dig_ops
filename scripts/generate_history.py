"""
Generates data/returns_history.csv by running 50 return scenarios
through the actual decision engine, so the history is consistent
with the scoring logic.

Run from project root:
    python3 scripts/generate_history.py
"""

import sys
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.models import Customer, Item
from engine.scoring import compute_trust_score, compute_item_risk_score, compute_final_risk_score, route_return
from engine.rules import apply_hard_rules

random.seed(42)

CUSTOMERS = [
    Customer("CUST-001", "Sarah Chen",       950,  85,  8,  0),
    Customer("CUST-002", "Marcus Williams",  820,  60,  5,  0),
    Customer("CUST-003", "Priya Patel",     1100, 120, 14,  0),
    Customer("CUST-004", "James Okafor",     730,  55,  9,  0),
    Customer("CUST-005", "Elena Russo",      900,  70,  6,  0),
    Customer("CUST-006", "Tyler Brooks",     400,  28,  5,  0),
    Customer("CUST-007", "Aisha Nkosi",      320,  22,  4,  0),
    Customer("CUST-008", "Daniel Kim",       500,  35,  7,  0),
    Customer("CUST-009", "Sofia Mendez",     280,  18,  3,  0),
    Customer("CUST-010", "Chris Huang",      450,  30,  6,  0),
    Customer("CUST-011", "Devon Riley",      200,  30, 16,  0),
    Customer("CUST-012", "Rachel Nguyen",    150,  20, 12,  0),
    Customer("CUST-013", "Jordan Lee",       380,  25, 11,  0),
    Customer("CUST-014", "Brianna Scott",     90,  12,  6,  0),
    Customer("CUST-015", "Omar Hassan",      310,  18,  9,  0),
    Customer("CUST-016", "Alex M.",          400,  20, 13,  2),
    Customer("CUST-017", "Tanya Ivanova",     60,   8,  5,  1),
    Customer("CUST-018", "Kevin Marsh",      180,  15, 10,  2),
    Customer("CUST-019", "James Park",        15,   2,  1,  0),
    Customer("CUST-020", "Nina Volkov",       25,   3,  2,  1),
]

ITEMS = [
    Item("ITEM-001", "Cotton T-Shirt",       "apparel",     25.00, "high",   5),
    Item("ITEM-002", "Denim Jacket",         "apparel",     89.00, "high",  12),
    Item("ITEM-003", "Running Shoes",        "apparel",     75.00, "medium",10),
    Item("ITEM-004", "Winter Coat",          "apparel",    180.00, "high",   8),
    Item("ITEM-005", "Wireless Headphones",  "electronics",120.00, "medium",20),
    Item("ITEM-006", "Bluetooth Speaker",    "electronics", 65.00, "high",  15),
    Item("ITEM-007", "Laptop Stand",         "electronics", 45.00, "high",   7),
    Item("ITEM-008", "Smartwatch",           "electronics",320.00, "medium",18),
    Item("ITEM-009", "DSLR Camera",          "electronics",650.00, "high",  14),
    Item("ITEM-010", "Face Serum",           "beauty",      45.00, "none",  22),
    Item("ITEM-011", "Moisturizer Set",      "beauty",      28.00, "none",   9),
    Item("ITEM-012", "Perfume",              "beauty",      90.00, "low",   30),
    Item("ITEM-013", "Electric Toothbrush",  "beauty",      55.00, "low",   11),
    Item("ITEM-014", "Coffee Table Book",    "books",       32.00, "high",  45),
    Item("ITEM-015", "Cookbook",             "books",       24.00, "high",  60),
    Item("ITEM-016", "Textbook",             "books",       85.00, "medium",35),
    Item("ITEM-017", "Throw Blanket",        "home_goods",  38.00, "high",   6),
    Item("ITEM-018", "Scented Candle Set",   "home_goods",  22.00, "medium",14),
    Item("ITEM-019", "Cast Iron Pan",        "home_goods",  75.00, "high",  21),
    Item("ITEM-020", "Air Purifier",         "home_goods", 195.00, "medium", 9),
]

REASONS = ["defective", "wrong_item", "not_as_described", "sizing_issue", "changed_mind"]

# Weight reasons so the distribution looks realistic
REASON_WEIGHTS = [0.20, 0.10, 0.15, 0.25, 0.30]

def generate_return(i: int) -> dict:
    customer = random.choice(CUSTOMERS)
    item = random.choice(ITEMS)
    reason = random.choices(REASONS, weights=REASON_WEIGHTS)[0]

    days_ago = random.randint(0, 29)
    submitted_at = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")

    decision_override, rule_name = apply_hard_rules(customer, item, reason)

    if decision_override:
        return {
            "return_id": f"RET-{1000 + i}",
            "customer": customer.name,
            "item": item.name,
            "category": item.category,
            "return_reason": reason,
            "risk_score": 0.0 if decision_override == "auto_approved" else 100.0,
            "decision": decision_override,
            "hard_rule": rule_name,
            "submitted_at": submitted_at,
        }

    trust = compute_trust_score(customer)
    item_risk = compute_item_risk_score(item)
    score, _ = compute_final_risk_score(trust, item_risk, reason)
    decision = route_return(score)

    return {
        "return_id": f"RET-{1000 + i}",
        "customer": customer.name,
        "item": item.name,
        "category": item.category,
        "return_reason": reason,
        "risk_score": score,
        "decision": decision,
        "hard_rule": "",
        "submitted_at": submitted_at,
    }


if __name__ == "__main__":
    rows = [generate_return(i) for i in range(50)]

    out_path = Path(__file__).parent.parent / "data" / "returns_history.csv"
    fieldnames = ["return_id", "customer", "item", "category", "return_reason",
                  "risk_score", "decision", "hard_rule", "submitted_at"]

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    approved = sum(1 for r in rows if r["decision"] == "auto_approved")
    flagged = len(rows) - approved
    print(f"Generated {len(rows)} returns → {approved} auto-approved, {flagged} flagged")
    print(f"Saved to {out_path}")
