import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Instant Refund Decision Engine",
    page_icon="↩️",
    layout="wide",
)

from utils import db
from ui import submit_return, dashboard, explainer, scenarios, inspection_queue

DATA_DIR = Path(__file__).parent / "data"
db.init_db(DATA_DIR / "returns_history.csv")

pending = db.count_pending_inspection()
queue_label = f"Inspection Queue ({pending})" if pending > 0 else "Inspection Queue"

SCREENS = {
    "Submit a Return": submit_return,
    "Dashboard": dashboard,
    queue_label: inspection_queue,
    "Score Explainer": explainer,
    "Scenario Comparison": scenarios,
}

st.sidebar.title("↩️ Refund Engine")
st.sidebar.caption("HBS Digital Operations — Spring 2026")
st.sidebar.markdown("---")

screen = st.sidebar.radio("Navigate", list(SCREENS.keys()))

live_count = db.count_live_returns()
if live_count > 0:
    st.sidebar.caption(f"{live_count} return{'s' if live_count != 1 else ''} submitted this session")

SCREENS[screen].render()
