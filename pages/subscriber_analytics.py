import streamlit as st
from api.data_cache import read_cache
from components.kpi_cards import render_kpi_row
from components.charts import create_donut, create_horizontal_bar, COLORS, PALETTE


def render():
    st.header("Subscriber Analytics")

    crm_available = st.session_state.get("crm_available", False)

    if not crm_available:
        st.warning(
            "FluentCRM is currently unavailable. Subscriber analytics require a FluentCRM connection.",
            icon="\u26a0\ufe0f"
        )
        return

    # Status KPIs
    counts = read_cache("subscriber_counts")
    if not counts:
        st.info("No subscriber data cached. Run prefetch.py first.")
        return

    total = sum(counts.values())

    render_kpi_row([
        {"label": "Total Contacts", "value": f"{total:,}"},
        {"label": "Subscribed", "value": f"{counts.get('subscribed', 0):,}"},
        {"label": "Unsubscribed", "value": f"{counts.get('unsubscribed', 0):,}"},
        {"label": "Pending", "value": f"{counts.get('pending', 0):,}"},
        {"label": "Bounced", "value": f"{counts.get('bounced', 0):,}"},
    ])

    col1, col2 = st.columns(2)

    with col1:
        status_labels = [k for k, v in counts.items() if v > 0]
        status_values = [v for v in counts.values() if v > 0]
        if status_labels:
            status_colors = [COLORS.get(s, PALETTE[0]) for s in status_labels]
            fig = create_donut(status_labels, status_values,
                               title="Contact Status Distribution", colors=status_colors)
            st.plotly_chart(fig, width="stretch")

    with col2:
        tags_data = read_cache("tags")
        if tags_data and "data" in tags_data:
            tags = tags_data["data"]
            if tags:
                tag_labels = [t.get("title", "Unknown") for t in tags[:15]]
                tag_values = [t.get("subscribersCount", 0) for t in tags[:15]]
                fig = create_horizontal_bar(tag_labels, tag_values, title="Subscribers by Tag")
                st.plotly_chart(fig, width="stretch")

    lists_data = read_cache("lists")
    if lists_data and "data" in lists_data:
        lists_items = lists_data["data"]
        if lists_items:
            list_labels = [l.get("title", "Unknown") for l in lists_items[:15]]
            list_values = [l.get("subscribersCount", 0) for l in lists_items[:15]]
            fig = create_horizontal_bar(list_labels, list_values,
                                        title="Subscribers by List", color=COLORS["info"])
            st.plotly_chart(fig, width="stretch")
