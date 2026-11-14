import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import style

# One colour per season, the same on every chart
SEASON_COLOURS = {
    "Winter": style.BLUE,
    "Spring": style.GREEN,
    "Summer": style.AMBER,
    "Autumn": style.CORAL,
}


def show(fig):
    """Draw a chart across the full width. Older Streamlit versions need the second form."""
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def _finish(fig, title, y_title):
    """The look shared by every chart: dark surface, soft grid, light text."""
    fig.update_layout(
        title=dict(text=title, font=dict(color=style.WHITE, size=17)),
        paper_bgcolor=style.SURFACE,
        plot_bgcolor=style.SURFACE,
        font=dict(color="#CBD5E1"),
        margin=dict(l=20, r=20, t=70, b=20),
        yaxis_title=y_title,
        xaxis_title=None,
        height=420,
        hoverlabel=dict(bgcolor=style.BG, font_color=style.WHITE, bordercolor=style.BORDER),
    )
    fig.update_yaxes(gridcolor=style.BORDER, zerolinecolor=style.BORDER)
    fig.update_xaxes(gridcolor=style.BORDER, linecolor=style.BORDER)
    return fig


def _rgba(hex_colour, alpha):
    """Turn '#2DD4BF' into 'rgba(45, 212, 191, 0.18)' for the soft fill under a line."""
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def monthly_chart(monthly):
    """One bar per month: average rentals per day. Busier months glow brighter."""
    fig = px.bar(
        monthly,
        x="month_label",
        y="mean_daily_rentals",
        color="mean_daily_rentals",
        color_continuous_scale=[[0.0, "#155E75"], [0.5, style.BLUE], [1.0, style.TEAL]],
        hover_data={"month_label": False, "mean_daily_rentals": ":,.0f",
                    "total_rentals": ":,.0f", "open_dates": True},
        labels={"mean_daily_rentals": "Rentals per day", "total_rentals": "Total rentals",
                "open_dates": "Open days"},
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_traces(marker_line_width=0)
    return _finish(fig, "Average rentals per day, by month", "Rentals per day")


def season_chart(seasons):
    """One bar per season: average rentals per day."""
    fig = px.bar(
        seasons,
        x="season",
        y="mean_daily_rentals",
        color="season",
        color_discrete_map=SEASON_COLOURS,
        hover_data={"season": False, "mean_daily_rentals": ":,.0f",
                    "total_rentals": ":,.0f", "open_dates": True},
        labels={"mean_daily_rentals": "Rentals per day", "total_rentals": "Total rentals",
                "open_dates": "Open days"},
    )
    fig.update_layout(showlegend=False)
    return _finish(fig, "Average rentals per day, by season", "Rentals per day")


def daily_line(series, month_label, colour=style.TEAL, y_max=None, title=None):
    """Daily rentals across one month. Closed dates leave a gap in the line.

    y_max fixes the top of the vertical axis, so two charts side by side use the same scale.
    """
    fig = px.line(
        x=series.index,
        y=series.values,
        markers=True,
        color_discrete_sequence=[colour],
    )
    fig.update_traces(
        connectgaps=False,
        fill="tozeroy",
        fillcolor=_rgba(colour, 0.18),
        line=dict(width=3),
        hovertemplate="%{x|%d %b %Y}: %{y:,.0f} rentals<extra></extra>",
    )
    fig = _finish(fig, title or f"Rentals per day, {month_label}", "Rentals per day")
    # An explicit format stops Plotly from printing the year under the first tick label
    fig.update_xaxes(tickformat="%d %b")
    if y_max is not None:
        fig.update_yaxes(range=[0, y_max])
    return fig


def long_line(series, average, title):
    """Daily rentals over a long period with a rolling average on top. Gaps mark closed days."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index, y=series.values, mode="lines", name="Daily rentals",
        line=dict(color=_rgba(style.TEAL, 0.55), width=1.5), connectgaps=False,
        hovertemplate="%{x|%d %b %Y}: %{y:,.0f} rentals<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=average.index, y=average.values, mode="lines", name="7-day average",
        line=dict(color=style.WHITE, width=3.5), connectgaps=False,
        hovertemplate="%{x|%d %b %Y}: %{y:,.0f} on average<extra></extra>",
    ))
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig = _finish(fig, title, "Rentals per day")
    fig.update_xaxes(tickformat="%b %Y")
    return fig


def hour_line(profile, title, colour=style.TEAL):
    """Average rentals for each hour of the day."""
    labels = [f"{hour:02d}:00" for hour in profile.index]
    fig = px.line(x=labels, y=profile.values, markers=True, color_discrete_sequence=[colour])
    fig.update_traces(
        fill="tozeroy",
        fillcolor=_rgba(colour, 0.18),
        line=dict(width=3),
        hovertemplate="%{x}: %{y:,.0f} rentals<extra></extra>",
    )
    return _finish(fig, title, "Average rentals per hour")


def predict_curve(values, chosen_hour, title):
    """Predicted rentals for the 24 hours, with the chosen hour marked."""
    labels = [f"{hour:02d}:00" for hour in range(24)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels, y=values, mode="lines+markers",
        line=dict(color=style.TEAL, width=3), marker=dict(size=6),
        hovertemplate="%{x}: %{y:,.0f} predicted<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[labels[chosen_hour]], y=[values[chosen_hour]], mode="markers",
        marker=dict(size=16, color=style.AMBER, line=dict(color=style.WHITE, width=2)),
        hovertemplate="Your hour, %{x}: %{y:,.0f} predicted<extra></extra>",
    ))
    fig.update_layout(showlegend=False)
    return _finish(fig, title, "Predicted demand, rentals per hour")
