import plotly.graph_objects as go

COLORS = {
    "primary": "#1B4D3E",
    "secondary": "#2E8B57",
    "accent": "#48D1CC",
    "warning": "#FF6B6B",
    "info": "#4ECDC4",
    "sent": "#2E8B57",
    "opened": "#48D1CC",
    "clicked": "#4ECDC4",
    "bounced": "#FF6B6B",
    "unsubscribed": "#FFB347",
    "pending": "#A78BFA",
    "subscribed": "#2E8B57",
    "complained": "#FF4444",
}

PALETTE = ["#2E8B57", "#48D1CC", "#4ECDC4", "#FFB347", "#FF6B6B", "#A78BFA", "#F472B6", "#60A5FA"]


def _base_layout(title=None):
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#262730", size=12),
        margin=dict(l=40, r=20, t=50 if title else 20, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        xaxis=dict(gridcolor="rgba(0,0,0,0.08)", zerolinecolor="rgba(0,0,0,0.08)"),
        yaxis=dict(gridcolor="rgba(0,0,0,0.08)", zerolinecolor="rgba(0,0,0,0.08)"),
    )
    if title:
        layout["title"] = dict(text=title, font=dict(size=16, color="#1B4D3E"))
    return layout


def create_time_series(df, x, y_cols, title=None, colors=None):
    fig = go.Figure()
    colors = colors or PALETTE
    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], name=col, mode="lines+markers",
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=5),
        ))
    fig.update_layout(**_base_layout(title))
    return fig


def create_funnel(stages, title=None):
    fig = go.Figure(go.Funnel(
        y=[s["label"] for s in stages],
        x=[s["value"] for s in stages],
        textinfo="value+percent initial",
        marker=dict(color=[COLORS.get(s.get("color_key", ""), PALETTE[i % len(PALETTE)]) for i, s in enumerate(stages)]),
        connector=dict(line=dict(color="rgba(255,255,255,0.1)")),
    ))
    fig.update_layout(**_base_layout(title))
    return fig


def create_donut(labels, values, title=None, colors=None):
    colors = colors or PALETTE
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.5,
        marker=dict(colors=colors[:len(labels)]),
        textinfo="label+percent", textfont=dict(size=11),
    ))
    fig.update_layout(**_base_layout(title), showlegend=True)
    return fig


def create_horizontal_bar(labels, values, title=None, color=None):
    fig = go.Figure(go.Bar(
        y=labels, x=values, orientation="h",
        marker=dict(color=color or COLORS["accent"]),
        text=values, textposition="auto",
    ))
    layout = _base_layout(title)
    layout["yaxis"] = dict(autorange="reversed", gridcolor="rgba(255,255,255,0.08)")
    fig.update_layout(**layout)
    return fig


def create_heatmap(z, x_labels, y_labels, title=None):
    fig = go.Figure(go.Heatmap(
        z=z, x=x_labels, y=y_labels,
        colorscale=[[0, "#F0F2F6"], [0.5, "#1B4D3E"], [1, "#48D1CC"]],
        texttemplate="%{z}", textfont=dict(size=10),
    ))
    fig.update_layout(**_base_layout(title))
    return fig


def create_stacked_area(df, x, y_cols, title=None, colors=None):
    fig = go.Figure()
    colors = colors or PALETTE
    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], name=col, mode="lines",
            stackgroup="one", line=dict(color=colors[i % len(colors)]),
        ))
    fig.update_layout(**_base_layout(title))
    return fig


def create_combo_chart(df, x, bar_col, line_col, title=None, bar_color=None, line_color=None):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df[x], y=df[bar_col], name=bar_col,
        marker=dict(color=bar_color or COLORS["sent"], opacity=0.7),
    ))
    fig.add_trace(go.Scatter(
        x=df[x], y=df[line_col], name=line_col, mode="lines+markers",
        line=dict(color=line_color or COLORS["opened"], width=2),
        yaxis="y2",
    ))
    layout = _base_layout(title)
    layout["yaxis2"] = dict(overlaying="y", side="right", gridcolor="rgba(255,255,255,0.08)")
    layout["barmode"] = "group"
    fig.update_layout(**layout)
    return fig


def create_bar_chart(labels, values, title=None, color=None):
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=color or COLORS["accent"]),
        text=values, textposition="auto",
    ))
    fig.update_layout(**_base_layout(title))
    return fig
