import streamlit as st
import pandas as pd
from api.data_cache import read_cache
from components.charts import (
    create_time_series, create_heatmap, create_stacked_area,
    COLORS,
)


def render():
    st.header("Engagement Trends")

    sends = read_cache("sends")
    opens = read_cache("opens")
    clicks = read_cache("clicks")
    bounces = read_cache("bounces")

    if not sends or not opens or not clicks:
        st.error("No cached data available. Run prefetch.py first.")
        return

    sends_days = sends.get("Days", [])
    opens_days = opens.get("Days", [])
    clicks_days = clicks.get("Days", [])
    bounces_days = bounces.get("Days", []) if bounces else []

    # Build merged dataframe
    sends_map = {d["Date"][:10]: d["Sent"] for d in sends_days}
    opens_map = {d["Date"][:10]: d for d in opens_days}
    clicks_map = {d["Date"][:10]: d for d in clicks_days}
    bounces_map = {}
    for d in bounces_days:
        total_bounced = sum(v for k, v in d.items() if k != "Date" and isinstance(v, int))
        bounces_map[d["Date"][:10]] = total_bounced

    all_dates = sorted(set(sends_map.keys()) | set(opens_map.keys()) | set(clicks_map.keys()))

    df = pd.DataFrame({
        "Date": all_dates,
        "Sent": [sends_map.get(d, 0) for d in all_dates],
        "Unique Opens": [opens_map.get(d, {}).get("Unique", 0) for d in all_dates],
        "Unique Clicks": [clicks_map.get(d, {}).get("Unique", 0) for d in all_dates],
        "Bounced": [bounces_map.get(d, 0) for d in all_dates],
    })

    # Section 1: Core metrics multi-line chart
    fig = create_time_series(
        df, "Date", ["Sent", "Unique Opens", "Unique Clicks"],
        title="Daily Activity Overview",
        colors=[COLORS["sent"], COLORS["opened"], COLORS["clicked"]],
    )
    st.plotly_chart(fig, width="stretch")

    # Section 2: Rate trends + Cumulative totals
    col1, col2 = st.columns(2)

    with col1:
        rate_rows = []
        for _, row in df.iterrows():
            s = row["Sent"]
            uo = row["Unique Opens"]
            uc = row["Unique Clicks"]
            rate_rows.append({
                "Date": row["Date"],
                "Open Rate %": round(uo / s * 100, 1) if s > 0 else 0,
                "Click-to-Open %": round(uc / uo * 100, 1) if uo > 0 else 0,
                "Bounce Rate %": round(row["Bounced"] / s * 100, 1) if s > 0 else 0,
            })
        df_rates = pd.DataFrame(rate_rows)
        fig = create_time_series(
            df_rates, "Date", ["Open Rate %", "Click-to-Open %", "Bounce Rate %"],
            title="Engagement Rates Over Time",
            colors=[COLORS["opened"], COLORS["clicked"], COLORS["bounced"]],
        )
        st.plotly_chart(fig, width="stretch")

    with col2:
        df_cum = df.copy()
        df_cum["Cumulative Sent"] = df_cum["Sent"].cumsum()
        df_cum["Cumulative Opens"] = df_cum["Unique Opens"].cumsum()
        df_cum["Cumulative Clicks"] = df_cum["Unique Clicks"].cumsum()
        fig = create_stacked_area(
            df_cum, "Date", ["Cumulative Sent", "Cumulative Opens", "Cumulative Clicks"],
            title="Cumulative Totals",
            colors=[COLORS["sent"], COLORS["opened"], COLORS["clicked"]],
        )
        st.plotly_chart(fig, width="stretch")

    # Section 3: Opens-by-hour heatmap
    st.subheader("Engagement by Hour of Day")
    open_events = read_cache("open_events") or []
    if open_events:
        hour_day_counts = {}
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for e in open_events:
            ts = e.get("ReceivedAt", "")
            if not ts:
                continue
            try:
                dt = pd.Timestamp(ts)
                dt_nz = dt + pd.Timedelta(hours=13)
                hour = dt_nz.hour
                day_of_week = dt_nz.dayofweek
                key = (day_of_week, hour)
                hour_day_counts[key] = hour_day_counts.get(key, 0) + 1
            except (ValueError, TypeError):
                continue

        if hour_day_counts:
            hours = list(range(24))
            z = []
            for day_idx in range(7):
                row = [hour_day_counts.get((day_idx, h), 0) for h in hours]
                z.append(row)

            hour_labels = [f"{h:02d}:00" for h in hours]
            fig = create_heatmap(z, hour_labels, day_names, title="Opens by Day & Hour (NZST)")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Insufficient timestamp data for heatmap.")
    else:
        st.info("No open event data available for heatmap analysis.")
