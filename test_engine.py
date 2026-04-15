"""
Quick smoke tests for the decision engine.
Run with: python test_engine.py
"""

from engine.models import Customer, Item
from engine.scoring import compute_trust_score, compute_item_risk_score, compute_final_risk_score, route_return
from engine.rules import apply_hard_rules


def print_result(label: str, customer: Customer, item: Item, reason: str):
    decision_override, rule_name = apply_hard_rules(customer, item, reason)

    if decision_override:
        print(f"\n{'='*60}")
        print(f"SCENARIO: {label}")
        print(f"  Customer : {customer.name} (fraud_flags={customer.fraud_flags}, return_rate={customer.return_rate:.0%})")
        print(f"  Item     : {item.name} (${item.price}, {item.category})")
        print(f"  Reason   : {reason}")
        print(f"  HARD RULE FIRED: {rule_name}")
        print(f"  DECISION : {decision_override.upper()}")
        return

    trust = compute_trust_score(customer)
    item_risk = compute_item_risk_score(item)
    score, breakdown = compute_final_risk_score(trust, item_risk, reason)
    decision = route_return(score)

    print(f"\n{'='*60}")
    print(f"SCENARIO: {label}")
    print(f"  Customer : {customer.name} (fraud_flags={customer.fraud_flags}, return_rate={customer.return_rate:.0%})")
    print(f"  Item     : {item.name} (${item.price}, {item.category}, tier={item.price_tier})")
    print(f"  Reason   : {reason}")
    print(f"  Trust score      : {trust:.1f}  →  trust risk: {breakdown['trust_risk']:.1f}  →  contribution: {breakdown['trust_contribution']:.1f}")
    print(f"  Item risk score  : {item_risk:.1f}  →  contribution: {breakdown['item_contribution']:.1f}")
    print(f"  Reason modifier  : {breakdown['reason_modifier']:+d}  →  contribution: {breakdown['reason_contribution']:.1f}")
    print(f"  FINAL RISK SCORE : {score:.1f}  (threshold: {breakdown['threshold']})")
    print(f"  DECISION : {decision.upper()}")


# ── Scenario A: Trusted customer + cheap defective item → should auto-approve ──
customer_a = Customer(
    customer_id="CUST-001",
    name="Sarah Chen",
    account_tenure_days=900,
    lifetime_orders=80,
    total_returns=8,
    fraud_flags=0,
)
item_a = Item(
    item_id="ITEM-001",
    name="Cotton T-Shirt",
    category="apparel",
    price=25.0,
    resale_viability="high",
    days_since_purchase=5,
)
print_result("Trusted customer + low-value apparel + defective", customer_a, item_a, "defective")

# ── Scenario B: New account + electronics + changed mind → should flag ──
customer_b = Customer(
    customer_id="CUST-002",
    name="James Park",
    account_tenure_days=15,
    lifetime_orders=2,
    total_returns=1,
    fraud_flags=0,
)
item_b = Item(
    item_id="ITEM-002",
    name="Wireless Headphones",
    category="electronics",
    price=120.0,
    resale_viability="medium",
    days_since_purchase=20,
)
print_result("New account + mid-value electronics + changed mind", customer_b, item_b, "changed_mind")

# ── Scenario C: Fraud-flagged customer → hard rule should fire ──
customer_c = Customer(
    customer_id="CUST-003",
    name="Alex M.",
    account_tenure_days=400,
    lifetime_orders=20,
    total_returns=13,
    fraud_flags=2,
)
item_c = Item(
    item_id="ITEM-003",
    name="Running Shoes",
    category="apparel",
    price=75.0,
    resale_viability="medium",
    days_since_purchase=10,
)
print_result("Fraud-flagged customer (hard rule)", customer_c, item_c, "sizing_issue")

# ── Scenario D: Average customer + high-value item → should flag ──
customer_d = Customer(
    customer_id="CUST-004",
    name="Maria Torres",
    account_tenure_days=500,
    lifetime_orders=25,
    total_returns=5,
    fraud_flags=0,
)
item_d = Item(
    item_id="ITEM-004",
    name="DSLR Camera",
    category="electronics",
    price=650.0,
    resale_viability="high",
    days_since_purchase=14,
)
print_result("Average customer + high-value item ($650) → hard rule", customer_d, item_d, "not_as_described")

# ── Scenario E: High return rate customer + borderline item ──
customer_e = Customer(
    customer_id="CUST-005",
    name="Devon Riley",
    account_tenure_days=200,
    lifetime_orders=30,
    total_returns=16,
    fraud_flags=0,
)
item_e = Item(
    item_id="ITEM-005",
    name="Face Serum",
    category="beauty",
    price=45.0,
    resale_viability="none",
    days_since_purchase=22,
)
print_result("High return rate + beauty + changed mind (borderline)", customer_e, item_e, "changed_mind")

print(f"\n{'='*60}")
print("Done.")
