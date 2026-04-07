import streamlit as st
import pandas as pd
from api.data_cache import read_cache
from components.kpi_cards import render_kpi_row
from components.charts import create_funnel, create_donut, create_combo_chart, COLORS


def render():
    st.header("Executive Summary")
    st.caption("At-a-glance campaign performance for media briefings")

    overview = read_cache("overview")
    if not overview:
        st.error("No cached data available. Run prefetch.py first.")
        return

    sent = overview.get("Sent", 0)
    bounced = overview.get("Bounced", 0)
    unique_opens = overview.get("UniqueOpens", 0)
    unique_clicks = overview.get("UniqueLinksClicked", 0)
    spam = overview.get("SpamComplaints", 0)

    open_rate = (unique_opens / sent * 100) if sent > 0 else 0
    click_rate = (unique_clicks / sent * 100) if sent > 0 else 0
    bounce_rate = (bounced / sent * 100) if sent > 0 else 0

    # Row 1: Email KPIs
    render_kpi_row([
        {"label": "Emails Sent", "value": f"{sent:,}"},
        {"label": "Unique Opens", "value": f"{unique_opens:,}"},
        {"label": "Open Rate", "value": f"{open_rate:.1f}%"},
        {"label": "Unique Clicks", "value": f"{unique_clicks:,}"},
        {"label": "Click Rate", "value": f"{click_rate:.1f}%"},
        {"label": "Bounce Rate", "value": f"{bounce_rate:.1f}%", "delta_color": "inverse"},
    ])

    # Row 2: FluentCRM KPIs (if available)
    if st.session_state.get("crm_available"):
        sub_data = read_cache("subscriber_counts")
        if sub_data:
            total_subs = sum(sub_data.values())
            render_kpi_row([
                {"label": "Total Contacts", "value": f"{total_subs:,}"},
                {"label": "Subscribed", "value": f"{sub_data.get('subscribed', 0):,}"},
                {"label": "Unsubscribed", "value": f"{sub_data.get('unsubscribed', 0):,}"},
                {"label": "Pending", "value": f"{sub_data.get('pending', 0):,}"},
            ])

    # Row 3: Daily trends + Engagement funnel
    col1, col2 = st.columns([3, 2])

    with col1:
        sends_data = read_cache("sends")
        opens_data = read_cache("opens")
        if sends_data and opens_data:
            sends_days = sends_data.get("Days", [])
            opens_days = opens_data.get("Days", [])

            sends_map = {d["Date"][:10]: d["Sent"] for d in sends_days}
            opens_map = {d["Date"][:10]: d.get("Unique", 0) for d in opens_days}
            all_dates = sorted(set(sends_map.keys()) | set(opens_map.keys()))

            df = pd.DataFrame({
                "Date": all_dates,
                "Sent": [sends_map.get(d, 0) for d in all_dates],
                "Unique Opens": [opens_map.get(d, 0) for d in all_dates],
            })

            fig = create_combo_chart(df, "Date", "Sent", "Unique Opens",
                                     title="Daily Sends & Opens")
            st.plotly_chart(fig, width="stretch")

    with col2:
        stages = [
            {"label": "Sent", "value": sent, "color_key": "sent"},
            {"label": "Opened", "value": unique_opens, "color_key": "opened"},
            {"label": "Clicked", "value": unique_clicks, "color_key": "clicked"},
        ]
        fig = create_funnel(stages, title="Engagement Funnel")
        st.plotly_chart(fig, width="stretch")

    # Row 4: Bounce breakdown
    bounces_data = read_cache("bounces")
    if bounces_data:
        days = bounces_data.get("Days", [])
        bounce_types = {}
        for day in days:
            for key, val in day.items():
                if key != "Date" and val > 0:
                    bounce_types[key] = bounce_types.get(key, 0) + val
        if bounce_types:
            labels = list(bounce_types.keys())
            values = list(bounce_types.values())
            bounce_colors = [COLORS.get("bounced"), COLORS.get("unsubscribed"),
                             COLORS.get("pending"), COLORS.get("info")]
            fig = create_donut(labels, values, title="Bounce Breakdown",
                               colors=bounce_colors)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No bounces in selected period.")
    if spam > 0:
        st.metric("Spam Complaints", spam)
