#!/usr/bin/env python3
"""Pre-fetch all API data into local cache files.

Run this on a schedule (e.g. every 2 hours via cron or PythonAnywhere scheduled task):
    python prefetch.py
"""
from dotenv import load_dotenv
load_dotenv()

from datetime import date
from api.postmark import PostmarkClient
from api.fluentcrm import FluentCRMClient
from api.data_cache import write_cache, set_cache_timestamp


def prefetch():
    from_date = "2026-03-24"
    to_date = date.today().strftime("%Y-%m-%d")

    pm = PostmarkClient()

    # Postmark aggregate stats
    write_cache("overview", pm.get_overview_stats(from_date, to_date))
    write_cache("sends", pm.get_sends_by_day(from_date, to_date))
    write_cache("opens", pm.get_opens_by_day(from_date, to_date))
    write_cache("clicks", pm.get_clicks_by_day(from_date, to_date))
    write_cache("bounces", pm.get_bounces_by_day(from_date, to_date))
    write_cache("overview_broadcast", pm.get_overview_stats(from_date, to_date, message_stream="broadcast"))
    write_cache("overview_outbound", pm.get_overview_stats(from_date, to_date, message_stream="outbound"))

    # Open events (paginated)
    all_opens = []
    for page in range(4):
        data = pm.get_open_events(count=500, offset=page * 500)
        if not data or not data.get("Opens"):
            break
        all_opens.extend(data["Opens"])
        if len(data["Opens"]) < 500:
            break
    write_cache("open_events", all_opens)

    # Click events (paginated)
    all_clicks = []
    for page in range(4):
        data = pm.get_click_events(count=500, offset=page * 500)
        if not data or not data.get("Clicks"):
            break
        all_clicks.extend(data["Clicks"])
        if len(data["Clicks"]) < 500:
            break
    write_cache("click_events", all_clicks)

    # FluentCRM data
    crm = FluentCRMClient()
    crm_available = crm.is_available()
    write_cache("crm_available", crm_available)

    if crm_available:
        sub_counts = {}
        for status in ["subscribed", "unsubscribed", "pending", "bounced", "complained"]:
            data = crm.get_subscribers(per_page=1, statuses=[status])
            sub_counts[status] = data.get("total", 0) if data and "total" in data else 0
        write_cache("subscriber_counts", sub_counts)
        write_cache("tags", crm.get_tags())
        write_cache("lists", crm.get_lists())

    set_cache_timestamp()
    print(f"Cache updated: {date.today()}")


if __name__ == "__main__":
    prefetch()
