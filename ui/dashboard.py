import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from utils.db import load_returns, reset_live_returns, get_config


DECISION_COLORS = {
    "auto_approved": "#057a55",
    "flagged_inspection": "#c81e1e",
}

REASON_LABELS = {
    "defective": "Defective",
    "wrong_item": "Wrong Item",
    "not_as_described": "Not as Described",
    "sizing_issue": "Sizing Issue",
    "changed_mind": "Changed Mind",
}

CATEGORY_LABELS = {
    "electronics": "Electronics",
    "apparel": "Apparel",
    "beauty": "Beauty",
    "home_goods": "Home Goods",
    "books": "Books",
}


def render():
    st.header("Returns Dashboard")
    st.caption("Aggregate view of return decisions across all submissions.")

    df = load_returns()
    threshold = get_config()["threshold"]

    if df.empty:
        st.info("No return data yet. Submit a return on the previous screen to get started.")
        return

    total = len(df)
    approved = (df["decision"] == "auto_approved").sum()
    flagged = (df["decision"] == "flagged_inspection").sum()
    avg_score = df["risk_score"].mean()

    # ── KPI row ────────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Returns", total)
    k2.metric("Auto-Approved", f"{approved} ({approved/total:.0%})")
    k3.metric("Flagged for Inspection", f"{flagged} ({flagged/total:.0%})")
    k4.metric("Avg Risk Score", f"{avg_score:.1f} / 100")

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Decisions by Return Reason")
        reason_df = (
            df.groupby(["return_reason", "decision"])
            .size()
            .reset_index(name="count")
        )
        reason_df["return_reason"] = reason_df["return_reason"].map(REASON_LABELS).fillna(reason_df["return_reason"])
        fig_bar = px.bar(
            reason_df,
            x="return_reason",
            y="count",
            color="decision",
            color_discrete_map=DECISION_COLORS,
            labels={"return_reason": "Return Reason", "count": "# Returns", "decision": "Decision"},
            barmode="stack",
        )
        fig_bar.update_layout(
            legend_title_text="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=30, b=0),
            xaxis_tickangle=-20,
        )
        fig_bar.for_each_trace(lambda t: t.update(
            name="Auto-Approved" if t.name == "auto_approved" else "Flagged"
        ))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("Returns by Category")
        cat_df = df.groupby("category").size().reset_index(name="count")
        cat_df["category"] = cat_df["category"].map(CATEGORY_LABELS).fillna(cat_df["category"])
        fig_pie = px.pie(
            cat_df,
            names="category",
            values="count",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4,
        )
        fig_pie.update_layout(margin=dict(t=30, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # ── Risk score distribution ────────────────────────────────────────────────
    st.subheader("Risk Score Distribution")
    scored_df = df[df["hard_rule"].isna() | (df["hard_rule"] == "")]
    fig_hist = px.histogram(
        scored_df,
        x="risk_score",
        color="decision",
        color_discrete_map=DECISION_COLORS,
        nbins=20,
        labels={"risk_score": "Risk Score", "count": "# Returns", "decision": "Decision"},
    )
    fig_hist.add_vline(x=threshold, line_dash="dash", line_color="#6b7280",
                       annotation_text=f"Threshold ({threshold:.0f})", annotation_position="top right")
    fig_hist.update_layout(
        legend_title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=30, b=0),
        bargap=0.1,
    )
    fig_hist.for_each_trace(lambda t: t.update(
        name="Auto-Approved" if t.name == "auto_approved" else "Flagged"
    ))
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")

    # ── Returns table ──────────────────────────────────────────────────────────
    st.subheader("All Returns")

    col_filter1, col_filter2, _ = st.columns([1, 1, 2])
    with col_filter1:
        decision_filter = st.selectbox("Filter by decision", ["All", "Auto-Approved", "Flagged"])
    with col_filter2:
        reason_filter = st.selectbox("Filter by reason", ["All"] + list(REASON_LABELS.values()))

    display_df = df.copy()
    if decision_filter == "Auto-Approved":
        display_df = display_df[display_df["decision"] == "auto_approved"]
    elif decision_filter == "Flagged":
        display_df = display_df[display_df["decision"] == "flagged_inspection"]

    if reason_filter != "All":
        reason_key = [k for k, v in REASON_LABELS.items() if v == reason_filter][0]
        display_df = display_df[display_df["return_reason"] == reason_key]

    display_df = display_df.copy()
    display_df["return_reason"] = display_df["return_reason"].map(REASON_LABELS).fillna(display_df["return_reason"])
    display_df["decision"] = display_df["decision"].map({
        "auto_approved": "✅ Auto-Approved",
        "flagged_inspection": "🔴 Flagged",
    }).fillna(display_df["decision"])

    st.dataframe(
        display_df[["return_id", "customer", "item", "return_reason", "risk_score", "decision", "submitted_at"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "return_id": "Return ID",
            "customer": "Customer",
            "item": "Item",
            "return_reason": "Reason",
            "risk_score": st.column_config.NumberColumn("Risk Score", format="%.1f"),
            "decision": "Decision",
            "submitted_at": "Submitted",
        },
    )

    # ── Download ───────────────────────────────────────────────────────────────
    st.download_button(
        label="Download returns as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"returns_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

    # ── Admin ──────────────────────────────────────────────────────────────────
    with st.expander("Admin"):
        st.caption("Reset removes all live submissions. Seed data (50 historical returns) is preserved.")
        if st.button("Reset live returns", type="secondary"):
            reset_live_returns()
            st.rerun()
