import streamlit as st

import style
import data
import charts
import analysis  # works because data.py adds the src folder to the path

style.setup("Compare")
style.banner("Compare", "Set any two months side by side")


@st.cache_data
def get_data():
    return data.load_all()


def summarise(df, label):
    """The figures of one month. Every number comes from your analysis functions."""
    view = data.pick(df, months=[label])
    daily = analysis.daily_table(view)
    figures = analysis.headline_figures(daily)
    profile = analysis.hour_profile(view)
    weather = analysis.daily_weather(view)
    return {
        "daily": daily,
        "total": figures["total_rentals"],
        "per_day": figures["mean_per_day"],
        "busiest_day": figures["busiest_rentals"],
        "busiest_date": figures["busiest_date"],
        "hour_value": float(profile.max()),
        "hour": int(profile.idxmax()),
        "temperature": float(weather["temperature"].mean()),
        "rain": float(weather["rainfall"].mean()),
    }


def widths(a, b):
    """Bar widths in percent. The larger value fills the half column.

    The scale starts at zero, or at the lowest value when one value is below zero (temperature).
    A floor of 25 percent keeps the text inside the bar.
    """
    base = min(0, a, b)
    top = max(a, b) - base
    if top == 0:
        return 100, 100
    return max(25, (a - base) / top * 100), max(25, (b - base) / top * 100)


def row(metric, value_a, value_b, fmt, extra_a="", extra_b=""):
    width_a, width_b = widths(value_a, value_b)
    return (metric, fmt(value_a) + extra_a, fmt(value_b) + extra_b, width_a, width_b)


df = get_data()
labels = data.month_labels(df)

# Explore may have sent two months. Use them once, then clear them.
picked = st.session_state.pop("compare_pick", None)
default_a, default_b = picked if picked else ("Jun 2018", "Aug 2018")

# ---------- Name tags and dropdowns ----------
header_box = st.container()  # filled after the dropdowns, so the tags show the current choice
col_a, col_mid, col_b = st.columns([5, 1, 5])
with col_a:
    month_a = st.selectbox("Month A", labels, index=labels.index(default_a), key="compare_a")
with col_b:
    month_b = st.selectbox("Month B", labels, index=labels.index(default_b), key="compare_b")
with header_box:
    style.versus_header(month_a, month_b)

if month_a == month_b:
    style.notice("Choose two different months. Month A and Month B are the same.")
    st.stop()

a = summarise(df, month_a)
b = summarise(df, month_b)

# ---------- One sentence ----------
gap = (a["per_day"] - b["per_day"]) / b["per_day"] * 100
direction = "above" if gap >= 0 else "below"
st.markdown(
    f"**{month_a}** averaged **{a['per_day']:,.0f}** rentals per day. "
    f"This is **{abs(gap):.1f}% {direction}** {month_b}, which averaged {b['per_day']:,.0f}."
)

# ---------- Butterfly bars ----------
style.versus_rows([
    row("Total rentals", a["total"], b["total"], lambda v: f"{v:,.0f}"),
    row("Average rentals per day", a["per_day"], b["per_day"], lambda v: f"{v:,.0f}"),
    row("Busiest day, rentals", a["busiest_day"], b["busiest_day"], lambda v: f"{v:,.0f}",
        f" ({a['busiest_date']:%d %b})", f" ({b['busiest_date']:%d %b})"),
    row("Busiest hour, average rentals", a["hour_value"], b["hour_value"], lambda v: f"{v:,.0f}",
        f" at {a['hour']:02d}:00", f" at {b['hour']:02d}:00"),
    row("Average temperature", a["temperature"], b["temperature"], lambda v: f"{v:.1f} °C"),
    row("Rainfall per day", a["rain"], b["rain"], lambda v: f"{v:.2f} mm"),
])

# ---------- Line charts, same vertical scale ----------
st.write("")
series_a = data.month_series(a["daily"])
series_b = data.month_series(b["daily"])
y_max = float(max(series_a.max(), series_b.max())) * 1.08

left, right = st.columns(2)
with left:
    charts.show(charts.daily_line(series_a, month_a, colour=style.COLOUR_A, y_max=y_max))
with right:
    charts.show(charts.daily_line(series_b, month_b, colour=style.COLOUR_B, y_max=y_max))

st.caption("Both charts share one vertical scale, so a quiet month looks quiet. "
           "A gap in a line marks a closed day and is never a zero.")