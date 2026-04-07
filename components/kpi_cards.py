import streamlit as st


def render_kpi_card(label, value, delta=None, delta_color="normal"):
    with st.container(border=True):
        st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def render_kpi_row(metrics):
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            render_kpi_card(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
                delta_color=m.get("delta_color", "normal"),
            )
