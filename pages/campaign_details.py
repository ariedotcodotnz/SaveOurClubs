import streamlit as st
import pandas as pd
from api.fluentcrm import FluentCRMClient
from api.postmark import PostmarkClient
from components.kpi_cards import render_kpi_row
from components.charts import create_horizontal_bar, create_donut, COLORS


@st.cache_data(ttl=600)
def _fetch_campaigns():
    return FluentCRMClient().get_campaigns(per_page=100, with_stats=True)


@st.cache_data(ttl=600)
def _fetch_campaign_links(campaign_id):
    return FluentCRMClient().get_campaign_links(campaign_id)


@st.cache_data(ttl=600)
def _fetch_campaign_unsubscribes(campaign_id):
    return FluentCRMClient().get_campaign_unsubscribes(campaign_id)


@st.cache_data(ttl=300)
def _fetch_broadcast_subjects(from_date, to_date):
    """Fallback: group broadcast messages by subject."""
    client = PostmarkClient()
    subjects = {}
    for offset in range(0, 1000, 100):
        data = client.search_messages(
            count=100, offset=offset, message_stream="broadcast",
            from_date=from_date, to_date=to_date,
        )
        if not data or not data.get("Messages"):
            break
        for msg in data["Messages"]:
            subj = msg.get("Subject", "Unknown")
            if subj not in subjects:
                subjects[subj] = {"count": 0, "message_ids": [], "date": msg.get("ReceivedAt", "")[:10]}
            subjects[subj]["count"] += 1
            msg_id = msg.get("MessageID", "")
            if msg_id:
                subjects[subj]["message_ids"].append(msg_id)
        if len(data["Messages"]) < 100:
            break
    return subjects


@st.cache_data(ttl=300)
def _fetch_overview_for_stream(from_date, to_date, stream):
    return PostmarkClient().get_overview_stats(from_date, to_date, message_stream=stream)


def render():
    st.header("Campaign Details")

    crm_available = st.session_state.get("crm_available", False)
    fd = st.session_state.get("from_date")
    td = st.session_state.get("to_date")

    if crm_available:
        _render_fluentcrm_campaigns()
    else:
        _render_postmark_campaigns(fd, td)


def _render_fluentcrm_campaigns():
    campaigns_data = _fetch_campaigns()
    if not campaigns_data or "data" not in campaigns_data:
        st.warning("Unable to load campaigns from FluentCRM.")
        return

    campaigns = campaigns_data["data"]
    if not campaigns:
        st.info("No campaigns found.")
        return

    # Campaign selector
    campaign_options = {
        f"{c.get('title', 'Untitled')} ({c.get('status', '')})": c
        for c in campaigns
    }
    selected_name = st.selectbox("Select Campaign", list(campaign_options.keys()))
    campaign = campaign_options[selected_name]
    campaign_id = campaign.get("id")

    # Campaign stats
    stats = campaign.get("stats", {})
    sent = stats.get("sent", 0) or stats.get("total", 0)
    opens = stats.get("views", 0)
    clicks = stats.get("clicks", 0)
    unsubs = stats.get("unsubscribers", 0)
    open_rate = round(opens / sent * 100, 1) if sent > 0 else 0
    click_rate = round(clicks / sent * 100, 1) if sent > 0 else 0

    render_kpi_row([
        {"label": "Recipients", "value": f"{sent:,}"},
        {"label": "Opens", "value": f"{opens:,}"},
        {"label": "Open Rate", "value": f"{open_rate}%"},
        {"label": "Clicks", "value": f"{clicks:,}"},
        {"label": "Click Rate", "value": f"{click_rate}%"},
        {"label": "Unsubscribes", "value": f"{unsubs:,}"},
    ])

    col1, col2 = st.columns(2)

    # Link performance
    with col1:
        links_data = _fetch_campaign_links(campaign_id)
        if links_data and isinstance(links_data, list):
            if links_data:
                st.subheader("Link Performance")
                rows = []
                for link in links_data:
                    rows.append({
                        "URL": (link.get("url", "") or "")[:60],
                        "Clicks": link.get("clicks", 0),
                        "Unique Clicks": link.get("unique_clicks", 0),
                    })
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        elif links_data and "data" in links_data:
            links = links_data["data"]
            if links:
                st.subheader("Link Performance")
                rows = []
                for link in links:
                    rows.append({
                        "URL": (link.get("url", "") or link.get("link", ""))[:60],
                        "Clicks": link.get("clicks", link.get("click_count", 0)),
                    })
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    # Unsubscribes
    with col2:
        unsub_data = _fetch_campaign_unsubscribes(campaign_id)
        if unsub_data and "data" in unsub_data:
            unsubs = unsub_data["data"]
            if unsubs:
                st.subheader("Unsubscribes")
                rows = []
                for u in unsubs:
                    rows.append({
                        "Email": u.get("email", ""),
                        "Name": f"{u.get('first_name', '')} {u.get('last_name', '')}".strip(),
                    })
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            else:
                st.success("No unsubscribes for this campaign.")

    # Campaign metadata
    with st.expander("Campaign Info"):
        st.markdown(f"**Status:** {campaign.get('status', 'Unknown')}")
        st.markdown(f"**Type:** {campaign.get('type', 'Unknown')}")
        st.markdown(f"**Created:** {campaign.get('created_at', 'Unknown')}")
        st.markdown(f"**Subject:** {campaign.get('email_subject', campaign.get('title', ''))}")


def _render_postmark_campaigns(from_date, to_date):
    st.info(
        "Showing campaign data from Postmark broadcast messages (FluentCRM unavailable).",
        icon="\u2139\ufe0f"
    )

    # Overall broadcast stats
    broadcast_stats = _fetch_overview_for_stream(from_date, to_date, "broadcast")
    if broadcast_stats:
        sent = broadcast_stats.get("Sent", 0)
        unique_opens = broadcast_stats.get("UniqueOpens", 0)
        unique_clicks = broadcast_stats.get("UniqueLinksClicked", 0)
        bounced = broadcast_stats.get("Bounced", 0)
        open_rate = round(unique_opens / sent * 100, 1) if sent > 0 else 0
        click_rate = round(unique_clicks / sent * 100, 1) if sent > 0 else 0

        render_kpi_row([
            {"label": "Broadcast Emails Sent", "value": f"{sent:,}"},
            {"label": "Unique Opens", "value": f"{unique_opens:,}"},
            {"label": "Open Rate", "value": f"{open_rate}%"},
            {"label": "Unique Clicks", "value": f"{unique_clicks:,}"},
            {"label": "Click Rate", "value": f"{click_rate}%"},
            {"label": "Bounced", "value": f"{bounced:,}"},
        ])

    # Campaigns by subject
    subjects = _fetch_broadcast_subjects(from_date, to_date)
    if subjects:
        st.subheader("Campaigns by Subject")
        rows = []
        for subj, info in sorted(subjects.items(), key=lambda x: x[1]["count"], reverse=True):
            rows.append({
                "Subject": subj[:80],
                "Recipients": info["count"],
                "First Sent": info["date"],
            })
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

        # Bar chart
        if len(rows) > 1:
            labels = [r["Subject"][:40] for r in rows[:10]]
            values = [r["Recipients"] for r in rows[:10]]
            fig = create_horizontal_bar(labels, values, title="Recipients by Campaign")
            st.plotly_chart(fig, width="stretch")
    else:
        st.info("No broadcast campaigns found in selected date range.")
