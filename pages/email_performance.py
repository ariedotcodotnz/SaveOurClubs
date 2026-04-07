import streamlit as st
import pandas as pd
from api.data_cache import read_cache
from components.charts import (
    create_time_series, create_donut, create_horizontal_bar,
    create_stacked_area, COLORS,
)


def render():
    st.header("Email Performance")

    tab1, tab2, tab3, tab4 = st.tabs(["Delivery", "Engagement", "Clients & Platforms", "Geographic"])

    # --- Delivery Tab ---
    with tab1:
        sends = read_cache("sends")
        bounces = read_cache("bounces")

        if sends:
            days = sends.get("Days", [])
            df = pd.DataFrame([{"Date": d["Date"][:10], "Sent": d["Sent"]} for d in days])
            if not df.empty:
                fig = create_time_series(df, "Date", ["Sent"], title="Emails Sent Per Day",
                                         colors=[COLORS["sent"]])
                st.plotly_chart(fig, width="stretch")

        if bounces:
            days = bounces.get("Days", [])
            rows = []
            for d in days:
                row = {"Date": d["Date"][:10]}
                for key in ["HardBounce", "SoftBounce", "Transient", "SMTPApiError", "SpamNotification"]:
                    if d.get(key, 0) > 0:
                        row[key] = d[key]
                if len(row) > 1:
                    rows.append(row)
            if rows:
                df_b = pd.DataFrame(rows).fillna(0)
                bounce_cols = [c for c in df_b.columns if c != "Date"]
                if bounce_cols:
                    fig = create_stacked_area(df_b, "Date", bounce_cols, title="Bounces by Type")
                    st.plotly_chart(fig, width="stretch")

    # --- Engagement Tab ---
    with tab2:
        opens = read_cache("opens")
        clicks = read_cache("clicks")

        if opens and clicks:
            opens_days = opens.get("Days", [])
            clicks_days = clicks.get("Days", [])

            opens_map = {d["Date"][:10]: d for d in opens_days}
            clicks_map = {d["Date"][:10]: d for d in clicks_days}
            all_dates = sorted(set(opens_map.keys()) | set(clicks_map.keys()))

            df = pd.DataFrame({
                "Date": all_dates,
                "Unique Opens": [opens_map.get(d, {}).get("Unique", 0) for d in all_dates],
                "Total Opens": [opens_map.get(d, {}).get("Opens", 0) for d in all_dates],
                "Unique Clicks": [clicks_map.get(d, {}).get("Unique", 0) for d in all_dates],
                "Total Clicks": [clicks_map.get(d, {}).get("Clicks", 0) for d in all_dates],
            })

            col1, col2 = st.columns(2)
            with col1:
                fig = create_time_series(df, "Date", ["Unique Opens", "Unique Clicks"],
                                         title="Unique Opens & Clicks",
                                         colors=[COLORS["opened"], COLORS["clicked"]])
                st.plotly_chart(fig, width="stretch")

            with col2:
                fig = create_time_series(df, "Date", ["Total Opens", "Unique Opens"],
                                         title="Total vs Unique Opens",
                                         colors=[COLORS["info"], COLORS["opened"]])
                st.plotly_chart(fig, width="stretch")

            # Click-to-open rate
            sends_data = read_cache("sends")
            if sends_data:
                sends_map = {d["Date"][:10]: d["Sent"] for d in sends_data.get("Days", [])}
                cto_rows = []
                for d in all_dates:
                    uo = opens_map.get(d, {}).get("Unique", 0)
                    uc = clicks_map.get(d, {}).get("Unique", 0)
                    s = sends_map.get(d, 0)
                    cto_rows.append({
                        "Date": d,
                        "Open Rate %": round(uo / s * 100, 1) if s > 0 else 0,
                        "Click-to-Open %": round(uc / uo * 100, 1) if uo > 0 else 0,
                    })
                df_rates = pd.DataFrame(cto_rows)
                fig = create_time_series(df_rates, "Date", ["Open Rate %", "Click-to-Open %"],
                                         title="Engagement Rates",
                                         colors=[COLORS["opened"], COLORS["clicked"]])
                st.plotly_chart(fig, width="stretch")

    # --- Clients & Platforms Tab ---
    with tab3:
        open_events = read_cache("open_events") or []
        if open_events:
            platforms = {}
            clients = {}
            for e in open_events:
                p = e.get("Platform", "Unknown") or "Unknown"
                platforms[p] = platforms.get(p, 0) + 1

                client_info = e.get("Client", {})
                c = client_info.get("Family", "Unknown") if client_info else "Unknown"
                clients[c] = clients.get(c, 0) + 1

            col1, col2 = st.columns(2)
            with col1:
                if platforms:
                    fig = create_donut(list(platforms.keys()), list(platforms.values()),
                                       title="Platform Breakdown")
                    st.plotly_chart(fig, width="stretch")

            with col2:
                if clients:
                    sorted_clients = sorted(clients.items(), key=lambda x: x[1], reverse=True)[:10]
                    labels = [c[0] for c in sorted_clients]
                    values = [c[1] for c in sorted_clients]
                    fig = create_horizontal_bar(labels, values, title="Top Email Clients")
                    st.plotly_chart(fig, width="stretch")

            os_data = {}
            for e in open_events:
                os_info = e.get("OS", {})
                os_name = os_info.get("Family", "Unknown") if os_info else "Unknown"
                os_data[os_name] = os_data.get(os_name, 0) + 1
            if os_data:
                sorted_os = sorted(os_data.items(), key=lambda x: x[1], reverse=True)[:10]
                fig = create_horizontal_bar(
                    [o[0] for o in sorted_os],
                    [o[1] for o in sorted_os],
                    title="Operating Systems",
                    color=COLORS["info"]
                )
                st.plotly_chart(fig, width="stretch")
        else:
            st.info("No open event data available for client/platform analysis.")

    # --- Geographic Tab ---
    with tab4:
        open_events = read_cache("open_events") or []
        click_events = read_cache("click_events") or []

        all_events = open_events + click_events
        if all_events:
            regions = {}
            cities = {}
            countries = {}
            for e in all_events:
                geo = e.get("Geo", {})
                if not geo:
                    continue
                region = geo.get("Region", "")
                city = geo.get("City", "")
                country = geo.get("Country", "")
                if region:
                    regions[region] = regions.get(region, 0) + 1
                if city:
                    cities[city] = cities.get(city, 0) + 1
                if country:
                    countries[country] = countries.get(country, 0) + 1

            col1, col2 = st.columns(2)

            with col1:
                if regions:
                    sorted_regions = sorted(regions.items(), key=lambda x: x[1], reverse=True)[:15]
                    fig = create_horizontal_bar(
                        [r[0] for r in sorted_regions],
                        [r[1] for r in sorted_regions],
                        title="Engagement by Region",
                    )
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("No geographic data available.")

            with col2:
                if cities:
                    sorted_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)[:15]
                    st.subheader("Top Cities")
                    st.dataframe(
                        pd.DataFrame(sorted_cities, columns=["City", "Events"]),
                        width="stretch", hide_index=True,
                    )

            if countries:
                sorted_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)
                fig = create_donut(
                    [c[0] for c in sorted_countries],
                    [c[1] for c in sorted_countries],
                    title="Engagement by Country",
                )
                st.plotly_chart(fig, width="stretch")
        else:
            st.info("No geographic data available. Events may not contain geo information.")
