import streamlit as st
from datetime import datetime

from engine.models import Customer, Item
from engine.scoring import compute_trust_score, compute_item_risk_score, compute_final_risk_score, route_return
from engine.rules import apply_hard_rules, RULE_DESCRIPTIONS
from utils.data_loader import load_customers, load_items
from utils.formatters import decision_badge, risk_label, trust_label


RETURN_REASONS = {
    "defective": "Defective / damaged item",
    "wrong_item": "Wrong item shipped",
    "not_as_described": "Not as described",
    "sizing_issue": "Sizing / fit issue",
    "changed_mind": "Changed mind",
}


def render():
    st.header("Submit a Return")
    st.caption("Select a customer and item to see how the decision engine routes the return in real time.")

    customers_df = load_customers()
    items_df = load_items()

    col_left, col_right = st.columns(2)

    # ── Customer selector ──────────────────────────────────────────────────────
    with col_left:
        st.subheader("Customer")
        customer_name = st.selectbox(
            "Select customer",
            options=customers_df["name"].tolist(),
            key="customer_select",
        )
        crow = customers_df[customers_df["name"] == customer_name].iloc[0]
        customer = Customer(
            customer_id=crow["customer_id"],
            name=crow["name"],
            account_tenure_days=int(crow["account_tenure_days"]),
            lifetime_orders=int(crow["lifetime_orders"]),
            total_returns=int(crow["total_returns"]),
            fraud_flags=int(crow["fraud_flags"]),
        )
        trust = compute_trust_score(customer)
        trust_lbl, trust_color = trust_label(trust)

        st.markdown(
            f"""
            <div style="background:#f8f9fa;border-radius:8px;padding:16px;margin-top:8px">
                <div style="font-size:13px;color:#6b7280">Account tenure</div>
                <div style="font-size:16px;font-weight:600">{customer.account_tenure_days} days</div>
                <div style="font-size:13px;color:#6b7280;margin-top:8px">Return rate</div>
                <div style="font-size:16px;font-weight:600">{customer.return_rate:.0%}
                    ({customer.total_returns} of {customer.lifetime_orders} orders)
                </div>
                <div style="font-size:13px;color:#6b7280;margin-top:8px">Fraud flags</div>
                <div style="font-size:16px;font-weight:600">{customer.fraud_flags}</div>
                <div style="font-size:13px;color:#6b7280;margin-top:8px">Trust score</div>
                <div style="font-size:20px;font-weight:700;color:{trust_color}">{trust:.0f} / 100
                    <span style="font-size:13px;font-weight:400"> — {trust_lbl}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Item selector ──────────────────────────────────────────────────────────
    with col_right:
        st.subheader("Item")
        item_name = st.selectbox(
            "Select item",
            options=items_df["name"].tolist(),
            key="item_select",
        )
        irow = items_df[items_df["name"] == item_name].iloc[0]
        item = Item(
            item_id=irow["item_id"],
            name=irow["name"],
            category=irow["category"],
            price=float(irow["price"]),
            resale_viability=irow["resale_viability"],
            days_since_purchase=int(irow["days_since_purchase"]),
        )

        st.markdown(
            f"""
            <div style="background:#f8f9fa;border-radius:8px;padding:16px;margin-top:8px">
                <div style="font-size:13px;color:#6b7280">Category</div>
                <div style="font-size:16px;font-weight:600">{item.category.replace("_", " ").title()}</div>
                <div style="font-size:13px;color:#6b7280;margin-top:8px">Price</div>
                <div style="font-size:16px;font-weight:600">${item.price:.2f}
                    <span style="font-size:13px;font-weight:400;color:#6b7280"> ({item.price_tier} tier)</span>
                </div>
                <div style="font-size:13px;color:#6b7280;margin-top:8px">Resale viability</div>
                <div style="font-size:16px;font-weight:600">{item.resale_viability.title()}</div>
                <div style="font-size:13px;color:#6b7280;margin-top:8px">Days since purchase</div>
                <div style="font-size:16px;font-weight:600">{item.days_since_purchase} days</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Return reason ──────────────────────────────────────────────────────────
    st.markdown("---")
    reason_label = st.selectbox(
        "Return reason",
        options=list(RETURN_REASONS.values()),
        key="reason_select",
    )
    reason_key = [k for k, v in RETURN_REASONS.items() if v == reason_label][0]

    # ── Submit ─────────────────────────────────────────────────────────────────
    submitted = st.button("Submit Return for Decision", type="primary", use_container_width=True)

    if submitted:
        _show_decision(customer, item, reason_key)


def _show_decision(customer: Customer, item: Item, reason: str):
    st.markdown("---")
    st.subheader("Decision")

    decision_override, rule_name = apply_hard_rules(customer, item, reason)

    if decision_override:
        # Hard rule fired
        decision = decision_override
        badge = decision_badge(decision)
        badge_color = "#057a55" if decision == "auto_approved" else "#c81e1e"

        st.markdown(
            f"<div style='font-size:24px;font-weight:700;color:{badge_color};padding:16px 0'>{badge}</div>",
            unsafe_allow_html=True,
        )
        st.info(f"**Policy override:** {RULE_DESCRIPTIONS[rule_name]}")

        _save_to_session(customer, item, reason, decision, 0.0 if decision == "auto_approved" else 100.0, {}, rule_name)
        return

    # Score-based routing
    trust = compute_trust_score(customer)
    item_risk = compute_item_risk_score(item)
    score, breakdown = compute_final_risk_score(trust, item_risk, reason)
    decision = route_return(score)

    risk_lbl, risk_color = risk_label(score)
    badge = decision_badge(decision)
    badge_color = "#057a55" if decision == "auto_approved" else "#c81e1e"

    col_decision, col_score = st.columns([2, 1])

    with col_decision:
        st.markdown(
            f"<div style='font-size:24px;font-weight:700;color:{badge_color};padding:16px 0'>{badge}</div>",
            unsafe_allow_html=True,
        )

    with col_score:
        st.metric("Risk Score", f"{score:.0f} / 100", help="Score below 45 = auto-approved. 45 or above = flagged.")
        st.markdown(
            f"<span style='color:{risk_color};font-weight:600'>{risk_lbl}</span>",
            unsafe_allow_html=True,
        )

    # Score breakdown table
    st.markdown("#### Score Breakdown")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Customer Trust**")
        st.markdown(f"Trust score: **{breakdown['trust_score']:.0f}** → risk: **{breakdown['trust_risk']:.0f}**")
        st.markdown(f"Weight: 40% → contribution: **{breakdown['trust_contribution']:.1f}**")

    with col2:
        st.markdown("**Item Risk**")
        st.markdown(f"Item risk score: **{breakdown['item_risk_score']:.0f}**")
        st.markdown(f"Weight: 35% → contribution: **{breakdown['item_contribution']:.1f}**")

    with col3:
        st.markdown("**Return Reason**")
        modifier = breakdown['reason_modifier']
        sign = "+" if modifier >= 0 else ""
        st.markdown(f"Modifier: **{sign}{modifier}** → component: **{breakdown['reason_component']:.0f}**")
        st.markdown(f"Weight: 25% → contribution: **{breakdown['reason_contribution']:.1f}**")

    st.markdown(
        f"<div style='background:#f8f9fa;border-radius:8px;padding:12px;margin-top:8px;font-size:15px'>"
        f"<b>Final risk score:</b> {breakdown['trust_contribution']:.1f} + {breakdown['item_contribution']:.1f} + {breakdown['reason_contribution']:.1f} = <b style='color:{risk_color}'>{score:.1f}</b> "
        f"(threshold: {breakdown['threshold']})"
        f"</div>",
        unsafe_allow_html=True,
    )

    _save_to_session(customer, item, reason, decision, score, breakdown, None)


def _save_to_session(customer, item, reason, decision, score, breakdown, rule_name):
    if "new_returns" not in st.session_state:
        st.session_state["new_returns"] = []

    import random
    return_id = f"RET-{random.randint(1000, 9999)}"

    st.session_state["new_returns"].append({
        "return_id": return_id,
        "customer": customer.name,
        "item": item.name,
        "category": item.category,
        "return_reason": reason,
        "risk_score": round(score, 1),
        "decision": decision,
        "hard_rule": rule_name or "",
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
