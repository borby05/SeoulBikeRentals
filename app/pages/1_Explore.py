import streamlit as st

import style
import data
import charts
import analysis  # works because data.py adds the src folder to the path

style.setup("Explore")
style.banner("Explore", "Filter demand by year, month, day type and hour")

DAY_TYPES = ["Weekday", "Weekend", "Holiday"]


@st.cache_data
def get_data():
    # add_day_type labels every row as Weekday, Weekend or Holiday
    return analysis.add_day_type(data.load_all())


def keep_first_month(first):
    """Runs when the user clicks 'Keep one month'. A click callback is allowed to reset a widget."""
    st.session_state["explore_months"] = [first]
    st.session_state["show_keep_message"] = True


df = get_data()

# ---------- Filters ----------
year_choice = st.selectbox("Year", ["All years", 2017, 2018])
year = None if year_choice == "All years" else year_choice
if year == 2017:
    style.notice("2017 contains December only. Select 2018 to view monthly and seasonal patterns.")

labels = data.month_labels(data.pick(df, year=year))

# A chosen month can vanish when the year changes. Remove it before the widget is drawn.
if "explore_months" in st.session_state:
    st.session_state["explore_months"] = [m for m in st.session_state["explore_months"] if m in labels]

col_month, col_type, col_hour = st.columns([4, 4, 3])
with col_month:
    chosen = st.multiselect("Months (leave empty for all)", labels, key="explore_months")
with col_type:
    day_types = st.multiselect("Day type", DAY_TYPES, default=DAY_TYPES)
with col_hour:
    hour_from, hour_to = st.slider("Hours of the day", 0, 23, (0, 23))

months = [m for m in labels if m in chosen]  # calendar order, whatever order the user clicked

if st.session_state.pop("show_keep_message", False):
    style.notice("To view several months together, use the Compare page.")

# ---------- Two or more months ----------
if len(months) == 2:
    st.write("You selected two months. Compare them, or keep one.")
    left, right = st.columns(2)
    with left:
        if st.button(f"Compare {months[0]} and {months[1]}", type="primary"):
            st.session_state["compare_pick"] = (months[0], months[1])
            st.switch_page("pages/2_Compare.py")
    with right:
        st.button("Keep one month", on_click=keep_first_month, args=(months[0],))
    st.stop()

if len(months) > 2:
    style.notice("The comparison page handles two months. Select two to continue.")
    st.stop()

# ---------- Filtered data ----------
view = data.pick(df, year=year, months=months or None)
view = view[view["day_type"].isin(day_types) & view["hour"].between(hour_from, hour_to)]

if view.empty:
    style.notice("No data matches this selection. Change a filter to continue.")
    st.stop()

hours_note = "" if (hour_from, hour_to) == (0, 23) else f", hours {hour_from:02d} to {hour_to:02d}"
period = months[0] if months else (year_choice if year else "December 2017 to November 2018")

daily = analysis.daily_table(view)
figures = analysis.headline_figures(daily)

# ---------- Cards ----------
cards = st.columns(4)
with cards[0]:
    style.number_card("Total rentals", f"{figures['total_rentals']:,}",
                      f"{figures['open_dates']} days in this selection", colour=style.TEAL)
with cards[1]:
    style.number_card("Average per day", f"{figures['mean_per_day']:,.0f}",
                      "rentals per day", colour=style.BLUE)
with cards[2]:
    style.number_card("Busiest day", figures["busiest_date"].strftime("%d %b %Y"),
                      f"{figures['busiest_rentals']:,} rentals", colour=style.AMBER)
with cards[3]:
    style.number_card("Quietest day", figures["quietest_date"].strftime("%d %b %Y"),
                      f"{figures['quietest_rentals']:,} rentals", colour=style.CORAL)

# ---------- Charts ----------
profile = analysis.hour_profile(view)

if not months:
    tab_line, tab_month, tab_hour = st.tabs(["Daily line", "By month", "By hour"])
    with tab_line:
        full, average = data.long_series(daily)
        charts.show(charts.long_line(full, average, f"Rentals per day, {period}{hours_note}"))
    with tab_month:
        charts.show(charts.monthly_chart(data.monthly_table(view)))
    with tab_hour:
        charts.show(charts.hour_line(profile, f"Average rentals per hour, {period}"))
else:
    tab_day, tab_hour = st.tabs(["Rentals per day", "Rentals per hour"])
    with tab_day:
        charts.show(charts.daily_line(data.month_series(daily), period,
                                      title=f"Rentals per day, {period}{hours_note}"))
    with tab_hour:
        charts.show(charts.hour_line(profile, f"Average rentals per hour, {period}"))

st.caption("A gap in a line marks a closed day or a day removed by your day type filter. "
           "A gap is never a zero.")
