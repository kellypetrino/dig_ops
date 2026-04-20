import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from engine.models import Customer, Item
from engine.scoring import (
    compute_trust_score,
    compute_item_risk_score,
    compute_final_risk_score,
    route_return,
    REASON_RISK_MODIFIER,
)
from engine.rules import apply_hard_rules
from utils.data_loader import load_customers, load_items


RETURN_REASONS = {
    "defective": "Defective / damaged item",
    "wrong_item": "Wrong item shipped",
    "not_as_described": "Not as described",
    "sizing_issue": "Sizing / fit issue",
    "changed_mind": "Changed mind",
}

# Preset example scenario for the interactive section
PRESET_CUSTOMER = Customer("CUST-008", "Daniel Kim", 500, 35, 7, 0)
PRESET_ITEM = Item("ITEM-005", "Wireless Headphones", "electronics", 120.00, "medium", 20)
PRESET_REASON = "sizing_issue"


def render():
    st.header("Score Explainer")
    st.caption("Understand how the engine scores a return and what happens when you change the rules.")

    # ── Section 1: How the formula works ──────────────────────────────────────
    st.subheader("How the Score is Calculated")

    st.markdown("""
    Every return is evaluated across three dimensions, each producing a component score.
    Those components are combined into a single **risk score (0–100)**. Returns below the
    threshold are auto-approved; at or above are flagged for inspection.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **Customer Trust (40%)**
        Starts at 100. Penalized for high return rates, fraud flags, and new accounts.
        Inverted to a *risk* score before combining — a trust score of 80 becomes a
        customer risk of 20.
        """)
    with col2:
        st.markdown("""
        **Item Risk (35%)**
        Starts at 0. Points added for higher price tier, riskier category (electronics
        > beauty > apparel), low resale viability, and older purchase dates.
        """)
    with col3:
        st.markdown("""
        **Return Reason (25%)**
        Centers at 50. Defective and wrong-item returns are discounted (company fault).
        Changed-mind returns are penalized (discretionary, higher scrutiny).
        """)

    st.markdown("""
    ```
    final_score = (100 − trust_score) × 0.40
                + item_risk_score     × 0.35
                + (50 + reason_mod)   × 0.25
    ```
    """)

    st.markdown("---")

    # ── Section 2: Interactive weight adjustment ───────────────────────────────
    st.subheader("Adjust the Weights")
    st.caption(
        "Drag the sliders to change how much each dimension contributes. "
        "Watch how it changes the decision for the example scenario below."
    )

    col_sliders, col_preview = st.columns([1, 1])

    with col_sliders:
        w_trust = st.slider("Customer trust weight", 0, 100, 40, step=5, key="w_trust") / 100
        w_item = st.slider("Item risk weight", 0, 100, 35, step=5, key="w_item") / 100
        w_reason = st.slider("Return reason weight", 0, 100, 25, step=5, key="w_reason") / 100
        total_weight = w_trust + w_item + w_reason

        if abs(total_weight - 1.0) > 0.01:
            st.warning(f"Weights sum to {total_weight:.0%} — they should sum to 100%. Scores will be scaled accordingly.")

        threshold = st.slider("Approval threshold", 20, 70, 45, step=5, key="threshold")

    with col_preview:
        st.markdown("**Example scenario**")
        st.markdown(f"Customer: *{PRESET_CUSTOMER.name}* — 500 day tenure, 20% return rate, 0 fraud flags")
        st.markdown(f"Item: *{PRESET_ITEM.name}* — ${PRESET_ITEM.price}, electronics, mid tier")
        st.markdown(f"Reason: *{RETURN_REASONS[PRESET_REASON]}*")
        st.markdown("---")

        override, rule = apply_hard_rules(PRESET_CUSTOMER, PRESET_ITEM, PRESET_REASON)
        if override:
            st.info(f"Hard rule fires: {rule} — scoring skipped")
        else:
            weights = {"trust": w_trust, "item": w_item, "reason": w_reason}
            trust = compute_trust_score(PRESET_CUSTOMER)
            item_risk = compute_item_risk_score(PRESET_ITEM)
            score, breakdown = compute_final_risk_score(trust, item_risk, PRESET_REASON, weights=weights)
            decision = route_return(score, threshold=threshold)

            decision_color = "#057a55" if decision == "auto_approved" else "#c81e1e"
            decision_label = "INSTANT REFUND APPROVED" if decision == "auto_approved" else "FLAGGED FOR INSPECTION"

            st.markdown(
                f"<div style='font-size:22px;font-weight:700;color:{decision_color}'>{decision_label}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**Risk score: {score:.1f}** (threshold: {threshold})")
            st.markdown(
                f"Contributions: "
                f"customer {breakdown['trust_contribution']:.1f} + "
                f"item {breakdown['item_contribution']:.1f} + "
                f"reason {breakdown['reason_contribution']:.1f}"
            )

    st.markdown("---")

    # ── Section 3: Threshold sensitivity ──────────────────────────────────────
    st.subheader("Threshold Sensitivity")
    st.caption(
        "How many of the 50 seeded returns would flip their decision at each threshold value? "
        "The vertical line shows the current threshold from the slider above."
    )

    _render_sensitivity_chart(
        w_trust=w_trust, w_item=w_item, w_reason=w_reason, current_threshold=threshold
    )

    st.markdown("---")

    # ── Section 4: Reason modifier reference ──────────────────────────────────
    st.subheader("Return Reason Modifiers")
    reason_rows = []
    for key, label in RETURN_REASONS.items():
        mod = REASON_RISK_MODIFIER.get(key, 0)
        component = 50 + mod
        sign = "+" if mod >= 0 else ""
        reason_rows.append({
            "Reason": label,
            "Modifier": f"{sign}{mod}",
            "Component score": component,
            "Effect": "Increases risk" if mod > 0 else ("Reduces risk" if mod < 0 else "Neutral"),
        })
    st.dataframe(pd.DataFrame(reason_rows), use_container_width=True, hide_index=True)


