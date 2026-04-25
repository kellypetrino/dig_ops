import streamlit as st
import pandas as pd

from utils.db import load_pending_inspection, resolve_return, count_pending_inspection

REASON_LABELS = {
    "defective": "Defective / damaged item",
    "wrong_item": "Wrong item shipped",
    "not_as_described": "Not as described",
    "sizing_issue": "Sizing / fit issue",
    "changed_mind": "Changed mind",
}


def render():
    st.header("Inspection Queue")

    pending_df = load_pending_inspection()
    resolved_df = _load_resolved()

    pending_count = len(pending_df)

    if pending_count == 0:
        st.success("Queue is clear — no returns pending inspection.")
    else:
        st.caption(
            f"{pending_count} return{'s' if pending_count != 1 else ''} awaiting inspection. "
            "Approve after physical review, or confirm fraud to update the customer's record."
        )

    # ── Pending returns ────────────────────────────────────────────────────────
    if not pending_df.empty:
        for _, row in pending_df.iterrows():
            _render_queue_card(row)

    # ── Resolved returns ───────────────────────────────────────────────────────
    if not resolved_df.empty:
        st.markdown("---")
        with st.expander(f"Resolved ({len(resolved_df)})"):
            for _, row in resolved_df.iterrows():
                _render_resolved_row(row)


def _render_queue_card(row: pd.Series):
    reason_label = REASON_LABELS.get(row["return_reason"], row["return_reason"])
    risk_score = row["risk_score"]
    hard_rule = row.get("hard_rule", "")

    with st.container():
        st.markdown(
            f"""
            <div style="border:1px solid #e5e7eb;border-left:4px solid #c81e1e;
                        border-radius:8px;padding:16px;margin-bottom:12px;background:#fff">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                        <div style="font-size:16px;font-weight:700">{row['customer']}</div>
                        <div style="font-size:14px;color:#374151;margin-top:2px">
                            {row['item']} &nbsp;·&nbsp;
                            {row['category'].replace('_',' ').title()} &nbsp;·&nbsp;
                            {reason_label}
                        </div>
                        <div style="font-size:12px;color:#6b7280;margin-top:4px">
                            {row['return_id']} &nbsp;·&nbsp; Submitted {row['submitted_at']}
                        </div>
                    </div>
                    <div style="text-align:right">
                        <div style="font-size:22px;font-weight:700;color:#c81e1e">
                            {"—" if hard_rule else f"{risk_score:.0f}"}
                        </div>
                        <div style="font-size:11px;color:#6b7280">
                            {"policy override" if hard_rule else "risk score"}
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_approve, col_fraud, col_spacer = st.columns([1, 1, 3])
        with col_approve:
            if st.button("Approve", key=f"approve_{row['return_id']}", type="primary"):
                resolve_return(row["return_id"], "inspection_approved")
                st.success(f"{row['return_id']} approved. Refund issued.")
                st.rerun()
        with col_fraud:
            if st.button("Confirm Fraud", key=f"fraud_{row['return_id']}", type="secondary"):
                resolve_return(row["return_id"], "fraud_confirmed")
                st.warning(f"{row['return_id']} flagged as fraud. Customer record updated.")
                st.rerun()

        st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)


def _render_resolved_row(row: pd.Series):
    status = row.get("status", "")
    if status == "inspection_approved":
        badge = "✅ Approved after inspection"
        color = "#057a55"
    elif status == "fraud_confirmed":
        badge = "🚫 Fraud confirmed"
        color = "#c81e1e"
    else:
        badge = status
        color = "#6b7280"

    reason_label = REASON_LABELS.get(row["return_reason"], row["return_reason"])

    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:10px 12px;border-radius:6px;background:#f8f9fa;margin-bottom:6px">
            <div style="font-size:13px">
                <span style="font-weight:600">{row['customer']}</span>
                &nbsp;·&nbsp; {row['item']} &nbsp;·&nbsp; {reason_label}
                <span style="color:#9ca3af"> — {row['return_id']}</span>
            </div>
            <div style="font-size:13px;font-weight:600;color:{color}">{badge}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _load_resolved() -> pd.DataFrame:
    """Load returns that have been resolved through the inspection queue."""
    from utils.db import load_returns
    df = load_returns()
    if df.empty:
        return pd.DataFrame()
    return df[df["status"].isin(["inspection_approved", "fraud_confirmed"])].sort_values(
        "submitted_at", ascending=False
    )
