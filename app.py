import streamlit as st
from datetime import date
from api.data_cache import read_cache, get_cache_timestamp

st.set_page_config(
    page_title="Save Our Clubs - Campaign Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
with st.sidebar:
    st.markdown("## Save Our Clubs")
    st.caption("saveourclubs.nz - Campaign Analytics")
    st.divider()

    # Data timestamp
    cache_ts = get_cache_timestamp()
    if cache_ts:
        st.caption(f"Data as of: {cache_ts}")
    else:
        st.warning("No cached data. Run prefetch.py first.")

    # Fixed defaults
    st.session_state["from_date"] = "2026-03-24"
    st.session_state["to_date"] = date.today().strftime("%Y-%m-%d")
    st.session_state["message_stream"] = None

    # CRM availability from cache
    crm_available = read_cache("crm_available")
    st.session_state["crm_available"] = crm_available if crm_available is not None else False


# --- Page Navigation ---
from pages.executive_summary import render as executive_summary
from pages.email_performance import render as email_performance
from pages.subscriber_analytics import render as subscriber_analytics
from pages.engagement_trends import render as engagement_trends

pg = st.navigation([
    st.Page(executive_summary, title="Executive Summary", icon=":material/dashboard:", url_path="summary"),
    st.Page(email_performance, title="Email Performance", icon=":material/email:", url_path="email"),
    st.Page(subscriber_analytics, title="Subscribers", icon=":material/group:", url_path="subscribers"),
    st.Page(engagement_trends, title="Engagement Trends", icon=":material/trending_up:", url_path="trends"),
])
pg.run()