def _render_sensitivity_chart(w_trust: float, w_item: float, w_reason: float, current_threshold: int):
    """For each threshold from 20–70, count how many of the 50 seeded returns
    would be auto-approved vs flagged, using the current weights."""

    customers_df = load_customers()
    items_df = load_items()

    # Rebuild customer/item objects from CSVs (same as history generator)
    from engine.models import Customer, Item as ItemModel
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.generate_history import CUSTOMERS, ITEMS, REASONS, REASON_WEIGHTS
    import random
    random.seed(42)

    scored = []
    for i in range(50):
        customer = random.choice(CUSTOMERS)
        item = random.choice(ITEMS)
        reason = random.choices(REASONS, weights=REASON_WEIGHTS)[0]
        override, _ = apply_hard_rules(customer, item, reason)
        if override:
            continue
        trust = compute_trust_score(customer)
        item_risk = compute_item_risk_score(item)
        score, _ = compute_final_risk_score(
            trust, item_risk, reason,
            weights={"trust": w_trust, "item": w_item, "reason": w_reason}
        )
        scored.append(score)

    thresholds = list(range(20, 75, 5))
    approved_counts = [sum(1 for s in scored if s < t) for t in thresholds]
    flagged_counts = [len(scored) - a for a, t in zip(approved_counts, thresholds)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=thresholds, y=approved_counts,
        mode="lines+markers", name="Auto-Approved",
        line=dict(color="#057a55", width=2),
        marker=dict(size=7),
    ))
    fig.add_trace(go.Scatter(
        x=thresholds, y=flagged_counts,
        mode="lines+markers", name="Flagged",
        line=dict(color="#c81e1e", width=2),
        marker=dict(size=7),
    ))
    fig.add_vline(
        x=current_threshold, line_dash="dash", line_color="#6b7280",
        annotation_text=f"Current: {current_threshold}",
        annotation_position="top right",
    )
    fig.update_layout(
        xaxis_title="Approval Threshold",
        yaxis_title="Number of Returns",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)
