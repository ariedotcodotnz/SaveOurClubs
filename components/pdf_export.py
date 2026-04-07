import io
from datetime import datetime
from fpdf import FPDF


class CampaignReport(FPDF):
    def __init__(self, from_date, to_date, stream=None):
        super().__init__()
        self.from_date = from_date
        self.to_date = to_date
        self.stream_label = stream if stream else "All Streams"

    def header(self):
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(27, 77, 62)  # #1B4D3E
        self.cell(0, 12, "Save Our Clubs", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 13)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, "Campaign Performance Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(
            0, 6,
            f"{self.from_date}  to  {self.to_date}   |   Stream: {self.stream_label}",
            align="C", new_x="LMARGIN", new_y="NEXT",
        )
        self.ln(2)
        # Divider line
        self.set_draw_color(27, 77, 62)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(
            0, 10,
            f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  saveourclubs.nz",
            align="C",
        )

    def section_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(27, 77, 62)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def add_kpi_grid(self, kpis, cols=3):
        col_width = (self.w - 20) / cols
        row_height = 22
        start_y = self.get_y()

        for i, (label, value) in enumerate(kpis):
            col = i % cols
            row = i // cols
            x = 10 + col * col_width
            y = start_y + row * row_height

            # KPI box background
            self.set_fill_color(245, 248, 246)
            self.rect(x + 1, y, col_width - 2, row_height - 2, "F")

            # Label
            self.set_xy(x, y + 2)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(100, 100, 100)
            self.cell(col_width, 5, label, align="C")

            # Value
            self.set_xy(x, y + 7)
            self.set_font("Helvetica", "B", 15)
            self.set_text_color(27, 77, 62)
            self.cell(col_width, 10, value, align="C")

        total_rows = (len(kpis) + cols - 1) // cols
        self.set_y(start_y + total_rows * row_height + 4)

    def add_chart_image(self, fig, width=None, height=400, title=None):
        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="#333333", size=12),
            title=dict(font=dict(color="#1B4D3E")) if fig.layout.title else {},
            xaxis=dict(gridcolor="rgba(0,0,0,0.08)", zerolinecolor="rgba(0,0,0,0.1)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0.08)", zerolinecolor="rgba(0,0,0,0.1)"),
        )
        if hasattr(fig.layout, "yaxis2") and fig.layout.yaxis2:
            fig.update_layout(
                yaxis2=dict(gridcolor="rgba(0,0,0,0.08)", zerolinecolor="rgba(0,0,0,0.1)"),
            )

        img_bytes = fig.to_image(format="png", width=800, height=height, scale=2)
        img_stream = io.BytesIO(img_bytes)

        img_width = width or (self.w - 20)
        space_needed = img_width * (height / 800) + 20
        if self.get_y() + space_needed > self.h - 20:
            self.add_page()

        if title:
            self.section_title(title)
        self.image(img_stream, x=10, w=img_width)
        self.ln(8)


def generate_media_report(from_date, to_date, stream=None, crm_available=False):
    from api.data_cache import read_cache
    from components.charts import create_combo_chart, create_funnel, create_donut, COLORS
    import pandas as pd

    overview = read_cache("overview")
    if not overview:
        return None

    sent = overview.get("Sent", 0)
    bounced = overview.get("Bounced", 0)
    unique_opens = overview.get("UniqueOpens", 0)
    unique_clicks = overview.get("UniqueLinksClicked", 0)
    spam = overview.get("SpamComplaints", 0)
    open_rate = (unique_opens / sent * 100) if sent > 0 else 0
    click_rate = (unique_clicks / sent * 100) if sent > 0 else 0
    bounce_rate = (bounced / sent * 100) if sent > 0 else 0

    pdf = CampaignReport(from_date, to_date, stream)
    pdf.add_page()

    # -- Email KPIs --
    pdf.section_title("Email Performance")
    pdf.add_kpi_grid([
        ("Emails Sent", f"{sent:,}"),
        ("Unique Opens", f"{unique_opens:,}"),
        ("Open Rate", f"{open_rate:.1f}%"),
        ("Unique Clicks", f"{unique_clicks:,}"),
        ("Click Rate", f"{click_rate:.1f}%"),
        ("Bounce Rate", f"{bounce_rate:.1f}%"),
    ])

    # -- Subscriber KPIs (if CRM available) --
    if crm_available:
        sub_data = read_cache("subscriber_counts")
        if sub_data:
            total_subs = sum(sub_data.values())
            pdf.section_title("Subscriber Summary")
            pdf.add_kpi_grid([
                ("Total Contacts", f"{total_subs:,}"),
                ("Subscribed", f"{sub_data.get('subscribed', 0):,}"),
                ("Unsubscribed", f"{sub_data.get('unsubscribed', 0):,}"),
                ("Pending", f"{sub_data.get('pending', 0):,}"),
            ], cols=4)

    # -- Daily Sends & Opens chart --
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
        pdf.add_chart_image(fig, title="Daily Sends & Opens")

    # -- Engagement Funnel --
    stages = [
        {"label": "Sent", "value": sent, "color_key": "sent"},
        {"label": "Opened", "value": unique_opens, "color_key": "opened"},
        {"label": "Clicked", "value": unique_clicks, "color_key": "clicked"},
    ]
    fig = create_funnel(stages, title="Engagement Funnel")
    pdf.add_chart_image(fig, width=pdf.w - 60, height=350, title="Engagement Funnel")

    # -- Bounce Breakdown --
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
            pdf.add_chart_image(fig, width=pdf.w - 60, height=350, title="Bounce Breakdown")

    if spam > 0:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 8, f"Spam Complaints: {spam}", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
