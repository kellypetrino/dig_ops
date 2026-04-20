import streamlit as st

st.set_page_config(
    page_title="Instant Refund Decision Engine",
    page_icon="↩️",
    layout="wide",
)

from ui import submit_return, dashboard

SCREENS = {
    "Submit a Return": submit_return,
    "Dashboard": dashboard,
}

st.sidebar.title("↩️ Refund Engine")
st.sidebar.caption("HBS Digital Operations — Spring 2026")
st.sidebar.markdown("---")

screen = st.sidebar.radio("Navigate", list(SCREENS.keys()))

SCREENS[screen].render()
