import streamlit as st

from engine.models import Customer, Item
from engine.scoring import compute_trust_score, compute_item_risk_score, compute_final_risk_score, route_return
from engine.rules import apply_hard_rules, RULE_DESCRIPTIONS
from utils.formatters import risk_label, trust_label


# Three hardcoded scenarios designed to show maximum contrast
SCENARIOS = [
    {
        "label": "Scenario A — Trusted Customer",
        "description": "Long-tenured customer, low return rate, company-fault reason. The easy case.",
        "customer": Customer("CUST-001", "Sarah Chen", 950, 85, 8, 0),
        "item": Item("ITEM-001", "Cotton T-Shirt", "apparel", 25.00, "high", 5),
        "reason": "defective",
        "reason_label": "Defective / damaged item",
    },
    {
        "label": "Scenario B — New Account",
        "description": "Brand new account, mid-value electronics, discretionary reason. The borderline case.",
        "customer": Customer("CUST-019", "James Park", 15, 2, 1, 0),
        "item": Item("ITEM-005", "Wireless Headphones", "electronics", 120.00, "medium", 20),
        "reason": "changed_mind",
        "reason_label": "Changed mind",
    },
    {
        "label": "Scenario C — Fraud-Flagged",
        "description": "Multiple fraud flags on record. Hard rule fires before scoring even begins.",
        "customer": Customer("CUST-016", "Alex M.", 400, 20, 13, 2),
        "item": Item("ITEM-003", "Running Shoes", "apparel", 75.00, "medium", 10),
        "reason": "sizing_issue",
        "reason_label": "Sizing / fit issue",
    },
]


def _render_scenario_card(scenario: dict):
    customer = scenario["customer"]
    item = scenario["item"]
    reason = scenario["reason"]

    st.markdown(f"### {scenario['label']}")
    st.caption(scenario["description"])

    # Customer info
    trust = compute_trust_score(customer)
    trust_lbl, trust_color = trust_label(trust)
    st.markdown("**Customer**")
    st.markdown(
        f"<div style='background:#f8f9fa;border-radius:8px;padding:12px;margin-bottom:8px'>"
        f"{customer.name}<br>"
        f"<span style='color:#6b7280;font-size:13px'>"
        f"Tenure: {customer.account_tenure_days} days &nbsp;·&nbsp; "
        f"Return rate: {customer.return_rate:.0%} &nbsp;·&nbsp; "
        f"Fraud flags: {customer.fraud_flags}"
        f"</span><br>"
        f"<span style='color:{trust_color};font-weight:600'>Trust: {trust:.0f} / 100 — {trust_lbl}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Item info
    st.markdown("**Item**")
    st.markdown(
        f"<div style='background:#f8f9fa;border-radius:8px;padding:12px;margin-bottom:8px'>"
        f"{item.name}<br>"
        f"<span style='color:#6b7280;font-size:13px'>"
        f"${item.price:.0f} &nbsp;·&nbsp; {item.category.replace('_',' ').title()} &nbsp;·&nbsp; "
        f"{item.price_tier} tier &nbsp;·&nbsp; resale: {item.resale_viability}"
        f"</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Reason
    st.markdown(f"**Reason:** {scenario['reason_label']}")

    st.markdown("---")

    # Decision
    override, rule_name = apply_hard_rules(customer, item, reason)

    if override:
        decision = override
        decision_color = "#057a55" if decision == "auto_approved" else "#c81e1e"
        decision_label = "INSTANT REFUND APPROVED" if decision == "auto_approved" else "FLAGGED FOR INSPECTION"
        st.markdown(
            f"<div style='font-size:18px;font-weight:700;color:{decision_color}'>{decision_label}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<span style='font-size:13px;color:#6b7280'>Policy override: {RULE_DESCRIPTIONS[rule_name]}</span>",
            unsafe_allow_html=True,
        )
        return

    item_risk = compute_item_risk_score(item)
    score, breakdown = compute_final_risk_score(trust, item_risk, reason)
    decision = route_return(score)

    risk_lbl, risk_color = risk_label(score)
    decision_color = "#057a55" if decision == "auto_approved" else "#c81e1e"
    decision_label = "INSTANT REFUND APPROVED" if decision == "auto_approved" else "FLAGGED FOR INSPECTION"

    st.markdown(
        f"<div style='font-size:18px;font-weight:700;color:{decision_color}'>{decision_label}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<span style='font-size:28px;font-weight:700;color:{risk_color}'>{score:.0f}</span>"
        f"<span style='color:#6b7280'> / 100 &nbsp;—&nbsp; {risk_lbl}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:13px;color:#6b7280;margin-top:4px'>"
        f"Customer {breakdown['trust_contribution']:.1f} + "
        f"Item {breakdown['item_contribution']:.1f} + "
        f"Reason {breakdown['reason_contribution']:.1f} = {score:.1f}"
        f"</div>",
        unsafe_allow_html=True,
    )


def render():
    st.header("Scenario Comparison")
    st.caption(
        "Three contrasting returns — same engine, very different outcomes. "
        "This is the clearest illustration of what the decision engine discriminates on."
    )

    cols = st.columns(3)
    for col, scenario in zip(cols, SCENARIOS):
        with col:
            _render_scenario_card(scenario)
